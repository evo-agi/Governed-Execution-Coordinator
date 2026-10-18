from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import inspect
import json
from pathlib import Path

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256
from ge_nwp_coordinator.global_stop import GlobalStopReasonClass, GlobalStopState
from ge_nwp_coordinator.lease import (
    AUTHORIZATION_DECISION_SCHEMA_ID,
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    AuthorizationModel,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
    LeaseRevocationState,
    Permission,
    StandingLease,
    UnsupportedAuthorizationProvider,
    derive_lease_runtime_decision,
)
from ge_nwp_coordinator.persistence_contracts import (
    B3AuthorizationModelHandling,
    AuthorizationReceiptContract,
    DependencyReceiptContract,
    FIRST_TRANSITION_EVENT_SEQUENCE,
    LeaseIdentityRecordContract,
    classify_authorization_model_for_b3,
    encode_sqlite_boolean,
    next_transition_event_sequence,
    normalize_transaction_timestamp,
    work_item_record_from_row,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.sqlite_writer_session import _SQLiteWriterSession
from ge_nwp_coordinator.state_machine import (
    DEPENDENCY_DECISION_SCHEMA_ID,
    TRANSITION_EVENT_SCHEMA_ID,
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvent,
    TransitionEvaluationKind,
    WorkItemRecord,
    WorkItemState,
    transition,
)
from ge_nwp_coordinator.state_store import WriterSession


def _contains_requests_client_usage(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == "requests" or alias.name.startswith("requests.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.module == "requests"
            or (node.module or "").startswith("requests.")
        ):
            return True
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "requests"
        ):
            return True
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        if node.args[0].value != "requests":
            continue
        if isinstance(function, ast.Name) and function.id == "__import__":
            return True
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
            and function.attr == "import_module"
        ):
            return True
    return False


def _assert_no_requests_client_usage(paths: tuple[Path, ...]) -> None:
    accepted = (
        "class Example:\n    max_pull_requests = 1\n"
        "payload = {'max_pull_requests': 1}\n"
        "def max_pull_requests() -> int:\n    return 1\n"
    )
    rejected = (
        "import requests\n",
        "import requests as rq\nrq.get(...)\n",
        "from requests import get\nget(...)\n",
        "from requests import get as http_get\nhttp_get(...)\n",
        "requests.get(...)\n",
        "__import__('requests')\n",
        "importlib.import_module('requests')\n",
    )
    assert not _contains_requests_client_usage(accepted)
    assert all(_contains_requests_client_usage(source) for source in rejected)
    assert not any(
        _contains_requests_client_usage(path.read_text(encoding="utf-8"))
        for path in paths
    )


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"


def _lease(**overrides: object) -> StandingLease:
    fields = {
        "schema_id": LEASE_SCHEMA_ID,
        "schema_version": 1,
        "lease_id": "lease-a2-p1",
        "issuer_label": "operator-policy",
        "issued_at": "2026-07-14T00:00:00Z",
        "valid_from": "2026-07-14T00:00:01Z",
        "expires_at": "2026-07-15T00:00:00Z",
        "revocation_state": LeaseRevocationState.NOT_REVOKED,
        "revocation_reference": None,
        "subject": "nwp-coordinator-p1",
        "repo_identity": {"component": "nwp-coordinator", "repo_label": "coordinator-local"},
        "branch_policy": {"base": "trunk_dev", "mode": "operator-approved"},
        "allowed_paths": ("tests", "src"),
        "forbidden_path_policy_identity": "governed-execution.nwp-forbidden-paths.v1",
        "task_classes": ("docs", "code"),
        "risk_lanes": ("low",),
        "finite_backlog_reference": "backlog-a2-p1",
        "finite_backlog_digest": "a" * 64,
        "max_work_items": 2,
        "max_concurrency": 1,
        "max_attempts": 1,
        "max_repairs": 0,
        "compute_api_budget": {"api_calls": 0, "compute_seconds": 0},
        "wall_clock_budget_seconds": 3600,
        "validation_requirements": ("unit-tests",),
        "audit_requirements": ("boundary-audit",),
        "local_commit_permission": Permission.FORBIDDEN,
        "publication_permission": Permission.FORBIDDEN,
        "cross_repo_permission": Permission.FORBIDDEN,
        "maintenance_permission": Permission.FORBIDDEN,
        "cleanup_requirements": ("no-worker-artifacts",),
        "reporting_cadence": "on-transition",
        "retention_policy": "safe-projections-only",
        "global_stop_reference": "operator-global-stop",
        "canonical_digest_metadata": {"algorithm": "sha256", "canonicalization": CANONICALIZATION_ID},
        "authorization_mechanism": {"kind": "unsupported", "descriptor": "p1-fail-closed"},
    }
    fields.update(overrides)
    return StandingLease(**fields).with_digest()


