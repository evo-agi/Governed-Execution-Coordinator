from dataclasses import FrozenInstanceError

import pytest

from ge_nwp_coordinator.lease import (
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    LeaseRevocationState,
    Permission,
    StandingLease,
    UnsupportedAuthorizationProvider,
    validate_standing_lease,
)


def _lease() -> StandingLease:
    return StandingLease(
        schema_id=LEASE_SCHEMA_ID,
        schema_version=1,
        lease_id="lease-a2-p1",
        issuer_label="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        valid_from="2026-07-14T00:00:01Z",
        expires_at="2026-07-15T00:00:00Z",
        revocation_state=LeaseRevocationState.NOT_REVOKED,
        revocation_reference=None,
        subject="nwp-coordinator-p1",
        repo_identity={"component": "nwp-coordinator", "repo_label": "coordinator-local"},
        branch_policy={"base": "trunk_dev", "mode": "operator-approved"},
        allowed_paths=("tests", "src"),
        forbidden_path_policy_identity="governed-execution.nwp-forbidden-paths.v1",
        task_classes=("docs", "code"),
        risk_lanes=("low",),
        finite_backlog_reference="backlog-a2-p1",
        finite_backlog_digest="a" * 64,
        max_work_items=2,
        max_concurrency=1,
        max_attempts=1,
        max_repairs=0,
        compute_api_budget={"api_calls": 0, "compute_seconds": 0},
        wall_clock_budget_seconds=3600,
        validation_requirements=("unit-tests",),
        audit_requirements=("boundary-audit",),
        local_commit_permission=Permission.FORBIDDEN,
        publication_permission=Permission.FORBIDDEN,
        cross_repo_permission=Permission.FORBIDDEN,
        maintenance_permission=Permission.FORBIDDEN,
        cleanup_requirements=("no-worker-artifacts",),
        reporting_cadence="on-transition",
        retention_policy="safe-projections-only",
        global_stop_reference="operator-global-stop",
        canonical_digest_metadata={"algorithm": "sha256", "canonicalization": CANONICALIZATION_ID},
        authorization_mechanism={"kind": "unsupported", "descriptor": "p1-fail-closed"},
    ).with_digest()


def test_deterministic_canonicalization_normalizes_set_like_fields() -> None:
    payload = _lease().to_dict()
    shuffled = dict(payload)
    shuffled["allowed_paths"] = ["src", "tests"]
    shuffled["task_classes"] = ["code", "docs"]
    reparsed = StandingLease.from_dict(shuffled)
    assert reparsed.validate_identity().identity_valid
    assert reparsed.canonical_digest() == _lease().canonical_digest()


def test_digest_mismatch_is_identity_invalid() -> None:
    payload = _lease().to_dict()
    payload["issuer_label"] = "different-issuer"
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert "digest_mismatch" in validation.issues


def test_schema_mismatch_is_rejected() -> None:
    payload = _lease().to_dict()
    payload["schema_id"] = "governed-execution.other.v1"
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid


def test_malformed_limits_are_rejected() -> None:
    payload = _lease().to_dict()
    payload["max_work_items"] = 0
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid


def test_expiry_and_revocation_shape_are_validated() -> None:
    payload = _lease().to_dict()
    payload["expires_at"] = "2026-07-14T00:00:01Z"
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert "expires_at_not_after_valid_from" in validation.issues

    payload = _lease().to_dict()
    payload["revocation_state"] = "revoked"
    payload = StandingLease.from_dict(payload).with_digest().to_dict()
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert "revoked_without_reference" in validation.issues


def test_digest_is_not_authorization_or_executability() -> None:
    lease = _lease()
    validation = lease.validate_identity()
    decision = UnsupportedAuthorizationProvider().authorize(lease)
    assert validation.identity_valid
    assert decision.identity_valid
    assert not decision.authorized
    assert not decision.executable
    assert decision.reason == "unsupported_authorization_model"


def test_no_duplicate_set_like_values_and_immutable_contracts() -> None:
    payload = _lease().to_dict()
    payload["allowed_paths"] = ["src", "src"]
    with pytest.raises(ValueError, match="duplicate"):
        StandingLease.from_dict(payload)

    lease = _lease()
    with pytest.raises(FrozenInstanceError):
        lease.lease_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        lease.repo_identity["component"] = "other"  # type: ignore[index]


def test_no_production_authorization_bypass_tokens() -> None:
    text = open("src/ge_nwp_coordinator/lease.py", encoding="utf-8").read()
    forbidden = ("allow_all", "trusted local", "TRUSTED_LOCAL", "os.environ", "unsigned_fixture")
    for token in forbidden:
        assert token not in text
