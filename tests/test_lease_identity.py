from dataclasses import FrozenInstanceError
import json

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
from ge_nwp_coordinator.state_machine import (
    TransitionContext,
    TransitionRequest,
    WorkItemRecord,
    WorkItemState,
    transition,
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

    payload = _lease().to_dict()
    payload["max_work_items"] = True
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert validation.issues == ("max_work_items must be a non-negative integer",)


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


def test_closed_world_rejects_unknown_and_misspelled_lease_fields_before_digest() -> None:
    payload = _lease().to_dict()
    payload["unexpected_private_value"] = "RAW_VALUE_SHOULD_NOT_LEAK"
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert validation.digest is None
    assert validation.issues == ("unknown_field:lease.unexpected_private_value",)
    assert "RAW_VALUE" not in repr(validation.issues)

    payload = _lease().to_dict()
    payload["lease_identifier"] = payload.pop("lease_id")
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert validation.digest is None
    assert validation.issues == ("unknown_field:lease.lease_identifier",)


@pytest.mark.parametrize(
    ("field_path", "value"),
    (
        (("branch_policy", "target"), "trunk_dev"),
        (("compute_api_budget", "tokens"), 1),
        (("authorization_mechanism", "trust_root"), "not-selected"),
    ),
)
def test_closed_world_rejects_unknown_nested_lease_fields(field_path: tuple[str, str], value: object) -> None:
    payload = _lease().to_dict()
    payload[field_path[0]][field_path[1]] = value
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert validation.digest is None
    assert validation.issues == (f"unknown_field:{field_path[0]}.{field_path[1]}",)


@pytest.mark.parametrize("field_name", ("revocation_reason", "validation_requirement", "audit_requirement"))
def test_closed_world_rejects_unknown_flat_lease_structural_fields(field_name: str) -> None:
    payload = _lease().to_dict()
    payload[field_name] = "not-part-of-v1"
    validation = validate_standing_lease(payload)
    assert not validation.identity_valid
    assert validation.digest is None
    assert validation.issues == (f"unknown_field:lease.{field_name}",)


def test_duplicate_json_object_keys_are_rejected_for_lease_inputs() -> None:
    with pytest.raises(ValueError, match="duplicate_field:schema_id"):
        StandingLease.from_json('{"schema_id":"a","schema_id":"b"}')
    with pytest.raises(ValueError, match="duplicate_field:base"):
        StandingLease.from_json('{"branch_policy":{"base":"a","base":"b"}}')


def test_unknown_field_cannot_preserve_an_accepted_lease_identity() -> None:
    clean = _lease().to_dict()
    dirty = json.loads(json.dumps(clean))
    dirty["extra_authority"] = "operator-approved"
    assert validate_standing_lease(clean).identity_valid
    dirty_validation = validate_standing_lease(dirty)
    assert not dirty_validation.identity_valid
    assert dirty_validation.digest is None
    with pytest.raises(ValueError, match="unknown_field:lease.extra_authority"):
        StandingLease.from_dict(dirty)


def test_permissive_fields_do_not_authorize_or_enable_executability() -> None:
    payload = _lease().to_dict()
    payload["publication_permission"] = Permission.ALLOWED.value
    payload["cross_repo_permission"] = Permission.ALLOWED.value
    payload["maintenance_permission"] = Permission.ALLOWED.value
    payload["local_commit_permission"] = Permission.ALLOWED.value
    payload["max_repairs"] = 2
    payload["max_work_items"] = 3
    payload["max_concurrency"] = 2
    lease = StandingLease.from_dict(payload).with_digest()

    validation = lease.validate_identity()
    decision = UnsupportedAuthorizationProvider().authorize(lease)
    assert validation.identity_valid
    assert decision.authorized is False
    assert decision.executable is False
    assert decision.reason == "unsupported_authorization_model"

    context = TransitionContext(lease_identity_valid=True, authorized=True, executable=True)
    commit = transition(
        WorkItemRecord(
            work_item_id="wi-1",
            lease_id=lease.lease_id,
            backlog_id=lease.finite_backlog_reference,
            state=WorkItemState.AUDITING,
            version=1,
        ),
        TransitionRequest(
            WorkItemState.COMMIT_ELIGIBLE,
            1,
            "commit",
            evidence_refs=("safe-evidence",),
        ),
        context,
    )
    repair = transition(
        WorkItemRecord(
            work_item_id="wi-1",
            lease_id=lease.lease_id,
            backlog_id=lease.finite_backlog_reference,
            state=WorkItemState.FAILED,
            version=1,
            max_repairs=lease.max_repairs,
        ),
        TransitionRequest(
            WorkItemState.REPAIR_ADMITTED,
            1,
            "repair",
            evidence_refs=("safe-evidence",),
        ),
        context,
    )
    cycle = transition(
        WorkItemRecord(
            work_item_id="wi-1",
            lease_id=lease.lease_id,
            backlog_id=lease.finite_backlog_reference,
            state=WorkItemState.READY,
            version=1,
            max_attempts=lease.max_attempts,
        ),
        TransitionRequest(WorkItemState.CYCLE_STARTING, 1, "cycle"),
        context,
    )
    assert commit.reason == "stage_not_enabled"
    assert repair.reason == "stage_not_enabled"
    assert cycle.reason == "stage_not_enabled"


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