def _test_only_authorized_operator_policy_context() -> TransitionContext:
    """Pure evaluator fixture only; not a persisted reader or provider."""
    lease = _lease()
    identity = lease.validate_identity()
    return TransitionContext(
        lease_identity=identity,
        authorization=AuthorizationDecision(
            decision_ref="authz-lease-a2-p1",
            lease_ref=identity.lease_ref,
            lease_identity_decision_ref=identity.decision_ref,
            lease_identity_valid=identity.identity_valid,
            authorization_model=AuthorizationModel.OPERATOR_POLICY,
            authorized=True,
            executable=False,
            reason="accepted",
        ),
        lease_runtime=derive_lease_runtime_decision(lease, "2026-07-14T00:00:02Z"),
        dependency_decision=DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1"),
    )


def _record(state: WorkItemState = WorkItemState.PROPOSED, version: int = 0) -> WorkItemRecord:
    return WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-a2-p1",
        backlog_id="backlog-a2-p1",
        state=state,
        version=version,
        budget_limit=10,
    )


def _command(target: WorkItemState, record: WorkItemRecord, context: TransitionContext) -> TransitionCommand:
    return TransitionCommand.create(
        work_item_id=record.work_item_id,
        idempotency_key="transition-k1",
        expected_version=record.version,
        target_state=target,
        lease_identity_decision_ref=context.lease_identity.decision_ref,
        authorization_decision_ref=context.authorization.decision_ref,
        global_stop_ref=context.global_stop.stop_ref,
        global_stop_version=context.global_stop.version,
        dependency_decision_ref=context.dependency_decision.decision_ref if target is WorkItemState.READY else None,
    )


def _lease_identity_row(lease: StandingLease | None = None) -> dict[str, object]:
    lease = lease or _lease()
    validation = lease.validate_identity()
    return {
        "decision_ref": validation.decision_ref,
        "lease_ref": validation.lease_ref,
        "identity_valid": encode_sqlite_boolean(validation.identity_valid, "lease_identity_record.identity_valid"),
        "lease_digest": validation.digest,
        "schema_id": LEASE_SCHEMA_ID,
        "canonical_json": canonical_json_bytes(lease.to_dict()).decode("utf-8"),
        "canonical_digest": canonical_sha256(lease.to_dict()),
    }


def _authorization_row(decision: AuthorizationDecision | None = None) -> dict[str, object]:
    decision = decision or UnsupportedAuthorizationProvider().authorize(_lease())
    return {
        "decision_ref": decision.decision_ref,
        "lease_ref": decision.lease_ref,
        "lease_identity_decision_ref": decision.lease_identity_decision_ref,
        "lease_identity_valid": encode_sqlite_boolean(
            decision.lease_identity_valid,
            "authorization_receipt.lease_identity_valid",
        ),
        "authorization_model": decision.authorization_model.value,
        "authorized": encode_sqlite_boolean(decision.authorized, "authorization_receipt.authorized"),
        "executable": encode_sqlite_boolean(decision.executable, "authorization_receipt.executable"),
        "reason": decision.reason,
        "schema_id": AUTHORIZATION_DECISION_SCHEMA_ID,
        "canonical_json": decision.canonical_json(),
        "canonical_digest": decision.canonical_digest(),
    }


def _dependency_row(decision: DependencyDecision | None = None) -> dict[str, object]:
    decision = decision or DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    return {
        "decision_ref": decision.decision_ref,
        "work_item_id": decision.work_item_id,
        "dependencies_satisfied": encode_sqlite_boolean(
            decision.dependencies_satisfied,
            "dependency_receipt.dependencies_satisfied",
        ),
        "reason": decision.reason,
        "schema_id": DEPENDENCY_DECISION_SCHEMA_ID,
        "canonical_json": decision.canonical_json(),
        "canonical_digest": decision.canonical_digest(),
    }


