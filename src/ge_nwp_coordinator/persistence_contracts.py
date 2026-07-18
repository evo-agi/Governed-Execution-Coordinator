"""Pure B3a persistence contracts for future SQLite transition apply.

B3a defines canonical row mappings and safe future error boundaries only. This
module must not open SQLite, allocate sequences from a database, or mutate state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256, require_exact_keys, require_string
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

LEASE_IDENTITY_RECORD_KEYS = frozenset(
    {
        "decision_ref",
        "lease_ref",
        "identity_valid",
        "lease_digest",
        "schema_id",
        "canonical_json",
        "canonical_digest",
    }
)
AUTHORIZATION_RECEIPT_KEYS = frozenset(
    {
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
    }
)
DEPENDENCY_RECEIPT_KEYS = frozenset(
    {
        "decision_ref",
        "work_item_id",
        "dependencies_satisfied",
        "reason",
        "schema_id",
        "canonical_json",
        "canonical_digest",
    }
)
WORK_ITEM_ROW_KEYS = frozenset(
    {
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
    }
)


class B3AuthorizationModelHandling(str, Enum):
    FAIL_CLOSED_UNSUPPORTED = "fail_closed_unsupported"
    UNSUPPORTED_AUTHORITATIVE_MODEL = "unsupported_authoritative_model"


@dataclass(frozen=True)
class LeaseIdentityRecordReconstruction:
    lease: StandingLease
    validation: LeaseIdentityValidation


@dataclass(frozen=True)
class LeaseIdentityRecordContract:
    decision_ref: str
    lease_ref: str
    identity_valid: bool
    lease_digest: str | None
    schema_id: str
    canonical_json: str
    canonical_digest: str

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
    canonical_json: str
    canonical_digest: str

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
    canonical_json: str
    canonical_digest: str

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


def work_item_record_from_row(payload: Mapping[str, Any]) -> WorkItemRecord:
    try:
        raw = require_exact_keys(payload, "work_item_row", WORK_ITEM_ROW_KEYS)
        schema_id = require_string(raw.get("schema_id"), "work_item_row.schema_id")
        if schema_id != WORK_ITEM_STATE_SCHEMA_ID:
            raise _integrity_failure()
        require_utc_timestamp(raw.get("updated_at"), "work_item_row.updated_at")
        return WorkItemRecord(
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
    except (TypeError, ValueError) as exc:
        raise _integrity_failure() from exc


def classify_authorization_model_for_b3(
    decision: AuthorizationDecision,
) -> B3AuthorizationModelHandling:
    if decision.authorization_model is AuthorizationModel.UNSUPPORTED:
        return B3AuthorizationModelHandling.FAIL_CLOSED_UNSUPPORTED
    return B3AuthorizationModelHandling.UNSUPPORTED_AUTHORITATIVE_MODEL


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


def require_sqlite_boolean(value: Any, field_name: str) -> bool:
    if type(value) is not int or value not in (0, 1):
        raise _integrity_failure()
    return bool(value)


def _require_equal(left: Any, right: Any) -> None:
    if left != right:
        raise _integrity_failure()


def _integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
