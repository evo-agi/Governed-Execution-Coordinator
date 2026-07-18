"""Standing lease identity and fail-closed authorization boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from ge_nwp_coordinator.canonicalization import (
    canonical_json_bytes,
    canonical_sha256,
    decode_json_object,
    require_exact_keys,
    require_bool,
    require_non_negative_int,
    require_object,
    require_positive_int,
    require_safe_ref_list,
    require_safe_ref,
    require_safe_ref_tuple,
    require_safe_relative_path_list,
    require_safe_relative_path_tuple,
    require_safe_string,
    require_string,
    normalize_set_like_strings,
)
from ge_nwp_coordinator.models import (
    ValidationIssue,
    require_contract_ref,
    require_reason_class,
    safe_issue_from_exception,
)

LEASE_SCHEMA_ID = "governed-execution.nwp-standing-lease.v1"
LEASE_SCHEMA_VERSION = 1
AUTHORIZATION_DECISION_SCHEMA_ID = "governed-execution.nwp-authorization-decision.v1"
LEASE_RUNTIME_DECISION_SCHEMA_ID = "governed-execution.nwp-lease-runtime-decision.v1"
CANONICALIZATION_ID = "governed-execution.nwp-json-canonical.v1"
SHA256_HEX_LENGTH = 64
LEASE_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "lease_id",
        "issuer_label",
        "issued_at",
        "valid_from",
        "expires_at",
        "revocation_state",
        "revocation_reference",
        "subject",
        "repo_identity",
        "branch_policy",
        "allowed_paths",
        "forbidden_path_policy_identity",
        "task_classes",
        "risk_lanes",
        "finite_backlog_reference",
        "finite_backlog_digest",
        "max_work_items",
        "max_concurrency",
        "max_attempts",
        "max_repairs",
        "compute_api_budget",
        "wall_clock_budget_seconds",
        "validation_requirements",
        "audit_requirements",
        "local_commit_permission",
        "publication_permission",
        "cross_repo_permission",
        "maintenance_permission",
        "cleanup_requirements",
        "reporting_cadence",
        "retention_policy",
        "global_stop_reference",
        "canonical_digest_metadata",
        "authorization_mechanism",
    }
)
REPO_IDENTITY_KEYS = frozenset({"component", "repo_label"})
BRANCH_POLICY_KEYS = frozenset({"base", "mode"})
COMPUTE_API_BUDGET_KEYS = frozenset({"api_calls", "compute_seconds"})
CANONICAL_DIGEST_METADATA_KEYS = frozenset({"algorithm", "canonicalization", "digest"})
AUTHORIZATION_MECHANISM_KEYS = frozenset({"kind", "descriptor"})
AUTHORIZATION_DECISION_KEYS = frozenset(
    {
        "schema_id",
        "decision_ref",
        "lease_ref",
        "lease_identity_decision_ref",
        "lease_identity_valid",
        "authorization_model",
        "authorized",
        "executable",
        "reason",
    }
)
LEASE_RUNTIME_DECISION_KEYS = frozenset({"schema_id", "lease_ref", "evaluated_at", "status", "reason"})


class LeaseRevocationState(str, Enum):
    NOT_REVOKED = "not_revoked"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class Permission(str, Enum):
    FORBIDDEN = "forbidden"
    ALLOWED = "allowed"


class AuthorizationModel(str, Enum):
    UNSUPPORTED = "unsupported"
    OPERATOR_POLICY = "operator_policy"


class LeaseRuntimeStatus(str, Enum):
    ACTIVE = "active"
    NOT_YET_VALID = "not_yet_valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REVOCATION_UNKNOWN = "revocation_unknown"


@dataclass(frozen=True)
class LeaseIdentityValidation:
    identity_valid: bool
    digest: str | None
    issues: tuple[ValidationIssue, ...]
    decision_ref: str
    lease_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "identity_valid", require_bool(self.identity_valid, "lease_identity.identity_valid"))
        if self.digest is not None:
            object.__setattr__(self, "digest", require_digest(self.digest, "lease_identity.digest"))
        if not isinstance(self.issues, tuple):
            raise ValueError("invalid_field_type:lease_identity.issues")
        object.__setattr__(
            self,
            "issues",
            tuple(require_contract_issue(issue, "lease_identity.issues[]") for issue in self.issues),
        )
        object.__setattr__(
            self,
            "decision_ref",
            require_contract_ref(self.decision_ref, "lease_identity.decision_ref"),
        )
        object.__setattr__(self, "lease_ref", require_contract_ref(self.lease_ref, "lease_identity.lease_ref"))
        if self.identity_valid and self.issues:
            raise ValueError("invalid_field_value:lease_identity.issues")
        if not self.identity_valid and not self.issues:
            raise ValueError("invalid_field_value:lease_identity.issues")

    @property
    def issue_reasons(self) -> tuple[str, ...]:
        return tuple(issue.reason for issue in self.issues)

    @property
    def issue_fields(self) -> tuple[str, ...]:
        return tuple(issue.field for issue in self.issues)


@dataclass(frozen=True)
class AuthorizationDecision:
    decision_ref: str
    lease_ref: str
    lease_identity_decision_ref: str
    lease_identity_valid: bool
    authorization_model: AuthorizationModel = AuthorizationModel.UNSUPPORTED
    authorized: bool = False
    executable: bool = False
    reason: str = "unsupported_authorization_model"
    schema_id: str = AUTHORIZATION_DECISION_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "authorization_decision.schema_id") != AUTHORIZATION_DECISION_SCHEMA_ID:
            raise ValueError("invalid_field_type:authorization_decision.schema_id")
        object.__setattr__(
            self,
            "decision_ref",
            require_contract_ref(self.decision_ref, "authorization_decision.decision_ref"),
        )
        object.__setattr__(self, "lease_ref", require_contract_ref(self.lease_ref, "authorization_decision.lease_ref"))
        object.__setattr__(
            self,
            "lease_identity_decision_ref",
            require_contract_ref(
                self.lease_identity_decision_ref,
                "authorization_decision.lease_identity_decision_ref",
            ),
        )
        object.__setattr__(
            self,
            "lease_identity_valid",
            require_bool(self.lease_identity_valid, "authorization_decision.lease_identity_valid"),
        )
        object.__setattr__(
            self,
            "authorization_model",
            _require_authorization_model(self.authorization_model, "authorization_decision.authorization_model"),
        )
        object.__setattr__(self, "authorized", require_bool(self.authorized, "authorization_decision.authorized"))
        object.__setattr__(self, "executable", require_bool(self.executable, "authorization_decision.executable"))
        object.__setattr__(self, "reason", require_reason_class(self.reason, "authorization_decision.reason"))
        if self.executable and not self.authorized:
            raise ValueError("invalid_field_value:authorization_decision.executable")
        if self.reason == "accepted" and not self.authorized:
            raise ValueError("invalid_field_value:authorization_decision.reason")
        if self.authorized and self.reason != "accepted":
            raise ValueError("invalid_field_value:authorization_decision.reason")
        if not self.lease_identity_valid and (self.authorized or self.executable):
            raise ValueError("invalid_field_value:authorization_decision.lease_identity_valid")
        if self.authorization_model is AuthorizationModel.UNSUPPORTED:
            if self.authorized or self.executable or self.reason != "unsupported_authorization_model":
                raise ValueError("invalid_field_value:authorization_decision.unsupported_model")

    @property
    def identity_valid(self) -> bool:
        return self.lease_identity_valid

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AuthorizationDecision":
        raw = require_exact_keys(payload, "authorization_decision", AUTHORIZATION_DECISION_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            decision_ref=raw.get("decision_ref"),
            lease_ref=raw.get("lease_ref"),
            lease_identity_decision_ref=raw.get("lease_identity_decision_ref"),
            lease_identity_valid=raw.get("lease_identity_valid"),
            authorization_model=raw.get("authorization_model"),
            authorized=raw.get("authorized"),
            executable=raw.get("executable"),
            reason=raw.get("reason"),
        )

    @classmethod
    def from_json(cls, text: str) -> "AuthorizationDecision":
        return cls.from_dict(decode_json_object(text, "authorization_decision"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "decision_ref": self.decision_ref,
            "lease_ref": self.lease_ref,
            "lease_identity_decision_ref": self.lease_identity_decision_ref,
            "lease_identity_valid": self.lease_identity_valid,
            "authorization_model": self.authorization_model.value,
            "authorized": self.authorized,
            "executable": self.executable,
            "reason": self.reason,
        }

    def canonical_identity_payload(self) -> dict[str, Any]:
        return self.to_dict()

    def canonical_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.canonical_identity_payload())

    def canonical_json(self) -> str:
        return self.canonical_json_bytes().decode("utf-8")

    def canonical_digest(self) -> str:
        return canonical_sha256(self.canonical_identity_payload())


@dataclass(frozen=True)
class LeaseRuntimeDecision:
    lease_ref: str
    evaluated_at: str
    status: LeaseRuntimeStatus
    reason: str
    schema_id: str = LEASE_RUNTIME_DECISION_SCHEMA_ID

    def __post_init__(self) -> None:
        if require_string(self.schema_id, "lease_runtime.schema_id") != LEASE_RUNTIME_DECISION_SCHEMA_ID:
            raise ValueError("invalid_field_type:lease_runtime.schema_id")
        object.__setattr__(self, "lease_ref", require_contract_ref(self.lease_ref, "lease_runtime.lease_ref"))
        object.__setattr__(self, "evaluated_at", require_utc_timestamp(self.evaluated_at, "lease_runtime.evaluated_at"))
        object.__setattr__(self, "status", _require_lease_runtime_status(self.status, "lease_runtime.status"))
        object.__setattr__(self, "reason", require_reason_class(self.reason, "lease_runtime.reason"))
        expected_reason = {
            LeaseRuntimeStatus.ACTIVE: "lease_runtime_active",
            LeaseRuntimeStatus.NOT_YET_VALID: "lease_not_yet_valid",
            LeaseRuntimeStatus.EXPIRED: "lease_expired",
            LeaseRuntimeStatus.REVOKED: "lease_revoked",
            LeaseRuntimeStatus.REVOCATION_UNKNOWN: "lease_revocation_unknown",
        }[self.status]
        if self.reason != expected_reason:
            raise ValueError("invalid_field_value:lease_runtime.reason")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LeaseRuntimeDecision":
        raw = require_exact_keys(payload, "lease_runtime", LEASE_RUNTIME_DECISION_KEYS)
        return cls(
            schema_id=raw.get("schema_id"),
            lease_ref=raw.get("lease_ref"),
            evaluated_at=raw.get("evaluated_at"),
            status=raw.get("status"),
            reason=raw.get("reason"),
        )

    @classmethod
    def from_json(cls, text: str) -> "LeaseRuntimeDecision":
        return cls.from_dict(decode_json_object(text, "lease_runtime"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "lease_ref": self.lease_ref,
            "evaluated_at": self.evaluated_at,
            "status": self.status.value,
            "reason": self.reason,
        }

    def canonical_json_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def canonical_json(self) -> str:
        return self.canonical_json_bytes().decode("utf-8")

    def canonical_digest(self) -> str:
        return canonical_sha256(self.to_dict())


class AuthorizationProvider(Protocol):
    """Boundary for future operator/repo authorization verification."""

    def authorize(self, lease: "StandingLease") -> AuthorizationDecision:
        """Return a fail-closed authorization decision for a parsed lease."""


class UnsupportedAuthorizationProvider:
    """Production/default provider until an issuer trust model is selected."""

    def authorize(self, lease: "StandingLease") -> AuthorizationDecision:
        validation = lease.validate_identity()
        return AuthorizationDecision(
            decision_ref=f"authz-{lease.lease_id}",
            lease_ref=lease.lease_id,
            lease_identity_decision_ref=validation.decision_ref,
            lease_identity_valid=validation.identity_valid,
            authorized=False,
            executable=False,
            reason="unsupported_authorization_model",
        )


@dataclass(frozen=True)
class StandingLease:
    schema_id: str
    schema_version: int
    lease_id: str
    issuer_label: str
    issued_at: str
    valid_from: str
    expires_at: str
    revocation_state: LeaseRevocationState
    revocation_reference: str | None
    subject: str
    repo_identity: Mapping[str, Any]
    branch_policy: Mapping[str, Any]
    allowed_paths: tuple[str, ...]
    forbidden_path_policy_identity: str
    task_classes: tuple[str, ...]
    risk_lanes: tuple[str, ...]
    finite_backlog_reference: str
    finite_backlog_digest: str
    max_work_items: int
    max_concurrency: int
    max_attempts: int
    max_repairs: int
    compute_api_budget: Mapping[str, Any]
    wall_clock_budget_seconds: int
    validation_requirements: tuple[str, ...]
    audit_requirements: tuple[str, ...]
    local_commit_permission: Permission
    publication_permission: Permission
    cross_repo_permission: Permission
    maintenance_permission: Permission
    cleanup_requirements: tuple[str, ...]
    reporting_cadence: str
    retention_policy: str
    global_stop_reference: str
    canonical_digest_metadata: Mapping[str, Any]
    authorization_mechanism: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_safe_string(self.schema_id, "schema_id"))
        object.__setattr__(self, "schema_version", require_positive_int(self.schema_version, "schema_version"))
        object.__setattr__(self, "lease_id", require_safe_ref(self.lease_id, "lease_id"))
        object.__setattr__(self, "issuer_label", require_safe_ref(self.issuer_label, "issuer_label"))
        object.__setattr__(self, "issued_at", require_safe_string(self.issued_at, "issued_at"))
        object.__setattr__(self, "valid_from", require_safe_string(self.valid_from, "valid_from"))
        object.__setattr__(self, "expires_at", require_safe_string(self.expires_at, "expires_at"))
        object.__setattr__(self, "revocation_state", _require_revocation_state(self.revocation_state))
        if self.revocation_reference is not None:
            object.__setattr__(
                self,
                "revocation_reference",
                require_safe_ref(self.revocation_reference, "revocation_reference"),
            )
        object.__setattr__(self, "subject", require_safe_ref(self.subject, "subject"))
        object.__setattr__(self, "repo_identity", _require_repo_identity(self.repo_identity))
        object.__setattr__(self, "branch_policy", _require_branch_policy(self.branch_policy))
        object.__setattr__(
            self,
            "allowed_paths",
            normalize_set_like_strings(
                require_safe_relative_path_tuple(self.allowed_paths, "allowed_paths", ordered=True),
                "allowed_paths",
            ),
        )
        object.__setattr__(self, "forbidden_path_policy_identity", require_safe_ref(
            self.forbidden_path_policy_identity,
            "forbidden_path_policy_identity",
        ))
        object.__setattr__(
            self,
            "task_classes",
            normalize_set_like_strings(require_safe_ref_tuple(self.task_classes, "task_classes"), "task_classes"),
        )
        object.__setattr__(
            self,
            "risk_lanes",
            normalize_set_like_strings(require_safe_ref_tuple(self.risk_lanes, "risk_lanes"), "risk_lanes"),
        )
        object.__setattr__(
            self,
            "finite_backlog_reference",
            require_safe_ref(self.finite_backlog_reference, "finite_backlog_reference"),
        )
        object.__setattr__(
            self,
            "finite_backlog_digest",
            require_digest(self.finite_backlog_digest, "finite_backlog_digest"),
        )
        object.__setattr__(self, "max_work_items", require_positive_int(self.max_work_items, "max_work_items"))
        object.__setattr__(self, "max_concurrency", require_positive_int(self.max_concurrency, "max_concurrency"))
        object.__setattr__(self, "max_attempts", require_positive_int(self.max_attempts, "max_attempts"))
        object.__setattr__(self, "max_repairs", require_non_negative_int(self.max_repairs, "max_repairs"))
        object.__setattr__(self, "compute_api_budget", _require_compute_api_budget(self.compute_api_budget))
        object.__setattr__(
            self,
            "wall_clock_budget_seconds",
            require_positive_int(self.wall_clock_budget_seconds, "wall_clock_budget_seconds"),
        )
        object.__setattr__(
            self,
            "validation_requirements",
            normalize_set_like_strings(
                require_safe_ref_tuple(self.validation_requirements, "validation_requirements"),
                "validation_requirements",
            ),
        )
        object.__setattr__(
            self,
            "audit_requirements",
            normalize_set_like_strings(
                require_safe_ref_tuple(self.audit_requirements, "audit_requirements"),
                "audit_requirements",
            ),
        )
        object.__setattr__(self, "local_commit_permission", _require_permission(
            self.local_commit_permission,
            "local_commit_permission",
        ))
        object.__setattr__(self, "publication_permission", _require_permission(
            self.publication_permission,
            "publication_permission",
        ))
        object.__setattr__(self, "cross_repo_permission", _require_permission(
            self.cross_repo_permission,
            "cross_repo_permission",
        ))
        object.__setattr__(self, "maintenance_permission", _require_permission(
            self.maintenance_permission,
            "maintenance_permission",
        ))
        object.__setattr__(
            self,
            "cleanup_requirements",
            normalize_set_like_strings(
                require_safe_ref_tuple(self.cleanup_requirements, "cleanup_requirements"),
                "cleanup_requirements",
            ),
        )
        object.__setattr__(self, "reporting_cadence", require_safe_ref(self.reporting_cadence, "reporting_cadence"))
        object.__setattr__(self, "retention_policy", require_safe_ref(self.retention_policy, "retention_policy"))
        object.__setattr__(
            self,
            "global_stop_reference",
            require_safe_ref(self.global_stop_reference, "global_stop_reference"),
        )
        object.__setattr__(
            self,
            "canonical_digest_metadata",
            _require_digest_metadata(self.canonical_digest_metadata, require_digest_value=False),
        )
        object.__setattr__(
            self,
            "authorization_mechanism",
            _require_authorization_mechanism(self.authorization_mechanism),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "StandingLease":
        raw = require_exact_keys(payload, "lease", LEASE_KEYS)
        schema_id = require_string(raw.get("schema_id"), "schema_id")
        if schema_id != LEASE_SCHEMA_ID:
            raise ValueError("unsupported lease schema_id")
        schema_version = require_positive_int(raw.get("schema_version"), "schema_version")
        if schema_version != LEASE_SCHEMA_VERSION:
            raise ValueError("unsupported lease schema_version")
        revocation_state = _require_revocation_state(raw.get("revocation_state"))
        revocation_reference = raw.get("revocation_reference")
        if revocation_reference is not None:
            revocation_reference = require_safe_ref(revocation_reference, "revocation_reference")

        return cls(
            schema_id=schema_id,
            schema_version=schema_version,
            lease_id=require_safe_ref(raw.get("lease_id"), "lease_id"),
            issuer_label=require_safe_ref(raw.get("issuer_label"), "issuer_label"),
            issued_at=require_safe_string(raw.get("issued_at"), "issued_at"),
            valid_from=require_safe_string(raw.get("valid_from"), "valid_from"),
            expires_at=require_safe_string(raw.get("expires_at"), "expires_at"),
            revocation_state=revocation_state,
            revocation_reference=revocation_reference,
            subject=require_safe_ref(raw.get("subject"), "subject"),
            repo_identity=_require_repo_identity(raw.get("repo_identity")),
            branch_policy=_require_branch_policy(raw.get("branch_policy")),
            allowed_paths=require_safe_relative_path_list(raw.get("allowed_paths"), "allowed_paths", ordered=False),
            forbidden_path_policy_identity=require_safe_ref(
                raw.get("forbidden_path_policy_identity"),
                "forbidden_path_policy_identity",
            ),
            task_classes=require_safe_ref_list(raw.get("task_classes"), "task_classes", ordered=False),
            risk_lanes=require_safe_ref_list(raw.get("risk_lanes"), "risk_lanes", ordered=False),
            finite_backlog_reference=require_safe_ref(
                raw.get("finite_backlog_reference"),
                "finite_backlog_reference",
            ),
            finite_backlog_digest=require_digest(raw.get("finite_backlog_digest"), "finite_backlog_digest"),
            max_work_items=require_positive_int(raw.get("max_work_items"), "max_work_items"),
            max_concurrency=require_positive_int(raw.get("max_concurrency"), "max_concurrency"),
            max_attempts=require_positive_int(raw.get("max_attempts"), "max_attempts"),
            max_repairs=require_non_negative_int(raw.get("max_repairs"), "max_repairs"),
            compute_api_budget=_require_compute_api_budget(raw.get("compute_api_budget")),
            wall_clock_budget_seconds=require_positive_int(
                raw.get("wall_clock_budget_seconds"),
                "wall_clock_budget_seconds",
            ),
            validation_requirements=require_safe_ref_list(
                raw.get("validation_requirements"),
                "validation_requirements",
                ordered=False,
            ),
            audit_requirements=require_safe_ref_list(
                raw.get("audit_requirements"),
                "audit_requirements",
                ordered=False,
            ),
            local_commit_permission=_require_permission(raw.get("local_commit_permission"), "local_commit_permission"),
            publication_permission=_require_permission(raw.get("publication_permission"), "publication_permission"),
            cross_repo_permission=_require_permission(raw.get("cross_repo_permission"), "cross_repo_permission"),
            maintenance_permission=_require_permission(raw.get("maintenance_permission"), "maintenance_permission"),
            cleanup_requirements=require_safe_ref_list(
                raw.get("cleanup_requirements"),
                "cleanup_requirements",
                ordered=False,
            ),
            reporting_cadence=require_safe_ref(raw.get("reporting_cadence"), "reporting_cadence"),
            retention_policy=require_safe_ref(raw.get("retention_policy"), "retention_policy"),
            global_stop_reference=require_safe_ref(raw.get("global_stop_reference"), "global_stop_reference"),
            canonical_digest_metadata=_require_digest_metadata(
                raw.get("canonical_digest_metadata"),
                require_digest_value=True,
            ),
            authorization_mechanism=_require_authorization_mechanism(raw.get("authorization_mechanism")),
        )

    @classmethod
    def from_json(cls, text: str) -> "StandingLease":
        return cls.from_dict(decode_json_object(text, "lease"))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        metadata = dict(self.canonical_digest_metadata)
        if not include_digest:
            metadata = {key: value for key, value in metadata.items() if key != "digest"}
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "lease_id": self.lease_id,
            "issuer_label": self.issuer_label,
            "issued_at": self.issued_at,
            "valid_from": self.valid_from,
            "expires_at": self.expires_at,
            "revocation_state": self.revocation_state.value,
            "revocation_reference": self.revocation_reference,
            "subject": self.subject,
            "repo_identity": dict(self.repo_identity),
            "branch_policy": dict(self.branch_policy),
            "allowed_paths": list(self.allowed_paths),
            "forbidden_path_policy_identity": self.forbidden_path_policy_identity,
            "task_classes": list(self.task_classes),
            "risk_lanes": list(self.risk_lanes),
            "finite_backlog_reference": self.finite_backlog_reference,
            "finite_backlog_digest": self.finite_backlog_digest,
            "max_work_items": self.max_work_items,
            "max_concurrency": self.max_concurrency,
            "max_attempts": self.max_attempts,
            "max_repairs": self.max_repairs,
            "compute_api_budget": dict(self.compute_api_budget),
            "wall_clock_budget_seconds": self.wall_clock_budget_seconds,
            "validation_requirements": list(self.validation_requirements),
            "audit_requirements": list(self.audit_requirements),
            "local_commit_permission": self.local_commit_permission.value,
            "publication_permission": self.publication_permission.value,
            "cross_repo_permission": self.cross_repo_permission.value,
            "maintenance_permission": self.maintenance_permission.value,
            "cleanup_requirements": list(self.cleanup_requirements),
            "reporting_cadence": self.reporting_cadence,
            "retention_policy": self.retention_policy,
            "global_stop_reference": self.global_stop_reference,
            "canonical_digest_metadata": metadata,
            "authorization_mechanism": dict(self.authorization_mechanism),
        }

    def canonical_identity_payload(self) -> dict[str, Any]:
        return self.to_dict(include_digest=False)

    def canonical_digest(self) -> str:
        return canonical_sha256(self.canonical_identity_payload())

    def with_digest(self) -> "StandingLease":
        metadata = dict(self.canonical_digest_metadata)
        metadata.setdefault("algorithm", "sha256")
        metadata.setdefault("canonicalization", CANONICALIZATION_ID)
        base = replace(self, canonical_digest_metadata=metadata)
        metadata["digest"] = base.canonical_digest()
        return replace(self, canonical_digest_metadata=MappingProxyType(metadata))

    def validate_identity(self) -> LeaseIdentityValidation:
        issues: list[ValidationIssue] = []
        digest: str | None = None
        try:
            if self.schema_id != LEASE_SCHEMA_ID:
                issues.append(_lease_issue("schema_id_mismatch", "schema_id"))
            if self.schema_version != LEASE_SCHEMA_VERSION:
                issues.append(_lease_issue("schema_version_mismatch", "schema_version"))
            _validate_time_window(self.issued_at, self.valid_from, self.expires_at, issues)
            if self.max_concurrency > self.max_work_items:
                issues.append(_lease_issue("max_concurrency_exceeds_max_work_items", "max_concurrency"))
            if self.max_attempts < 1:
                issues.append(_lease_issue("max_attempts_malformed", "max_attempts"))
            if self.max_repairs < 0:
                issues.append(_lease_issue("max_repairs_malformed", "max_repairs"))
            if not self.finite_backlog_reference or not self.finite_backlog_digest:
                issues.append(_lease_issue("finite_backlog_binding_malformed", "finite_backlog_reference"))
            if self.revocation_state is LeaseRevocationState.REVOKED and not self.revocation_reference:
                issues.append(_lease_issue("revoked_without_reference", "revocation_reference"))
            if self.revocation_state is LeaseRevocationState.NOT_REVOKED and self.revocation_reference:
                issues.append(_lease_issue("non_revoked_with_reference", "revocation_reference"))
            metadata = dict(self.canonical_digest_metadata)
            if metadata.get("algorithm") != "sha256":
                issues.append(_lease_issue("digest_algorithm_mismatch", "canonical_digest_metadata.algorithm"))
            if metadata.get("canonicalization") != CANONICALIZATION_ID:
                issues.append(_lease_issue("canonicalization_mismatch", "canonical_digest_metadata.canonicalization"))
            expected = metadata.get("digest")
            digest = self.canonical_digest()
            if not isinstance(expected, str) or expected != digest:
                issues.append(_lease_issue("digest_mismatch", "canonical_digest_metadata.digest"))
        except ValueError as exc:
            issues.append(safe_issue_from_exception(exc))
        return LeaseIdentityValidation(
            identity_valid=not issues,
            digest=digest,
            issues=tuple(issues),
            decision_ref=f"lease-identity-{self.lease_id}",
            lease_ref=self.lease_id,
        )


def require_digest(value: Any, field_name: str) -> str:
    digest = require_string(value, field_name)
    if len(digest) != SHA256_HEX_LENGTH or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")
    return digest


def validate_standing_lease(payload: Mapping[str, Any] | str) -> LeaseIdentityValidation:
    try:
        lease = StandingLease.from_json(payload) if isinstance(payload, str) else StandingLease.from_dict(payload)
        return lease.validate_identity()
    except (ValueError, TypeError) as exc:
        return LeaseIdentityValidation(
            identity_valid=False,
            digest=None,
            issues=(safe_issue_from_exception(exc),),
            decision_ref="lease-identity-invalid",
            lease_ref="lease-unknown",
        )


def derive_lease_runtime_decision(
    lease: StandingLease,
    transaction_time: datetime | str,
) -> LeaseRuntimeDecision:
    """Derive runtime lease status from canonical lease content and transaction time."""

    if not isinstance(lease, StandingLease):
        raise ValueError("invalid_field_type:lease_runtime.lease")
    evaluated_at = require_utc_timestamp(transaction_time, "lease_runtime.evaluated_at")
    evaluated = _parse_strict_utc_timestamp(evaluated_at, "lease_runtime.evaluated_at")
    valid_from = _parse_timestamp(lease.valid_from, "lease.valid_from")
    expires_at = _parse_timestamp(lease.expires_at, "lease.expires_at")

    if lease.revocation_state is LeaseRevocationState.REVOKED:
        status = LeaseRuntimeStatus.REVOKED
    elif lease.revocation_state is LeaseRevocationState.UNKNOWN:
        status = LeaseRuntimeStatus.REVOCATION_UNKNOWN
    elif evaluated < valid_from:
        status = LeaseRuntimeStatus.NOT_YET_VALID
    elif evaluated >= expires_at:
        status = LeaseRuntimeStatus.EXPIRED
    else:
        status = LeaseRuntimeStatus.ACTIVE

    reason = {
        LeaseRuntimeStatus.ACTIVE: "lease_runtime_active",
        LeaseRuntimeStatus.NOT_YET_VALID: "lease_not_yet_valid",
        LeaseRuntimeStatus.EXPIRED: "lease_expired",
        LeaseRuntimeStatus.REVOKED: "lease_revoked",
        LeaseRuntimeStatus.REVOCATION_UNKNOWN: "lease_revocation_unknown",
    }[status]
    return LeaseRuntimeDecision(
        lease_ref=lease.lease_id,
        evaluated_at=evaluated_at,
        status=status,
        reason=reason,
    )


def require_utc_timestamp(value: Any, field_name: str) -> str:
    parsed = _parse_strict_utc_timestamp(value, field_name)
    return parsed.isoformat().replace("+00:00", "Z")


def _require_revocation_state(value: Any) -> LeaseRevocationState:
    raw = require_string(value, "revocation_state")
    if raw not in {state.value for state in LeaseRevocationState}:
        raise ValueError("invalid_field_type:revocation_state")
    return LeaseRevocationState(raw)


def _require_permission(value: Any, field_name: str) -> Permission:
    raw = require_string(value, field_name)
    if raw not in {permission.value for permission in Permission}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return Permission(raw)


def _require_authorization_model(value: Any, field_name: str) -> AuthorizationModel:
    if isinstance(value, AuthorizationModel):
        return value
    raw = require_string(value, field_name)
    if raw not in {model.value for model in AuthorizationModel}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return AuthorizationModel(raw)


def _require_lease_runtime_status(value: Any, field_name: str) -> LeaseRuntimeStatus:
    if isinstance(value, LeaseRuntimeStatus):
        return value
    raw = require_string(value, field_name)
    if raw not in {status.value for status in LeaseRuntimeStatus}:
        raise ValueError(f"invalid_field_type:{field_name}")
    return LeaseRuntimeStatus(raw)


def require_contract_issue(value: Any, field_name: str) -> ValidationIssue:
    if not isinstance(value, ValidationIssue):
        raise ValueError(f"invalid_field_type:{field_name}")
    return value


def _require_repo_identity(value: Any) -> Mapping[str, Any]:
    raw = require_exact_keys(value, "repo_identity", REPO_IDENTITY_KEYS)
    return MappingProxyType(
        {
            "component": require_safe_ref(raw.get("component"), "repo_identity.component"),
            "repo_label": require_safe_ref(raw.get("repo_label"), "repo_identity.repo_label"),
        }
    )


def _require_branch_policy(value: Any) -> Mapping[str, Any]:
    raw = require_exact_keys(value, "branch_policy", BRANCH_POLICY_KEYS)
    return MappingProxyType(
        {
            "base": require_safe_string(raw.get("base"), "branch_policy.base"),
            "mode": require_safe_ref(raw.get("mode"), "branch_policy.mode"),
        }
    )


def _require_compute_api_budget(value: Any) -> Mapping[str, Any]:
    raw = require_exact_keys(value, "compute_api_budget", COMPUTE_API_BUDGET_KEYS)
    return MappingProxyType(
        {
            "api_calls": require_non_negative_int(raw.get("api_calls"), "compute_api_budget.api_calls"),
            "compute_seconds": require_non_negative_int(
                raw.get("compute_seconds"),
                "compute_api_budget.compute_seconds",
            ),
        }
    )


def _require_digest_metadata(value: Any, *, require_digest_value: bool) -> Mapping[str, Any]:
    optional = () if require_digest_value else ("digest",)
    raw = require_exact_keys(
        value,
        "canonical_digest_metadata",
        CANONICAL_DIGEST_METADATA_KEYS,
        optional_keys=optional,
    )
    result: dict[str, Any] = {
        "algorithm": require_safe_ref(raw.get("algorithm"), "canonical_digest_metadata.algorithm"),
        "canonicalization": require_safe_ref(
            raw.get("canonicalization"),
            "canonical_digest_metadata.canonicalization",
        ),
    }
    if "digest" in raw:
        result["digest"] = require_digest(raw.get("digest"), "canonical_digest_metadata.digest")
    return MappingProxyType(result)


def _require_authorization_mechanism(value: Any) -> Mapping[str, Any]:
    raw = require_exact_keys(value, "authorization_mechanism", AUTHORIZATION_MECHANISM_KEYS)
    kind = require_safe_ref(raw.get("kind"), "authorization_mechanism.kind")
    if kind != "unsupported":
        raise ValueError("invalid_field_type:authorization_mechanism.kind")
    return MappingProxyType(
        {
            "kind": kind,
            "descriptor": require_safe_ref(raw.get("descriptor"), "authorization_mechanism.descriptor"),
        }
    )


def _parse_strict_utc_timestamp(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() != timedelta(0) or value.microsecond != 0:
            raise ValueError(f"invalid_field_type:{field_name}")
        return value.astimezone(timezone.utc).replace(microsecond=0)
    text = require_safe_string(value, field_name, max_length=64)
    parsed = _parse_timezone_aware_timestamp(text, field_name)
    if parsed.utcoffset() != timedelta(0) or parsed.microsecond != 0:
        raise ValueError(f"invalid_field_type:{field_name}")
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _parse_timestamp(value: str, field_name: str) -> datetime:
    return _parse_timezone_aware_timestamp(value, field_name).astimezone(timezone.utc)


def _parse_timezone_aware_timestamp(value: Any, field_name: str) -> datetime:
    text = require_safe_string(value, field_name, max_length=64)
    raw = f"{text[:-1]}+00:00" if text.endswith("Z") else text
    parsed = _try_parse_iso_timestamp(raw)
    if parsed is None:
        raise ValueError(f"invalid_field_type:{field_name}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"invalid_field_type:{field_name}")
    return parsed


def _try_parse_iso_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _lease_issue(reason: str, field: str) -> ValidationIssue:
    return ValidationIssue(field=field, reason=reason)


def _validate_time_window(
    issued_at: str,
    valid_from: str,
    expires_at: str,
    issues: list[ValidationIssue],
) -> None:
    try:
        issued = _parse_timestamp(issued_at, "issued_at")
        valid = _parse_timestamp(valid_from, "valid_from")
        expires = _parse_timestamp(expires_at, "expires_at")
    except ValueError as exc:
        issues.append(safe_issue_from_exception(exc))
        return
    if valid < issued:
        issues.append(_lease_issue("valid_from_before_issued_at", "valid_from"))
    if expires <= valid:
        issues.append(_lease_issue("expires_at_not_after_valid_from", "expires_at"))