def _work_item_row(record: WorkItemRecord | None = None) -> dict[str, object]:
    record = record or _record(version=3)
    row = {**record.to_dict(), "updated_at": "2026-07-14T00:00:00Z"}
    row["state"] = record.state.value
    row["cleanup_required"] = encode_sqlite_boolean(record.cleanup_required, "work_item_row.cleanup_required")
    return row


def _rekey_transition_event_payload(payload: dict[str, object]) -> dict[str, object]:
    payload = deepcopy(payload)
    ref_payload = dict(payload)
    ref_payload.pop("event_ref")
    payload["event_ref"] = f"transition-event-{canonical_sha256(ref_payload)[:24]}"
    return payload


SQLITE_BOOLEAN_ROW_CASES = (
    ("lease_identity_record", _lease_identity_row, "identity_valid", LeaseIdentityRecordContract.from_dict),
    ("authorization_receipt", _authorization_row, "lease_identity_valid", AuthorizationReceiptContract.from_dict),
    ("authorization_receipt", _authorization_row, "authorized", AuthorizationReceiptContract.from_dict),
    ("authorization_receipt", _authorization_row, "executable", AuthorizationReceiptContract.from_dict),
    ("dependency_receipt", _dependency_row, "dependencies_satisfied", DependencyReceiptContract.from_dict),
    ("work_item_row", _work_item_row, "cleanup_required", work_item_record_from_row),
)


def test_writer_session_transition_signature_is_command_only_and_context_is_internal() -> None:
    assert list(inspect.signature(WriterSession.apply_transition).parameters) == ["self", "transition_command"]
    assert list(inspect.signature(_SQLiteWriterSession.apply_transition).parameters) == ["self", "transition_command"]
    assert "typed_context" not in inspect.getsource(WriterSession.apply_transition)
    assert "LeaseRuntimeDecision" in ge_nwp_coordinator.__all__
    assert "acquire_sqlite_writer_session" not in ge_nwp_coordinator.__all__
    assert "encode_sqlite_boolean" not in ge_nwp_coordinator.__all__


@pytest.mark.parametrize(
    ("transaction_time", "expected_status", "expected_reason"),
    (
        ("2026-07-14T00:00:02Z", LeaseRuntimeStatus.ACTIVE, "lease_runtime_active"),
        ("2026-07-14T00:00:02+00:00", LeaseRuntimeStatus.ACTIVE, "lease_runtime_active"),
        ("2026-07-14T00:00:00Z", LeaseRuntimeStatus.NOT_YET_VALID, "lease_not_yet_valid"),
        ("2026-07-15T00:00:00Z", LeaseRuntimeStatus.EXPIRED, "lease_expired"),
        (datetime(2026, 7, 14, 0, 0, 2, tzinfo=timezone.utc), LeaseRuntimeStatus.ACTIVE, "lease_runtime_active"),
    ),
)
def test_lease_runtime_decision_derives_status_from_utc_time(
    transaction_time: object,
    expected_status: LeaseRuntimeStatus,
    expected_reason: str,
) -> None:
    decision = derive_lease_runtime_decision(_lease(), transaction_time)  # type: ignore[arg-type]
    assert decision.status is expected_status
    assert decision.reason == expected_reason
    assert LeaseRuntimeDecision.from_json(decision.canonical_json()) == decision


def test_lease_runtime_revocation_precedence_and_utc_rejection() -> None:
    revoked = _lease(revocation_state=LeaseRevocationState.REVOKED, revocation_reference="operator-revocation-1")
    unknown = _lease(revocation_state=LeaseRevocationState.UNKNOWN)
    assert derive_lease_runtime_decision(revoked, "2026-07-13T00:00:00Z").status is LeaseRuntimeStatus.REVOKED
    assert derive_lease_runtime_decision(unknown, "2026-07-16T00:00:00Z").status is LeaseRuntimeStatus.REVOCATION_UNKNOWN
    with pytest.raises(ValueError):
        derive_lease_runtime_decision(_lease(), "2026-07-13T20:00:02-04:00")
    with pytest.raises(ValueError):
        normalize_transaction_timestamp(datetime(2026, 7, 14, 0, 0, 2))


def test_lease_identity_and_runtime_share_explicit_offset_timestamp_parsing() -> None:
    lease = _lease(
        issued_at="2026-07-14T00:00:00+00:00",
        valid_from="2026-07-13T20:00:01-04:00",
        expires_at="2026-07-14T20:00:00-04:00",
    )
    validation = lease.validate_identity()
    assert validation.identity_valid
    runtime = derive_lease_runtime_decision(lease, "2026-07-14T00:00:02Z")
    assert runtime.status is LeaseRuntimeStatus.ACTIVE
    assert runtime.evaluated_at == "2026-07-14T00:00:02Z"
    assert lease.to_dict()["valid_from"] == "2026-07-13T20:00:01-04:00"


