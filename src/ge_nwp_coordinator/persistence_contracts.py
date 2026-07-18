"""Pure B3a persistence contracts for future SQLite transition apply.

B3a defines canonical row mappings and safe future error boundaries only. This
module must not open SQLite, allocate sequences from a database, or mutate state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, BACKLOG_SCHEMA_VERSION, FiniteBacklog, WorkItem
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256, require_exact_keys, require_string
from ge_nwp_coordinator.global_stop import GLOBAL_STOP_SCHEMA_ID, GlobalStopState
from ge_nwp_coordinator.lease import (
    AUTHORIZATION_DECISION_SCHEMA_ID,
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    AuthorizationModel,
    LeaseIdentityValidation,
    StandingLease,
    require_digest,
    require_utc_timestamp,
)
from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.state_machine import (
    DEPENDENCY_DECISION_SCHEMA_ID,
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    WorkItemRecord,
    WorkItemState,
    require_work_item_state,
)

SQLITE_SIGNED_INT_MAX = 9223372036854775807
FIRST_TRANSITION_EVENT_SEQUENCE = 0
_SAFE_SQL_IDENTIFIER_FIRST_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz")
_SAFE_SQL_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")


def _validated_row_columns(name: str, columns: tuple[str, ...]) -> tuple[str, ...]:
    if not columns:
        raise ValueError(f"invalid_row_columns:{name}")
    seen: set[str] = set()
    for column in columns:
        if type(column) is not str or not column:
            raise ValueError(f"invalid_row_column:{name}")
        if column[0] not in _SAFE_SQL_IDENTIFIER_FIRST_CHARS:
            raise ValueError(f"invalid_row_column:{name}")
        if any(character not in _SAFE_SQL_IDENTIFIER_CHARS for character in column):
            raise ValueError(f"invalid_row_column:{name}")
        if column in seen:
            raise ValueError(f"duplicate_row_column:{name}")
        seen.add(column)
    return columns


def _row_keys_without(columns: tuple[str, ...], operational_timestamp_column: str) -> frozenset[str]:
    if operational_timestamp_column not in columns:
        raise ValueError("missing_operational_timestamp_column")
    return frozenset(column for column in columns if column != operational_timestamp_column)

LEASE_IDENTITY_RECORD_ROW_COLUMNS = _validated_row_columns(
    "LEASE_IDENTITY_RECORD_ROW_COLUMNS",
    (
        "decision_ref",
        "lease_ref",
        "identity_valid",
        "lease_digest",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    ),
)
LEASE_IDENTITY_RECORD_ROW_KEYS = frozenset(LEASE_IDENTITY_RECORD_ROW_COLUMNS)
LEASE_IDENTITY_RECORD_KEYS = _row_keys_without(LEASE_IDENTITY_RECORD_ROW_COLUMNS, "created_at")
AUTHORIZATION_RECEIPT_ROW_COLUMNS = _validated_row_columns(
    "AUTHORIZATION_RECEIPT_ROW_COLUMNS",
    (
        "decision_ref",
        "lease_ref",
        "lease_identity_decision_ref",
        "lease_identity_valid",
        "authorization_model",
        "authorized",
        "executable",
        "reason",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    ),
)
AUTHORIZATION_RECEIPT_ROW_KEYS = frozenset(AUTHORIZATION_RECEIPT_ROW_COLUMNS)
AUTHORIZATION_RECEIPT_KEYS = _row_keys_without(AUTHORIZATION_RECEIPT_ROW_COLUMNS, "created_at")
DEPENDENCY_RECEIPT_ROW_COLUMNS = _validated_row_columns(
    "DEPENDENCY_RECEIPT_ROW_COLUMNS",
    (
        "decision_ref",
        "work_item_id",
        "dependencies_satisfied",
        "reason",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    ),
)
DEPENDENCY_RECEIPT_ROW_KEYS = frozenset(DEPENDENCY_RECEIPT_ROW_COLUMNS)
DEPENDENCY_RECEIPT_KEYS = _row_keys_without(DEPENDENCY_RECEIPT_ROW_COLUMNS, "created_at")
WORK_ITEM_ROW_COLUMNS = _validated_row_columns(
    "WORK_ITEM_ROW_COLUMNS",
    (
        "work_item_id",
        "lease_id",
        "backlog_id",
        "schema_id",
        "state",
        "version",
        "attempt_count",
        "repair_count",
        "budget_consumed",
        "budget_limit",
        "max_attempts",
        "max_repairs",
        "cleanup_required",
        "updated_at",
    ),
)
WORK_ITEM_ROW_KEYS = frozenset(WORK_ITEM_ROW_COLUMNS)
ADMITTED_BACKLOG_ROW_COLUMNS = _validated_row_columns(
    "ADMITTED_BACKLOG_ROW_COLUMNS",
    (
        "backlog_id",
        "lease_ref",
        "schema_id",
        "schema_version",
        "content_digest",
        "canonical_json",
        "admitted_at",
    ),
)
ADMITTED_BACKLOG_ROW_KEYS = frozenset(ADMITTED_BACKLOG_ROW_COLUMNS)
GLOBAL_STOP_CURRENT_ROW_COLUMNS = _validated_row_columns(
    "GLOBAL_STOP_CURRENT_ROW_COLUMNS",
    (
        "singleton_id",
        "schema_id",
        "version",
        "active",
        "stop_id",
        "reason_class",
        "issuer_ref",
        "issued_at",
        "operator_decision_ref",
        "updated_at",
    ),
)
GLOBAL_STOP_CURRENT_ROW_KEYS = frozenset(GLOBAL_STOP_CURRENT_ROW_COLUMNS)
_MAX_CANONICAL_JSON_BYTES = 1048576


class B3AuthorizationModelHandling(str, Enum):
    FAIL_CLOSED_UNSUPPORTED = "fail_closed_unsupported"
    UNSUPPORTED_AUTHORITATIVE_MODEL = "unsupported_authoritative_model"


@dataclass(frozen=True)
class LeaseIdentityRecordReconstruction:
    lease: StandingLease = field(repr=False)
    validation: LeaseIdentityValidation = field(repr=False)


@dataclass(frozen=True)
class LeaseIdentityRecordEnvelope:
    reconstruction: LeaseIdentityRecordReconstruction = field(repr=False)
    created_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.reconstruction, LeaseIdentityRecordReconstruction):
            raise _integrity_failure()
        object.__setattr__(
            self,
            "created_at",
            _require_canonical_utc_timestamp(self.created_at, "lease_identity_record_row.created_at"),
        )


@dataclass(frozen=True)
class AuthorizationReceiptEnvelope:
    decision: AuthorizationDecision = field(repr=False)
    created_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, AuthorizationDecision):
            raise _integrity_failure()
        object.__setattr__(
            self,
            "created_at",
            _require_canonical_utc_timestamp(self.created_at, "authorization_receipt_row.created_at"),
        )


@dataclass(frozen=True)
class DependencyReceiptEnvelope:
    decision: DependencyDecision = field(repr=False)
    created_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, DependencyDecision):
            raise _integrity_failure()
        object.__setattr__(
            self,
            "created_at",
            _require_canonical_utc_timestamp(self.created_at, "dependency_receipt_row.created_at"),
        )


@dataclass(frozen=True)
class WorkItemRecordEnvelope:
    record: WorkItemRecord = field(repr=False)
    updated_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.record, WorkItemRecord):
            raise _integrity_failure()
        object.__setattr__(
            self,
            "updated_at",
            _require_canonical_utc_timestamp(self.updated_at, "work_item_row.updated_at"),
        )


@dataclass(frozen=True)
class AdmittedBacklogRecordEnvelope:
    backlog: FiniteBacklog = field(repr=False)
    admitted_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.backlog, FiniteBacklog):
            raise _integrity_failure()
        object.__setattr__(
            self,
            "admitted_at",
            _require_canonical_utc_timestamp(self.admitted_at, "admitted_backlog_row.admitted_at"),
        )


@dataclass(frozen=True)
class GlobalStopCurrentRecordEnvelope:
    state: GlobalStopState = field(repr=False)
    updated_at: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, GlobalStopState):
            raise _integrity_failure()
        object.__setattr__(
            self,
            "updated_at",
            _require_canonical_utc_timestamp(self.updated_at, "global_stop_current_row.updated_at"),
        )


@dataclass(frozen=True)
class LeaseIdentityRecordContract:
    decision_ref: str
    lease_ref: str
    identity_valid: bool
    lease_digest: str | None = field(repr=False)
    schema_id: str
    canonical_json: str = field(repr=False)
    canonical_digest: str = field(repr=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LeaseIdentityRecordContract":
        try:
            raw = require_exact_keys(payload, "lease_identity_record", LEASE_IDENTITY_RECORD_KEYS)
            lease_digest = raw.get("lease_digest")
            if lease_digest is not None:
                lease_digest = require_digest(lease_digest, "lease_identity_record.lease_digest")
            schema_id = require_string(raw.get("schema_id"), "lease_identity_record.schema_id")
            if schema_id != LEASE_SCHEMA_ID:
                raise _integrity_failure()
            return cls(
                decision_ref=require_contract_ref(raw.get("decision_ref"), "lease_identity_record.decision_ref"),
                lease_ref=require_contract_ref(raw.get("lease_ref"), "lease_identity_record.lease_ref"),
                identity_valid=require_sqlite_boolean(raw.get("identity_valid"), "lease_identity_record.identity_valid"),
                lease_digest=lease_digest,
                schema_id=schema_id,
                canonical_json=require_string(raw.get("canonical_json"), "lease_identity_record.canonical_json"),
                canonical_digest=require_digest(raw.get("canonical_digest"), "lease_identity_record.canonical_digest"),
            )
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc

    def reconstruct(self) -> LeaseIdentityRecordReconstruction:
        try:
            lease = StandingLease.from_json(self.canonical_json)
            validation = lease.validate_identity()
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc
        _require_exact_canonical_json(self.canonical_json, lease.to_dict())
        _require_equal(self.canonical_digest, canonical_sha256(lease.to_dict()))
        _require_equal(self.decision_ref, validation.decision_ref)
        _require_equal(self.lease_ref, validation.lease_ref)
        _require_equal(self.identity_valid, validation.identity_valid)
        _require_equal(self.lease_digest, validation.digest)
        _require_equal(self.schema_id, lease.schema_id)
        return LeaseIdentityRecordReconstruction(lease=lease, validation=validation)


@dataclass(frozen=True)
class AuthorizationReceiptContract:
    decision_ref: str
    lease_ref: str
    lease_identity_decision_ref: str
    lease_identity_valid: bool
    authorization_model: str
    authorized: bool
    executable: bool
    reason: str
    schema_id: str
    canonical_json: str = field(repr=False)
    canonical_digest: str = field(repr=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AuthorizationReceiptContract":
        try:
            raw = require_exact_keys(payload, "authorization_receipt", AUTHORIZATION_RECEIPT_KEYS)
            schema_id = require_string(raw.get("schema_id"), "authorization_receipt.schema_id")
            if schema_id != AUTHORIZATION_DECISION_SCHEMA_ID:
                raise _integrity_failure()
            return cls(
                decision_ref=require_contract_ref(raw.get("decision_ref"), "authorization_receipt.decision_ref"),
                lease_ref=require_contract_ref(raw.get("lease_ref"), "authorization_receipt.lease_ref"),
                lease_identity_decision_ref=require_contract_ref(
                    raw.get("lease_identity_decision_ref"),
                    "authorization_receipt.lease_identity_decision_ref",
                ),
                lease_identity_valid=require_sqlite_boolean(
                    raw.get("lease_identity_valid"),
                    "authorization_receipt.lease_identity_valid",
                ),
                authorization_model=require_string(raw.get("authorization_model"), "authorization_receipt.authorization_model"),
                authorized=require_sqlite_boolean(raw.get("authorized"), "authorization_receipt.authorized"),
                executable=require_sqlite_boolean(raw.get("executable"), "authorization_receipt.executable"),
                reason=require_string(raw.get("reason"), "authorization_receipt.reason"),
                schema_id=schema_id,
                canonical_json=require_string(raw.get("canonical_json"), "authorization_receipt.canonical_json"),
                canonical_digest=require_digest(raw.get("canonical_digest"), "authorization_receipt.canonical_digest"),
            )
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc

    def reconstruct(self) -> AuthorizationDecision:
        try:
            decision = AuthorizationDecision.from_json(self.canonical_json)
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc
        _require_exact_canonical_json(self.canonical_json, decision.to_dict())
        _require_equal(self.canonical_digest, decision.canonical_digest())
        _require_equal(self.decision_ref, decision.decision_ref)
        _require_equal(self.lease_ref, decision.lease_ref)
        _require_equal(self.lease_identity_decision_ref, decision.lease_identity_decision_ref)
        _require_equal(self.lease_identity_valid, decision.lease_identity_valid)
        _require_equal(self.authorization_model, decision.authorization_model.value)
        _require_equal(self.authorized, decision.authorized)
        _require_equal(self.executable, decision.executable)
        _require_equal(self.reason, decision.reason)
        _require_equal(self.schema_id, decision.schema_id)
        return decision


@dataclass(frozen=True)
class DependencyReceiptContract:
    decision_ref: str
    work_item_id: str | None
    dependencies_satisfied: bool
    reason: str
    schema_id: str
    canonical_json: str = field(repr=False)
    canonical_digest: str = field(repr=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DependencyReceiptContract":
        try:
            raw = require_exact_keys(payload, "dependency_receipt", DEPENDENCY_RECEIPT_KEYS)
            schema_id = require_string(raw.get("schema_id"), "dependency_receipt.schema_id")
            if schema_id != DEPENDENCY_DECISION_SCHEMA_ID:
                raise _integrity_failure()
            work_item_id = raw.get("work_item_id")
            if work_item_id is not None:
                work_item_id = require_contract_ref(work_item_id, "dependency_receipt.work_item_id")
            return cls(
                decision_ref=require_contract_ref(raw.get("decision_ref"), "dependency_receipt.decision_ref"),
                work_item_id=work_item_id,
                dependencies_satisfied=require_sqlite_boolean(
                    raw.get("dependencies_satisfied"),
                    "dependency_receipt.dependencies_satisfied",
                ),
                reason=require_string(raw.get("reason"), "dependency_receipt.reason"),
                schema_id=schema_id,
                canonical_json=require_string(raw.get("canonical_json"), "dependency_receipt.canonical_json"),
                canonical_digest=require_digest(raw.get("canonical_digest"), "dependency_receipt.canonical_digest"),
            )
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc

    def reconstruct(self) -> DependencyDecision:
        try:
            decision = DependencyDecision.from_json(self.canonical_json)
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc
        _require_exact_canonical_json(self.canonical_json, decision.to_dict())
        _require_equal(self.canonical_digest, decision.canonical_digest())
        _require_equal(self.decision_ref, decision.decision_ref)
        _require_equal(self.work_item_id, decision.work_item_id)
        _require_equal(self.dependencies_satisfied, decision.dependencies_satisfied)
        _require_equal(self.reason, decision.reason)
        _require_equal(self.schema_id, decision.schema_id)
        return decision


@dataclass(frozen=True)
class AdmittedBacklogRecordContract:
    backlog_id: str
    lease_ref: str
    schema_id: str
    schema_version: int
    content_digest: str = field(repr=False)
    canonical_json: str = field(repr=False)
    admitted_at: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AdmittedBacklogRecordContract":
        try:
            raw = require_exact_keys(payload, "admitted_backlog_row", ADMITTED_BACKLOG_ROW_KEYS)
            schema_id = require_string(raw.get("schema_id"), "admitted_backlog_row.schema_id")
            if schema_id != BACKLOG_SCHEMA_ID:
                raise _integrity_failure()
            schema_version = _require_exact_row_int(
                raw.get("schema_version"),
                "admitted_backlog_row.schema_version",
                expected=BACKLOG_SCHEMA_VERSION,
            )
            return cls(
                backlog_id=require_contract_ref(raw.get("backlog_id"), "admitted_backlog_row.backlog_id"),
                lease_ref=require_contract_ref(raw.get("lease_ref"), "admitted_backlog_row.lease_ref"),
                schema_id=schema_id,
                schema_version=schema_version,
                content_digest=require_digest(raw.get("content_digest"), "admitted_backlog_row.content_digest"),
                canonical_json=_require_bounded_canonical_json(
                    raw.get("canonical_json"),
                    "admitted_backlog_row.canonical_json",
                ),
                admitted_at=_require_canonical_utc_timestamp(
                    raw.get("admitted_at"),
                    "admitted_backlog_row.admitted_at",
                ),
            )
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc

    def reconstruct(self) -> AdmittedBacklogRecordEnvelope:
        try:
            backlog = FiniteBacklog.from_json(self.canonical_json)
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc
        _require_exact_canonical_json(self.canonical_json, backlog.to_dict())
        _require_equal(self.backlog_id, backlog.backlog_id)
        _require_equal(self.lease_ref, backlog.lease_reference)
        _require_equal(self.schema_id, backlog.schema_id)
        _require_equal(self.schema_version, backlog.schema_version)
        _require_equal(self.content_digest, backlog.content_digest)
        return AdmittedBacklogRecordEnvelope(backlog=backlog, admitted_at=self.admitted_at)


@dataclass(frozen=True)
class GlobalStopCurrentRecordContract:
    singleton_id: int
    schema_id: str
    version: int
    active: bool
    stop_id: str | None
    reason_class: str | None
    issuer_ref: str | None
    issued_at: str | None
    operator_decision_ref: str | None
    updated_at: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GlobalStopCurrentRecordContract":
        try:
            raw = require_exact_keys(payload, "global_stop_current_row", GLOBAL_STOP_CURRENT_ROW_KEYS)
            singleton_id = _require_exact_row_int(
                raw.get("singleton_id"),
                "global_stop_current_row.singleton_id",
                expected=1,
            )
            schema_id = require_string(raw.get("schema_id"), "global_stop_current_row.schema_id")
            if schema_id != GLOBAL_STOP_SCHEMA_ID:
                raise _integrity_failure()
            version = _require_row_non_negative_int(raw.get("version"), "global_stop_current_row.version")
            active = require_sqlite_boolean(raw.get("active"), "global_stop_current_row.active")
            updated_at = _require_canonical_utc_timestamp(
                raw.get("updated_at"),
                "global_stop_current_row.updated_at",
            )
            nullable_fields = (
                raw.get("stop_id"),
                raw.get("reason_class"),
                raw.get("issuer_ref"),
                raw.get("issued_at"),
                raw.get("operator_decision_ref"),
            )
            if active:
                stop_id = require_contract_ref(raw.get("stop_id"), "global_stop_current_row.stop_id")
                reason_class = require_string(raw.get("reason_class"), "global_stop_current_row.reason_class")
                issuer_ref = require_contract_ref(raw.get("issuer_ref"), "global_stop_current_row.issuer_ref")
                issued_at = _require_canonical_utc_timestamp(
                    raw.get("issued_at"),
                    "global_stop_current_row.issued_at",
                )
                operator_decision_ref = require_contract_ref(
                    raw.get("operator_decision_ref"),
                    "global_stop_current_row.operator_decision_ref",
                )
            else:
                if any(value is not None for value in nullable_fields):
                    raise _integrity_failure()
                stop_id = None
                reason_class = None
                issuer_ref = None
                issued_at = None
                operator_decision_ref = None
            return cls(
                singleton_id=singleton_id,
                schema_id=schema_id,
                version=version,
                active=active,
                stop_id=stop_id,
                reason_class=reason_class,
                issuer_ref=issuer_ref,
                issued_at=issued_at,
                operator_decision_ref=operator_decision_ref,
                updated_at=updated_at,
            )
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc

    def reconstruct(self) -> GlobalStopCurrentRecordEnvelope:
        try:
            state = GlobalStopState(
                schema_id=self.schema_id,
                version=self.version,
                active=self.active,
                stop_id=self.stop_id,
                reason_class=self.reason_class,
                issuer_ref=self.issuer_ref,
                issued_at=self.issued_at,
                operator_decision_ref=self.operator_decision_ref,
            )
        except (TypeError, ValueError) as exc:
            raise _integrity_failure() from exc
        return GlobalStopCurrentRecordEnvelope(state=state, updated_at=self.updated_at)


def lease_identity_record_envelope_from_row(payload: Mapping[str, Any]) -> LeaseIdentityRecordEnvelope:
    try:
        raw = require_exact_keys(payload, "lease_identity_record_row", LEASE_IDENTITY_RECORD_ROW_KEYS)
        created_at = _require_canonical_utc_timestamp(
            raw.get("created_at"),
            "lease_identity_record_row.created_at",
        )
        reconstruction = LeaseIdentityRecordContract.from_dict(
            _row_projection(raw, LEASE_IDENTITY_RECORD_KEYS)
        ).reconstruct()
        return LeaseIdentityRecordEnvelope(reconstruction=reconstruction, created_at=created_at)
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc


def authorization_receipt_envelope_from_row(payload: Mapping[str, Any]) -> AuthorizationReceiptEnvelope:
    try:
        raw = require_exact_keys(payload, "authorization_receipt_row", AUTHORIZATION_RECEIPT_ROW_KEYS)
        created_at = _require_canonical_utc_timestamp(
            raw.get("created_at"),
            "authorization_receipt_row.created_at",
        )
        decision = AuthorizationReceiptContract.from_dict(_row_projection(raw, AUTHORIZATION_RECEIPT_KEYS)).reconstruct()
        return AuthorizationReceiptEnvelope(decision=decision, created_at=created_at)
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc


def dependency_receipt_envelope_from_row(payload: Mapping[str, Any]) -> DependencyReceiptEnvelope:
    try:
        raw = require_exact_keys(payload, "dependency_receipt_row", DEPENDENCY_RECEIPT_ROW_KEYS)
        created_at = _require_canonical_utc_timestamp(
            raw.get("created_at"),
            "dependency_receipt_row.created_at",
        )
        decision = DependencyReceiptContract.from_dict(_row_projection(raw, DEPENDENCY_RECEIPT_KEYS)).reconstruct()
        return DependencyReceiptEnvelope(decision=decision, created_at=created_at)
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc


def work_item_record_envelope_from_row(payload: Mapping[str, Any]) -> WorkItemRecordEnvelope:
    try:
        raw = require_exact_keys(payload, "work_item_row", WORK_ITEM_ROW_KEYS)
        schema_id = require_string(raw.get("schema_id"), "work_item_row.schema_id")
        if schema_id != WORK_ITEM_STATE_SCHEMA_ID:
            raise _integrity_failure()
        updated_at = _require_canonical_utc_timestamp(raw.get("updated_at"), "work_item_row.updated_at")
        record = WorkItemRecord(
            schema_id=schema_id,
            work_item_id=raw.get("work_item_id"),
            lease_id=raw.get("lease_id"),
            backlog_id=raw.get("backlog_id"),
            state=require_work_item_state(raw.get("state"), "work_item_row.state"),
            version=raw.get("version"),
            attempt_count=raw.get("attempt_count"),
            repair_count=raw.get("repair_count"),
            budget_consumed=raw.get("budget_consumed"),
            budget_limit=raw.get("budget_limit"),
            max_attempts=raw.get("max_attempts"),
            max_repairs=raw.get("max_repairs"),
            cleanup_required=require_sqlite_boolean(raw.get("cleanup_required"), "work_item_row.cleanup_required"),
        )
        return WorkItemRecordEnvelope(record=record, updated_at=updated_at)
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc


def work_item_record_from_row(payload: Mapping[str, Any]) -> WorkItemRecord:
    return work_item_record_envelope_from_row(payload).record


def admitted_backlog_record_envelope_from_row(payload: Mapping[str, Any]) -> AdmittedBacklogRecordEnvelope:
    return AdmittedBacklogRecordContract.from_dict(payload).reconstruct()


def global_stop_current_envelope_from_row(payload: Mapping[str, Any]) -> GlobalStopCurrentRecordEnvelope:
    return GlobalStopCurrentRecordContract.from_dict(payload).reconstruct()


def classify_authorization_model_for_b3(
    decision: AuthorizationDecision,
) -> B3AuthorizationModelHandling:
    if decision.authorization_model is AuthorizationModel.UNSUPPORTED:
        return B3AuthorizationModelHandling.FAIL_CLOSED_UNSUPPORTED
    return B3AuthorizationModelHandling.UNSUPPORTED_AUTHORITATIVE_MODEL


def validate_b3_work_item_authority_binding(
    lease: StandingLease,
    backlog: FiniteBacklog,
    record: WorkItemRecord,
) -> WorkItem:
    """Validate the B3 v1 lease/backlog/work-item read bundle.

    This is a pure prerequisite contract for future SQLite readers. It returns
    the matched canonical backlog work item and otherwise raises only the safe
    database-integrity store classification.
    """

    try:
        if not isinstance(lease, StandingLease):
            raise ValueError("invalid_field_type:b3_authority.lease")
        if not isinstance(backlog, FiniteBacklog):
            raise ValueError("invalid_field_type:b3_authority.backlog")
        if not isinstance(record, WorkItemRecord):
            raise ValueError("invalid_field_type:b3_authority.record")

        canonical_backlog = FiniteBacklog.from_dict(backlog.to_dict())
        _require_equal(canonical_backlog.schema_id, BACKLOG_SCHEMA_ID)
        _require_equal(canonical_backlog.schema_version, BACKLOG_SCHEMA_VERSION)
        _require_equal(record.backlog_id, canonical_backlog.backlog_id)
        _require_equal(canonical_backlog.backlog_id, lease.finite_backlog_reference)
        _require_equal(canonical_backlog.lease_reference, record.lease_id)
        _require_equal(record.lease_id, lease.lease_id)
        _require_equal(canonical_backlog.content_digest, lease.finite_backlog_digest)

        if len(canonical_backlog.work_items) > lease.max_work_items:
            raise _integrity_failure()
        matched_items = tuple(
            item for item in canonical_backlog.work_items if item.work_item_id == record.work_item_id
        )
        if len(matched_items) != 1:
            raise _integrity_failure()

        _validate_b3_limit_provenance(lease, record)
        _validate_b3_zero_scalar_budget(record)
        _validate_b3_static_budget_policy(lease, canonical_backlog)
        return matched_items[0]
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc


def next_transition_event_sequence(max_event_sequence: int | None) -> int:
    if max_event_sequence is None:
        return FIRST_TRANSITION_EVENT_SEQUENCE
    if not isinstance(max_event_sequence, int) or isinstance(max_event_sequence, bool) or max_event_sequence < 0:
        raise _integrity_failure()
    if max_event_sequence >= SQLITE_SIGNED_INT_MAX:
        raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.EVENT_SEQUENCE_EXHAUSTED)
    return max_event_sequence + 1


def normalize_transaction_timestamp(value: Any) -> str:
    return require_utc_timestamp(value, "transaction_timestamp")


def encode_sqlite_boolean(value: bool, field_name: str) -> int:
    if type(value) is not bool:
        raise _integrity_failure()
    return 1 if value else 0


def _require_exact_canonical_json(text: str, payload: Mapping[str, Any]) -> None:
    _require_equal(text, canonical_json_bytes(payload).decode("utf-8"))


def _require_bounded_canonical_json(value: Any, field_name: str) -> str:
    text = require_string(value, field_name)
    if len(text.encode("utf-8")) > _MAX_CANONICAL_JSON_BYTES:
        raise _integrity_failure()
    return text


def _require_canonical_utc_timestamp(value: Any, field_name: str) -> str:
    try:
        normalized = require_utc_timestamp(value, field_name)
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc
    if type(value) is not str or value != normalized:
        raise _integrity_failure()
    return normalized


def require_sqlite_boolean(value: Any, field_name: str) -> bool:
    if type(value) is not int or value not in (0, 1):
        raise _integrity_failure()
    return bool(value)


def _require_equal(left: Any, right: Any) -> None:
    if left != right:
        raise _integrity_failure()


def _require_exact_row_int(value: Any, field_name: str, *, expected: int) -> int:
    if type(value) is not int or value != expected:
        raise _integrity_failure()
    return value


def _require_row_non_negative_int(value: Any, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise _integrity_failure()
    return value


def _row_projection(raw: Mapping[str, Any], keys: frozenset[str]) -> dict[str, Any]:
    return {key: raw[key] for key in keys}


def _validate_b3_limit_provenance(lease: StandingLease, record: WorkItemRecord) -> None:
    _require_equal(record.max_attempts, lease.max_attempts)
    _require_equal(record.max_repairs, lease.max_repairs)
    if record.attempt_count > record.max_attempts:
        raise _integrity_failure()
    if record.repair_count > record.max_repairs:
        raise _integrity_failure()


def _validate_b3_zero_scalar_budget(record: WorkItemRecord) -> None:
    if record.budget_consumed != 0:
        raise _integrity_failure()
    if record.budget_limit != 0:
        raise _integrity_failure()


def _validate_b3_static_budget_policy(lease: StandingLease, backlog: FiniteBacklog) -> None:
    lease_api_calls = _budget_dimension(lease.compute_api_budget, "api_calls")
    lease_compute_seconds = _budget_dimension(lease.compute_api_budget, "compute_seconds")
    total_api_calls = 0
    total_compute_seconds = 0
    for item in backlog.work_items:
        item_api_calls = _budget_dimension(item.budget_allocation, "api_calls")
        item_compute_seconds = _budget_dimension(item.budget_allocation, "compute_seconds")
        if item_api_calls > lease_api_calls:
            raise _integrity_failure()
        if item_compute_seconds > lease_compute_seconds:
            raise _integrity_failure()
        total_api_calls += item_api_calls
        total_compute_seconds += item_compute_seconds
    if total_api_calls > lease_api_calls:
        raise _integrity_failure()
    if total_compute_seconds > lease_compute_seconds:
        raise _integrity_failure()


def _budget_dimension(payload: Mapping[str, Any], field_name: str) -> int:
    value = payload.get(field_name)
    if type(value) is not int or value < 0:
        raise _integrity_failure()
    return value


def _integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