@pytest.mark.parametrize("timestamp", ("2026-07-14T00:00:01", "not-a-timestamp"))
def test_lease_identity_and_runtime_reject_naive_or_malformed_lease_timestamps(timestamp: str) -> None:
    lease = _lease(valid_from=timestamp)
    assert not lease.validate_identity().identity_valid
    with pytest.raises(ValueError):
        derive_lease_runtime_decision(lease, "2026-07-14T00:00:02Z")


def test_transition_context_has_runtime_decision_not_raw_booleans() -> None:
    names = {field.name for field in fields(TransitionContext)}
    assert "lease_runtime" in names
    assert "lease_expired" not in names
    assert "lease_revoked" not in names


def test_runtime_status_drives_domain_rejection_without_caller_booleans() -> None:
    context = _test_only_authorized_operator_policy_context()
    record = _record()
    not_yet_context = TransitionContext(
        lease_identity=context.lease_identity,
        authorization=context.authorization,
        lease_runtime=LeaseRuntimeDecision(
            lease_ref=record.lease_id,
            evaluated_at="2026-07-13T00:00:00Z",
            status=LeaseRuntimeStatus.NOT_YET_VALID,
            reason="lease_not_yet_valid",
        ),
        dependency_decision=context.dependency_decision,
    )
    result = transition(record, _command(WorkItemState.LEASE_ADMITTED, record, not_yet_context), not_yet_context)
    assert result.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    assert result.reason == "lease_not_yet_valid"


def test_authorization_decision_schema_alignment_and_current_b3_handling() -> None:
    lease = _lease()
    unsupported = UnsupportedAuthorizationProvider().authorize(lease)
    assert unsupported.lease_identity_decision_ref == lease.validate_identity().decision_ref
    assert AuthorizationDecision.from_json(unsupported.canonical_json()) == unsupported
    assert unsupported.canonical_digest() == canonical_sha256(unsupported.to_dict())
    assert classify_authorization_model_for_b3(unsupported) is B3AuthorizationModelHandling.FAIL_CLOSED_UNSUPPORTED

    operator_policy = AuthorizationDecision(
        decision_ref="authz-operator-policy",
        lease_ref=lease.lease_id,
        lease_identity_decision_ref=lease.validate_identity().decision_ref,
        lease_identity_valid=True,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=True,
        executable=True,
        reason="accepted",
    )
    assert classify_authorization_model_for_b3(operator_policy) is B3AuthorizationModelHandling.UNSUPPORTED_AUTHORITATIVE_MODEL
    payload = operator_policy.to_dict()
    payload.pop("lease_identity_decision_ref")
    with pytest.raises(ValueError):
        AuthorizationDecision.from_dict(payload)


def test_authorization_decision_rejects_incoherent_authority_states() -> None:
    lease = _lease()
    identity = lease.validate_identity()
    base = {
        "decision_ref": "authz-operator-policy",
        "lease_ref": lease.lease_id,
        "lease_identity_decision_ref": identity.decision_ref,
        "lease_identity_valid": True,
        "authorization_model": AuthorizationModel.OPERATOR_POLICY,
        "authorized": False,
        "executable": False,
        "reason": "lease_not_authorized",
    }
    invalid_cases = (
        {"authorized": False, "executable": True, "reason": "lease_not_authorized"},
        {"authorized": False, "executable": False, "reason": "accepted"},
        {"authorized": True, "executable": False, "reason": "lease_not_authorized"},
        {"lease_identity_valid": False, "authorized": True, "executable": False, "reason": "accepted"},
        {"lease_identity_valid": False, "authorized": False, "executable": True, "reason": "lease_not_authorized"},
        {
            "authorization_model": AuthorizationModel.UNSUPPORTED,
            "authorized": False,
            "executable": False,
            "reason": "accepted",
        },
    )
    for overrides in invalid_cases:
        with pytest.raises(ValueError):
            AuthorizationDecision(**{**base, **overrides})


def test_authorization_decision_preserves_coherent_operator_policy_vocab_without_trust() -> None:
    lease = _lease()
    identity = lease.validate_identity()
    denied = AuthorizationDecision(
        decision_ref="authz-operator-policy-denied",
        lease_ref=lease.lease_id,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=True,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=False,
        executable=False,
        reason="lease_not_authorized",
    )
    accepted = AuthorizationDecision(
        decision_ref="authz-operator-policy-accepted",
        lease_ref=lease.lease_id,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=True,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=True,
        executable=True,
        reason="accepted",
    )
    assert AuthorizationDecision.from_json(denied.canonical_json()) == denied
    assert AuthorizationDecision.from_json(accepted.canonical_json()) == accepted
    assert denied.canonical_digest() != accepted.canonical_digest()
    assert classify_authorization_model_for_b3(accepted) is B3AuthorizationModelHandling.UNSUPPORTED_AUTHORITATIVE_MODEL
    assert "executable=False" in inspect.getsource(UnsupportedAuthorizationProvider.authorize)


def test_dependency_decision_schema_alignment_and_nullable_work_item_binding() -> None:
    bound = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    assert DependencyDecision.from_json(bound.canonical_json()) == bound
    assert bound.canonical_digest() == canonical_sha256(bound.to_dict())
    unbound = DependencyDecision(decision_ref="deps-general", work_item_id=None)
    assert unbound.to_dict()["work_item_id"] is None
    with pytest.raises(ValueError):
        DependencyDecision.from_dict({**bound.to_dict(), "extra": "not-allowed"})


def test_transition_event_provenance_and_canonical_mapping() -> None:
    context = _test_only_authorized_operator_policy_context()
    record = _record()
    result = transition(record, _command(WorkItemState.LEASE_ADMITTED, record, context), context)
    assert result.event is not None
    event = result.event
    assert event.lease_identity_decision_ref == context.lease_identity.decision_ref
    assert event.authorization_decision_ref == context.authorization.decision_ref
    assert event.global_stop_ref == context.global_stop.stop_ref
    assert event.global_stop_version == context.global_stop.version
    assert event.lease_runtime == context.lease_runtime
    assert event.to_dict()["lease_runtime"] == context.lease_runtime.to_dict()
    assert event.canonical_event_ref_payload()["lease_runtime"] == context.lease_runtime.to_dict()
    assert event.to_dict()["lease_runtime"]["evaluated_at"] == "2026-07-14T00:00:02Z"
    assert event.event_ref == f"transition-event-{canonical_sha256(event.canonical_event_ref_payload())[:24]}"
    assert TransitionEvent.from_json(event.canonical_json()) == event
    assert event.canonical_digest() == canonical_sha256(event.to_dict())
    assert "event_sequence" not in event.to_dict()
    assert "created_at" not in event.to_dict()
    with pytest.raises(ValueError):
        TransitionEvent.from_dict({**event.to_dict(), "created_at": "2026-07-14T00:00:00Z"})


def test_transition_event_runtime_provenance_changes_identity_and_digest() -> None:
    context = _test_only_authorized_operator_policy_context()
    record = _record()
    result = transition(record, _command(WorkItemState.LEASE_ADMITTED, record, context), context)
    assert result.event is not None
    event = result.event

    changed_status = deepcopy(event.to_dict())
    changed_status["lease_runtime"] = {
        **changed_status["lease_runtime"],
        "status": "expired",
        "reason": "lease_expired",
    }
    changed_status_event = TransitionEvent.from_dict(_rekey_transition_event_payload(changed_status))
    assert changed_status_event.event_ref != event.event_ref
    assert changed_status_event.canonical_digest() != event.canonical_digest()

    changed_time = deepcopy(event.to_dict())
    changed_time["lease_runtime"] = {
        **changed_time["lease_runtime"],
        "evaluated_at": "2026-07-14T00:00:03Z",
    }
    changed_time_event = TransitionEvent.from_dict(_rekey_transition_event_payload(changed_time))
    assert changed_time_event.event_ref != event.event_ref
    assert changed_time_event.canonical_digest() != event.canonical_digest()

    changed_reason = deepcopy(event.to_dict())
    changed_reason["lease_runtime"] = {
        **changed_reason["lease_runtime"],
        "reason": "lease_expired",
    }
    with pytest.raises(ValueError):
        TransitionEvent.from_dict(_rekey_transition_event_payload(changed_reason))

    changed_lease_ref = deepcopy(event.to_dict())
    changed_lease_ref["lease_runtime"] = {
        **changed_lease_ref["lease_runtime"],
        "lease_ref": "lease-other",
    }
    with pytest.raises(ValueError):
        TransitionEvent.from_dict(_rekey_transition_event_payload(changed_lease_ref))


def test_work_item_replay_mapping_excludes_updated_at_and_row_adapter_maps_it() -> None:
    record = _record(version=3)
    assert WorkItemRecord.from_json(record.canonical_json()) == record
    assert record.canonical_digest() == canonical_sha256(record.to_dict())
    assert "updated_at" not in record.to_dict()
    with pytest.raises(ValueError):
        WorkItemRecord.from_dict({**record.to_dict(), "updated_at": "2026-07-14T00:00:00Z"})

    row = {**record.to_dict(), "updated_at": "2026-07-14T00:00:00Z"}
    row["state"] = record.state.value
    row["cleanup_required"] = 0
    assert work_item_record_from_row(row) == record
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        work_item_record_from_row({**row, "cleanup_required": True})
    assert exc_info.value.error_class == "database_integrity_failure"


def test_lease_identity_authorization_and_dependency_receipt_contracts_verify_canonical_rows() -> None:
    lease = _lease()
    validation = lease.validate_identity()
    lease_row = _lease_identity_row(lease)
    assert LeaseIdentityRecordContract.from_dict(lease_row).reconstruct().validation == validation
    with pytest.raises(SQLiteMutationStoreError):
        LeaseIdentityRecordContract.from_dict({**lease_row, "lease_ref": "lease-other"}).reconstruct()

    auth = UnsupportedAuthorizationProvider().authorize(lease)
    auth_row = _authorization_row(auth)
    assert AuthorizationReceiptContract.from_dict(auth_row).reconstruct() == auth

    deps = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    deps_row = _dependency_row(deps)
    assert DependencyReceiptContract.from_dict(deps_row).reconstruct() == deps


@pytest.mark.parametrize(("case_name", "row_factory", "field_name", "adapter"), SQLITE_BOOLEAN_ROW_CASES)
@pytest.mark.parametrize("value", (0, 1))
def test_persisted_sqlite_boolean_fields_accept_only_exact_integers(
    case_name: str,
    row_factory: object,
    field_name: str,
    adapter: object,
    value: int,
) -> None:
    row = row_factory()  # type: ignore[operator]
    row[field_name] = value
    parsed = adapter(row)  # type: ignore[operator]
    assert parsed is not None
    assert case_name


@pytest.mark.parametrize(("case_name", "row_factory", "field_name", "adapter"), SQLITE_BOOLEAN_ROW_CASES)
@pytest.mark.parametrize("value", (False, True, 0.0, 1.0, Decimal("0"), Decimal("1"), "0", "1", None))
def test_persisted_sqlite_boolean_fields_reject_non_integer_values(
    case_name: str,
    row_factory: object,
    field_name: str,
    adapter: object,
    value: object,
) -> None:
    row = row_factory()  # type: ignore[operator]
    row[field_name] = value
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        adapter(row)  # type: ignore[operator]
    assert exc_info.value.error_class == "database_integrity_failure"
    assert str(exc_info.value) == "database_integrity_failure"
    assert repr(value) not in repr(exc_info.value)
    assert case_name


@pytest.mark.parametrize(("value", "expected"), ((False, 0), (True, 1)))
def test_sqlite_boolean_write_encoder_accepts_only_exact_python_bool(value: bool, expected: int) -> None:
    assert encode_sqlite_boolean(value, "future_boolean_field") == expected


@pytest.mark.parametrize("value", (0, 1, 0.0, 1.0, Decimal("0"), Decimal("1"), "0", "1", None, object()))
def test_sqlite_boolean_write_encoder_rejects_non_bool_without_echoing_value(value: object) -> None:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        encode_sqlite_boolean(value, "future_boolean_field")  # type: ignore[arg-type]
    assert exc_info.value.error_class == "database_integrity_failure"
    assert str(exc_info.value) == "database_integrity_failure"
    assert repr(value) not in repr(exc_info.value)


def test_positive_boolean_row_fixtures_use_encoder_and_corrupt_rows_bypass_it_only_in_tests() -> None:
    positive_fixture_source = "\n".join(
        inspect.getsource(factory) for factory in (_lease_identity_row, _authorization_row, _dependency_row, _work_item_row)
    )
    assert positive_fixture_source.count("encode_sqlite_boolean") == 6
    corrupt_test_source = inspect.getsource(test_persisted_sqlite_boolean_fields_reject_non_integer_values)
    assert "row[field_name] = value" in corrupt_test_source
    assert "encode_sqlite_boolean(value" not in corrupt_test_source


def test_persisted_canonical_json_columns_require_literal_canonical_text() -> None:
    lease = _lease()
    lease_row = _lease_identity_row(lease)
    noncanonical_lease_row = {
        **lease_row,
        "canonical_json": json.dumps(lease.to_dict(), indent=2, sort_keys=True),
    }
    with pytest.raises(SQLiteMutationStoreError):
        LeaseIdentityRecordContract.from_dict(noncanonical_lease_row).reconstruct()

    unknown_lease_row = {
        **lease_row,
        "canonical_json": canonical_json_bytes({**lease.to_dict(), "unknown": "field"}).decode("utf-8"),
    }
    with pytest.raises(SQLiteMutationStoreError):
        LeaseIdentityRecordContract.from_dict(unknown_lease_row).reconstruct()

    auth = UnsupportedAuthorizationProvider().authorize(lease)
    auth_row = _authorization_row(auth)
    noncanonical_auth_row = {
        **auth_row,
        "canonical_json": json.dumps(auth.to_dict(), indent=2, sort_keys=True),
    }
    with pytest.raises(SQLiteMutationStoreError):
        AuthorizationReceiptContract.from_dict(noncanonical_auth_row).reconstruct()

    duplicate_auth_row = {
        **auth_row,
        "canonical_json": auth.canonical_json().replace(
            '"reason":"unsupported_authorization_model"',
            '"reason":"unsupported_authorization_model","reason":"unsupported_authorization_model"',
            1,
        ),
    }
    with pytest.raises(SQLiteMutationStoreError):
        AuthorizationReceiptContract.from_dict(duplicate_auth_row).reconstruct()

    deps = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    deps_row = _dependency_row(deps)
    noncanonical_deps_row = {
        **deps_row,
        "canonical_json": json.dumps(deps.to_dict(), indent=2, sort_keys=True),
    }
    with pytest.raises(SQLiteMutationStoreError):
        DependencyReceiptContract.from_dict(noncanonical_deps_row).reconstruct()


def test_global_stop_current_state_has_closed_canonical_read_mapping() -> None:
    clear = GlobalStopState()
    assert GlobalStopState.from_json(clear.canonical_json()) == clear
    active = GlobalStopState(
        version=1,
        active=True,
        stop_id="stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        operator_decision_ref="operator-decision-1",
    )
    assert GlobalStopState.from_dict(active.to_dict()) == active
    with pytest.raises(ValueError):
        GlobalStopState.from_dict({**clear.to_dict(), "private_payload": "not-allowed"})


def test_event_sequence_timestamp_and_mutation_error_contracts_are_safe() -> None:
    assert FIRST_TRANSITION_EVENT_SEQUENCE == 0
    assert next_transition_event_sequence(None) == 0
    assert next_transition_event_sequence(0) == 1
    assert normalize_transaction_timestamp("2026-07-14T00:00:02Z") == "2026-07-14T00:00:02Z"
    assert normalize_transaction_timestamp("2026-07-14T00:00:02+00:00") == "2026-07-14T00:00:02Z"
    with pytest.raises(SQLiteMutationStoreError) as exhausted:
        next_transition_event_sequence(9223372036854775807)
    assert exhausted.value.error_class == "event_sequence_exhausted"

    for code in SQLiteMutationStoreErrorCode:
        error = SQLiteMutationStoreError(code, internal_detail={"private": "/tmp/private.db"})
        assert str(error) == code.value
        assert "/tmp" not in repr(error)
        assert "private.db" not in repr(error)


def test_b3a_static_boundary_has_no_runtime_sqlite_mutation_or_admission_surface() -> None:
    source_paths = tuple(
        path
        for path in (ROOT / "src/ge_nwp_coordinator").rglob("*.py")
        if path.name
        not in {
            "sqlite_transition_write_contracts.py",
            "sqlite_global_stop_write_contracts.py",
        }
    )
    _assert_no_requests_client_usage(source_paths)
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_paths
    )
    for forbidden in (
        "INSERT INTO transition_events",
        "INSERT INTO global_stop_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
        "lookup_idempotency",
        "class SQLiteStateStore",
        "CoordinatorService",
        "Scheduler",
        "QueueConsumer",
        "socket",
        "urllib",
        "seed_authorization",
        "seed_work_item",
    ):
        assert forbidden not in source
    assert "sqlite3" not in (ROOT / "src/ge_nwp_coordinator/persistence_contracts.py").read_text(encoding="utf-8")
    assert sorted(path.name for path in (ROOT / "src/ge_nwp_coordinator/sqlite_migrations").glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
        "0004_rw0_c1_durable_evidence.sql",
    ]
    migration_bytes = (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM


def test_b3a_contract_doc_pins_non_runtime_scope_and_future_reconstruction() -> None:
    doc = (ROOT / ".docs/b3-transition-persistence-contract.md").read_text(encoding="utf-8")
    adr = (ROOT / ".docs/sqlite-state-backend-adr.md").read_text(encoding="utf-8")
    normalized = " ".join(doc.split())
    normalized_adr = " ".join(adr.split())
    for phrase in (
        "B3a contract-only prerequisites",
        "does not implement SQLite transition mutation",
        "WriterSession.apply_transition` accepts only a `TransitionCommand",
        "Caller-supplied `TransitionContext` is not an authority input",
        "LeaseRuntimeDecision",
        "authorization_model=operator_policy` is schema vocabulary only",
        "complete nested `LeaseRuntimeDecision` mapping",
        "transition_events.created_at` must equal `TransitionEvent.lease_runtime.evaluated_at",
        "SQL `event_sequence` and SQL `created_at` are not independently part of event JSON",
        "P1 Disabled Stage Gate",
        "the pure evaluator returns a domain-rejected event with reason `stage_not_enabled` before lease runtime",
        "Changing the runtime decision changes event identity and digest",
        "exact Python `bool` values become exact SQLite integers `0` or `1`",
        "replay `WorkItemRecord` canonical mapping",
        "COALESCE(MAX(event_sequence), -1) + 1",
        "commit_outcome_unknown",
        "B3a adds no admission API",
        "temporary current-generation-2 database at terminal migration `0004_rw0_c1_durable_evidence`",
        "historical schema-0001 B3/B4 graph",
        "All nineteen C2B tables, all nine cognitive proposal-selection tables, and all twenty-three RW0-C1 tables remain empty",
        "Migration 0002 is the unchanged historical prefix introduced by C2B2",
        "neither B3 nor C2B2 implemented or acquired ownership of migration 0003",
        "neither add nor consume C2B2 runtime behavior",
        "current physical generation-2, terminal-0004 database",
        "B3 did not implement migration 0003 or 0004",
        "`.docs/b3-tests-only-coherent-fixtures.md`",
    ):
        assert phrase in normalized
    for phrase in (
        "validates external command shape before invoking writer apply",
        "WriterSession.apply_transition(command)` with no caller-supplied `TransitionContext",
        "Reconstruct `TransitionContext` exclusively from persisted receipts",
    ):
        assert phrase in normalized_adr
    assert "typed-context shape" not in adr
    assert "invokes the `StateStore` port" not in adr
    assert "temporary managed schema-0001 database" not in doc
    assert "No migration 0002 is required for these prerequisite contracts" not in doc

def _d1_subprocess_owners(sources: tuple[tuple[Path, str], ...]) -> set[str]:
    owners: set[str] = set()
    for path, source in sources:
        tree = ast.parse(source, filename=str(path))
        imported = any(
            (isinstance(node, ast.Import)
             and any(alias.name == "subprocess" for alias in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module == "subprocess")
            for node in ast.walk(tree)
        )
        called = any(
            isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Attribute)
                 and node.func.attr == "Popen"
                 and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "subprocess")
                or (isinstance(node.func, ast.Name) and node.func.id == "Popen")
            )
            for node in ast.walk(tree)
        )
        if imported or called or "subprocess" in source or "Popen" in source:
            owners.add(path.name)
    return owners


def test_d1_supervisor_is_the_only_production_subprocess_owner() -> None:
    package = ROOT / "src/ge_nwp_coordinator"
    sources = tuple(
        (path, path.read_text(encoding="utf-8"))
        for path in sorted(package.rglob("*.py"))
    )
    assert _d1_subprocess_owners(sources) == {"_rw0_d1_process_supervisor.py"}
    hostile = tuple(
        (path, source + ("\nimport subprocess\n" if path.name == "_rw0_d1_fake_planner.py" else ""))
        for path, source in sources
    )
    assert _d1_subprocess_owners(hostile) != {"_rw0_d1_process_supervisor.py"}
