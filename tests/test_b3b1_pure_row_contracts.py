from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import inspect
import json
from pathlib import Path
import traceback

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, FiniteBacklog, WorkItem
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256
from ge_nwp_coordinator.global_stop import GLOBAL_STOP_SCHEMA_ID, GlobalStopReasonClass, GlobalStopState
from ge_nwp_coordinator.lease import (
    AUTHORIZATION_DECISION_SCHEMA_ID,
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    AuthorizationModel,
    LeaseRevocationState,
    Permission,
    StandingLease,
    UnsupportedAuthorizationProvider,
)
from ge_nwp_coordinator.persistence_contracts import (
    AdmittedBacklogRecordContract,
    AdmittedBacklogRecordEnvelope,
    AuthorizationReceiptEnvelope,
    B3AuthorizationModelHandling,
    DependencyReceiptEnvelope,
    GlobalStopCurrentRecordEnvelope,
    LeaseIdentityRecordEnvelope,
    WorkItemRecordEnvelope,
    admitted_backlog_record_envelope_from_row,
    authorization_receipt_envelope_from_row,
    classify_authorization_model_for_b3,
    dependency_receipt_envelope_from_row,
    encode_sqlite_boolean,
    global_stop_current_envelope_from_row,
    lease_identity_record_envelope_from_row,
    validate_b3_work_item_authority_binding,
    work_item_record_envelope_from_row,
    work_item_record_from_row,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.state_machine import (
    DEPENDENCY_DECISION_SCHEMA_ID,
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    WorkItemRecord,
    WorkItemState,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
PRIVATE_REF = "private-assignment-ref-wi-1"
PRIVATE_PATH = "src/private-area"
PRIVATE_TIMESTAMP = "PRIVATE-TIMESTAMP-DO-NOT-LEAK-271828"
CANONICAL_TIMESTAMP = "2026-07-14T00:00:03Z"


def _item(
    work_item_id: str = "wi-1",
    *,
    dependencies: tuple[str, ...] = (),
    api_calls: int = 1,
    compute_seconds: int = 10,
) -> WorkItem:
    return WorkItem(
        work_item_id=work_item_id,
        objective_label=f"{work_item_id} objective",
        opaque_private_assignment_ref=PRIVATE_REF if work_item_id == "wi-1" else f"assignment-{work_item_id}",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=(PRIVATE_PATH, "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": api_calls, "compute_seconds": compute_seconds},
        dependencies=dependencies,
        stop_conditions=("global-stop",),
    )


def _backlog(**overrides: object) -> FiniteBacklog:
    fields = {
        "schema_id": BACKLOG_SCHEMA_ID,
        "schema_version": 1,
        "backlog_id": "backlog-a2-p1",
        "lease_reference": "lease-a2-p1",
        "work_items": (_item(), _item("wi-2", dependencies=("wi-1",), api_calls=2, compute_seconds=20)),
        "content_digest": "0" * 64,
    }
    fields.update(overrides)
    return FiniteBacklog(**fields).with_digest()


def _lease(backlog: FiniteBacklog | None = None, **overrides: object) -> StandingLease:
    backlog = backlog or _backlog()
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
        "allowed_paths": (PRIVATE_PATH, "tests"),
        "forbidden_path_policy_identity": "governed-execution.nwp-forbidden-paths.v1",
        "task_classes": ("docs", "code"),
        "risk_lanes": ("low",),
        "finite_backlog_reference": backlog.backlog_id,
        "finite_backlog_digest": backlog.content_digest,
        "max_work_items": 3,
        "max_concurrency": 1,
        "max_attempts": 2,
        "max_repairs": 1,
        "compute_api_budget": {"api_calls": 3, "compute_seconds": 30},
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


def _record(**overrides: object) -> WorkItemRecord:
    fields = {
        "schema_id": WORK_ITEM_STATE_SCHEMA_ID,
        "work_item_id": "wi-1",
        "lease_id": "lease-a2-p1",
        "backlog_id": "backlog-a2-p1",
        "state": WorkItemState.LEASE_ADMITTED,
        "version": 3,
        "attempt_count": 1,
        "repair_count": 0,
        "budget_consumed": 0,
        "budget_limit": 0,
        "max_attempts": 2,
        "max_repairs": 1,
        "cleanup_required": False,
    }
    fields.update(overrides)
    return WorkItemRecord(**fields)


def _lease_identity_row(lease: StandingLease | None = None, *, created_at: str = CANONICAL_TIMESTAMP) -> dict[str, object]:
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
        "created_at": created_at,
    }


def _authorization_row(
    decision: AuthorizationDecision | None = None,
    *,
    created_at: str = CANONICAL_TIMESTAMP,
) -> dict[str, object]:
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
        "created_at": created_at,
    }


def _dependency_row(
    decision: DependencyDecision | None = None,
    *,
    created_at: str = CANONICAL_TIMESTAMP,
) -> dict[str, object]:
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
        "created_at": created_at,
    }


def _work_item_row(record: WorkItemRecord | None = None, *, updated_at: str = CANONICAL_TIMESTAMP) -> dict[str, object]:
    record = record or _record()
    row = {**record.to_dict(), "updated_at": updated_at}
    row["state"] = record.state.value
    row["cleanup_required"] = encode_sqlite_boolean(record.cleanup_required, "work_item_row.cleanup_required")
    return row


def _admitted_backlog_row(
    backlog: FiniteBacklog | None = None,
    *,
    admitted_at: str = CANONICAL_TIMESTAMP,
) -> dict[str, object]:
    backlog = backlog or _backlog()
    return {
        "backlog_id": backlog.backlog_id,
        "lease_ref": backlog.lease_reference,
        "schema_id": backlog.schema_id,
        "schema_version": backlog.schema_version,
        "content_digest": backlog.content_digest,
        "canonical_json": canonical_json_bytes(backlog.to_dict()).decode("utf-8"),
        "admitted_at": admitted_at,
    }


def _global_stop_clear_row(*, updated_at: str = "1970-01-01T00:00:00Z") -> dict[str, object]:
    return {
        "singleton_id": 1,
        "schema_id": GLOBAL_STOP_SCHEMA_ID,
        "version": 0,
        "active": 0,
        "stop_id": None,
        "reason_class": None,
        "issuer_ref": None,
        "issued_at": None,
        "operator_decision_ref": None,
        "updated_at": updated_at,
    }


def _global_stop_active_row(*, updated_at: str = CANONICAL_TIMESTAMP) -> dict[str, object]:
    return {
        "singleton_id": 1,
        "schema_id": GLOBAL_STOP_SCHEMA_ID,
        "version": 2,
        "active": 1,
        "stop_id": "stop-1",
        "reason_class": "operator_stop",
        "issuer_ref": "operator-policy",
        "issued_at": "2026-07-14T00:00:00Z",
        "operator_decision_ref": "operator-decision-1",
        "updated_at": updated_at,
    }


def _assert_integrity_failure(call: object) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()  # type: ignore[operator]
    assert exc_info.value.error_class == "database_integrity_failure"
    assert str(exc_info.value) == "database_integrity_failure"
    assert exc_info.value.args == ("database_integrity_failure",)
    public_shape = f"{exc_info.value!r} {exc_info.value.args!r} {exc_info.value}"
    for forbidden in (
        PRIVATE_REF,
        PRIVATE_PATH,
        "canonical_json",
        "opaque_private_assignment_ref",
        "allowed_paths",
        "branch_policy",
        "stop_conditions",
        "validation_profile",
    ):
        assert forbidden not in public_shape
    return exc_info.value


def _exception_graph(exc: BaseException) -> tuple[BaseException, ...]:
    seen: set[int] = set()
    pending = [exc]
    graph: list[BaseException] = []
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        graph.append(current)
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return tuple(graph)


def _assert_exception_graph_omits(exc: BaseException, sentinel: str) -> None:
    rendered = [
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    ]
    for node in _exception_graph(exc):
        rendered.extend((str(node), repr(node), repr(node.args)))
    assert sentinel not in "\n".join(rendered)


def _assert_timestamp_integrity_failure_is_redacted(call: object) -> SQLiteMutationStoreError:
    exc = _assert_integrity_failure(call)
    _assert_exception_graph_omits(exc, PRIVATE_TIMESTAMP)
    return exc


def _assert_safe_envelope_repr(envelope: object) -> None:
    rendered = repr(envelope)
    for forbidden in (
        PRIVATE_REF,
        PRIVATE_PATH,
        "canonical_json",
        "opaque_private_assignment_ref",
        "allowed_paths",
        "branch_policy",
        "stop_conditions",
        "validation_profile",
        "content_digest",
    ):
        assert forbidden not in rendered


def test_lease_identity_full_row_reconstructs_envelope_and_retains_created_at() -> None:
    lease = _lease()
    row = _lease_identity_row(lease, created_at="2026-07-14T00:00:04Z")

    envelope = lease_identity_record_envelope_from_row(row)

    assert isinstance(envelope, LeaseIdentityRecordEnvelope)
    assert envelope.created_at == "2026-07-14T00:00:04Z"
    assert envelope.reconstruction.lease == lease
    assert envelope.reconstruction.validation == lease.validate_identity()
    _assert_safe_envelope_repr(envelope)


def test_lease_identity_row_shape_booleans_canonical_digest_and_timestamp_are_strict() -> None:
    row = _lease_identity_row()
    for malformed in (
        {key: value for key, value in row.items() if key != "created_at"},
        {**row, "extra": "nope"},
        {**row, "identity_valid": True},
        {**row, "lease_ref": "lease-other"},
        {**row, "canonical_digest": "b" * 64},
        {**row, "canonical_json": json.dumps(_lease().to_dict(), indent=2, sort_keys=True)},
        {**row, "created_at": "2026-07-14T00:00:04+00:00"},
        {**row, "created_at": "2026-07-14T00:00:04.000001Z"},
    ):
        _assert_integrity_failure(lambda malformed=malformed: lease_identity_record_envelope_from_row(malformed))


def test_authorization_full_row_reconstructs_unsupported_receipt_and_retains_created_at() -> None:
    decision = UnsupportedAuthorizationProvider().authorize(_lease())
    envelope = authorization_receipt_envelope_from_row(
        _authorization_row(decision, created_at="2026-07-14T00:00:05Z")
    )

    assert isinstance(envelope, AuthorizationReceiptEnvelope)
    assert envelope.decision == decision
    assert envelope.created_at == "2026-07-14T00:00:05Z"
    _assert_safe_envelope_repr(envelope)


def test_authorization_row_strict_booleans_canonical_equality_and_operator_policy_is_untrusted() -> None:
    lease = _lease()
    identity = lease.validate_identity()
    operator_policy = AuthorizationDecision(
        decision_ref="authz-operator-policy",
        lease_ref=lease.lease_id,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=True,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=True,
        executable=True,
        reason="accepted",
    )
    envelope = authorization_receipt_envelope_from_row(_authorization_row(operator_policy))
    assert envelope.decision == operator_policy
    assert classify_authorization_model_for_b3(envelope.decision) is B3AuthorizationModelHandling.UNSUPPORTED_AUTHORITATIVE_MODEL

    row = _authorization_row()
    for malformed in (
        {**row, "authorized": True},
        {**row, "executable": Decimal("0")},
        {**row, "lease_identity_valid": "1"},
        {**row, "reason": "accepted"},
        {**row, "canonical_digest": "b" * 64},
        {**row, "created_at": "2026-07-14T00:00:03"},
    ):
        _assert_integrity_failure(lambda malformed=malformed: authorization_receipt_envelope_from_row(malformed))


def test_dependency_full_rows_reconstruct_bound_and_neutral_decisions() -> None:
    bound = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    neutral = DependencyDecision()

    bound_envelope = dependency_receipt_envelope_from_row(_dependency_row(bound))
    neutral_envelope = dependency_receipt_envelope_from_row(_dependency_row(neutral))

    assert isinstance(bound_envelope, DependencyReceiptEnvelope)
    assert bound_envelope.decision == bound
    assert bound_envelope.created_at == CANONICAL_TIMESTAMP
    assert neutral_envelope.decision == neutral
    _assert_safe_envelope_repr(bound_envelope)


def test_dependency_row_strict_boolean_canonical_index_and_timestamp_validation() -> None:
    row = _dependency_row()
    for malformed in (
        {**row, "dependencies_satisfied": False},
        {**row, "work_item_id": "wi-other"},
        {**row, "canonical_json": row["canonical_json"].replace('"work_item_id":"wi-1"', '"work_item_id":"wi-other"')},
        {**row, "canonical_digest": "c" * 64},
        {**row, "created_at": datetime(2026, 7, 14, 0, 0, 3, tzinfo=timezone.utc)},
    ):
        _assert_integrity_failure(lambda malformed=malformed: dependency_receipt_envelope_from_row(malformed))


def test_work_item_full_row_envelope_and_compatibility_adapter_return_record() -> None:
    record = _record()
    row = _work_item_row(record, updated_at="2026-07-14T00:00:06Z")

    envelope = work_item_record_envelope_from_row(row)

    assert isinstance(envelope, WorkItemRecordEnvelope)
    assert envelope.record == record
    assert envelope.updated_at == "2026-07-14T00:00:06Z"
    assert work_item_record_from_row(row) == record
    assert record.budget_consumed == 0
    assert record.budget_limit == 0
    assert "validate_b3_work_item_authority_binding" not in inspect.getsource(work_item_record_envelope_from_row)
    _assert_safe_envelope_repr(envelope)


def test_work_item_row_strict_boolean_enum_counter_ref_and_timestamp_validation() -> None:
    row = _work_item_row()
    for malformed in (
        {**row, "cleanup_required": True},
        {**row, "state": "not-a-state"},
        {**row, "version": True},
        {**row, "work_item_id": "secret-ref"},
        {**row, "updated_at": "2026-07-14T00:00:06-04:00"},
        {**row, "updated_at": "2026-07-14T00:00:06.100000Z"},
    ):
        _assert_integrity_failure(lambda malformed=malformed: work_item_record_envelope_from_row(malformed))


def test_admitted_backlog_full_row_reconstructs_identical_backlog_and_retains_admitted_at() -> None:
    backlog = _backlog()
    row = _admitted_backlog_row(backlog, admitted_at="2026-07-14T00:00:07Z")

    envelope = admitted_backlog_record_envelope_from_row(row)

    assert isinstance(envelope, AdmittedBacklogRecordEnvelope)
    assert envelope.backlog == backlog
    assert envelope.admitted_at == "2026-07-14T00:00:07Z"
    _assert_safe_envelope_repr(envelope)


@pytest.mark.parametrize(
    "mutate",
    (
        lambda row: {**row, "backlog_id": "backlog-other"},
        lambda row: {**row, "lease_ref": "lease-other"},
        lambda row: {**row, "schema_id": "governed-execution.nwp-finite-backlog.v2"},
        lambda row: {**row, "schema_version": 2},
        lambda row: {**row, "schema_version": True},
        lambda row: {**row, "content_digest": "d" * 64},
    ),
)
def test_admitted_backlog_row_requires_index_schema_version_and_digest_equality(mutate: object) -> None:
    row = _admitted_backlog_row()
    malformed = mutate(row)  # type: ignore[operator]
    _assert_integrity_failure(lambda: admitted_backlog_record_envelope_from_row(malformed))


def test_admitted_backlog_row_requires_literal_canonical_json_and_rejects_unknown_duplicate_content() -> None:
    backlog = _backlog()
    row = _admitted_backlog_row(backlog)
    noncanonical = {**row, "canonical_json": json.dumps(backlog.to_dict(), indent=2, sort_keys=True)}
    unknown_payload = {**backlog.to_dict(), "extra": "field"}
    duplicate_json = row["canonical_json"].replace(
        '"backlog_id":"backlog-a2-p1"',
        '"backlog_id":"backlog-a2-p1","backlog_id":"backlog-a2-p1"',
        1,
    )
    embedded_digest_mismatch = deepcopy(backlog.to_dict())
    embedded_digest_mismatch["content_digest"] = "e" * 64

    for malformed in (
        noncanonical,
        {**row, "canonical_json": canonical_json_bytes(unknown_payload).decode("utf-8")},
        {**row, "canonical_json": duplicate_json},
        {**row, "canonical_json": canonical_json_bytes(embedded_digest_mismatch).decode("utf-8")},
        {**row, "admitted_at": "2026-07-14T00:00:07+00:00"},
    ):
        _assert_integrity_failure(lambda malformed=malformed: admitted_backlog_record_envelope_from_row(malformed))


def test_admitted_backlog_errors_and_reprs_do_not_expose_private_backlog_material() -> None:
    row = _admitted_backlog_row()
    _assert_integrity_failure(
        lambda: admitted_backlog_record_envelope_from_row({**row, "content_digest": "f" * 64})
    )
    contract = AdmittedBacklogRecordContract.from_dict(row)
    assert PRIVATE_REF not in repr(contract)
    assert PRIVATE_PATH not in repr(contract)
    assert "canonical_json" not in repr(contract)
    assert "content_digest" not in repr(contract)


def test_global_stop_current_clear_and_active_singleton_rows_reconstruct_envelopes() -> None:
    clear_envelope = global_stop_current_envelope_from_row(_global_stop_clear_row())
    active_envelope = global_stop_current_envelope_from_row(_global_stop_active_row(updated_at="2026-07-14T00:00:08Z"))

    assert isinstance(clear_envelope, GlobalStopCurrentRecordEnvelope)
    assert clear_envelope.state == GlobalStopState()
    assert clear_envelope.updated_at == "1970-01-01T00:00:00Z"
    assert active_envelope.state == GlobalStopState(
        version=2,
        active=True,
        stop_id="stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        operator_decision_ref="operator-decision-1",
    )
    assert active_envelope.updated_at == "2026-07-14T00:00:08Z"
    _assert_safe_envelope_repr(active_envelope)


def test_global_stop_current_row_rejects_type_enum_timestamp_and_nullability_contradictions() -> None:
    clear = _global_stop_clear_row()
    active = _global_stop_active_row()
    for malformed in (
        {**clear, "singleton_id": True},
        {**clear, "singleton_id": 2},
        {**clear, "schema_id": "governed-execution.nwp-global-stop.v2"},
        {**clear, "version": True},
        {**clear, "active": True},
        {**clear, "stop_id": "stop-1"},
        {**active, "stop_id": None},
        {**active, "reason_class": "not-a-reason"},
        {**active, "issuer_ref": "endpoint-issuer"},
        {**active, "issued_at": "2026-07-14T00:00:00.000001Z"},
        {**active, "updated_at": "2026-07-14T00:00:08+00:00"},
    ):
        _assert_integrity_failure(lambda malformed=malformed: global_stop_current_envelope_from_row(malformed))


def test_operational_timestamp_changes_do_not_change_semantic_models_or_digests() -> None:
    record = _record()
    first = work_item_record_envelope_from_row(_work_item_row(record, updated_at="2026-07-14T00:00:09Z"))
    second = work_item_record_envelope_from_row(_work_item_row(record, updated_at="2026-07-14T00:00:10Z"))
    assert first.record == second.record
    assert first.record.canonical_digest() == second.record.canonical_digest()
    assert first.updated_at != second.updated_at

    backlog = _backlog()
    admitted_first = admitted_backlog_record_envelope_from_row(
        _admitted_backlog_row(backlog, admitted_at="2026-07-14T00:00:09Z")
    )
    admitted_second = admitted_backlog_record_envelope_from_row(
        _admitted_backlog_row(backlog, admitted_at="2026-07-14T00:00:10Z")
    )
    assert admitted_first.backlog == admitted_second.backlog
    assert admitted_first.backlog.content_digest == admitted_second.backlog.content_digest
    assert admitted_first.admitted_at != admitted_second.admitted_at


@pytest.mark.parametrize(
    "timestamp",
    (
        "2026-07-14T00:00:03",
        "2026-07-14T00:00:03-04:00",
        "2026-07-14T00:00:03+00:00",
        "2026-07-14T00:00:03.000001Z",
        datetime(2026, 7, 14, 0, 0, 3, tzinfo=timezone.utc),
    ),
)
def test_operational_timestamp_envelopes_reject_non_canonical_utc_z_values(timestamp: object) -> None:
    _assert_integrity_failure(
        lambda: work_item_record_envelope_from_row(_work_item_row(updated_at=timestamp))  # type: ignore[arg-type]
    )


@pytest.mark.parametrize(
    ("adapter", "row_factory", "timestamp_field"),
    (
        (lease_identity_record_envelope_from_row, _lease_identity_row, "created_at"),
        (authorization_receipt_envelope_from_row, _authorization_row, "created_at"),
        (dependency_receipt_envelope_from_row, _dependency_row, "created_at"),
        (work_item_record_envelope_from_row, _work_item_row, "updated_at"),
        (admitted_backlog_record_envelope_from_row, _admitted_backlog_row, "admitted_at"),
        (global_stop_current_envelope_from_row, _global_stop_clear_row, "updated_at"),
        (global_stop_current_envelope_from_row, _global_stop_active_row, "issued_at"),
    ),
)
def test_row_timestamp_parse_failures_do_not_retain_rejected_literals(
    adapter: object,
    row_factory: object,
    timestamp_field: str,
) -> None:
    row = row_factory()  # type: ignore[operator]
    malformed = {**row, timestamp_field: PRIVATE_TIMESTAMP}

    _assert_timestamp_integrity_failure_is_redacted(lambda: adapter(malformed))  # type: ignore[operator]


@pytest.mark.parametrize(
    ("envelope_factory", "timestamp_field"),
    (
        (lambda: lease_identity_record_envelope_from_row(_lease_identity_row()), "created_at"),
        (lambda: authorization_receipt_envelope_from_row(_authorization_row()), "created_at"),
        (lambda: dependency_receipt_envelope_from_row(_dependency_row()), "created_at"),
        (lambda: work_item_record_envelope_from_row(_work_item_row()), "updated_at"),
        (lambda: admitted_backlog_record_envelope_from_row(_admitted_backlog_row()), "admitted_at"),
        (lambda: global_stop_current_envelope_from_row(_global_stop_clear_row()), "updated_at"),
    ),
)
def test_envelope_timestamp_parse_failures_do_not_retain_rejected_literals(
    envelope_factory: object,
    timestamp_field: str,
) -> None:
    envelope = envelope_factory()  # type: ignore[operator]

    _assert_timestamp_integrity_failure_is_redacted(
        lambda: replace(envelope, **{timestamp_field: PRIVATE_TIMESTAMP})
    )


def test_envelopes_have_no_public_serialization_or_report_methods() -> None:
    envelopes = (
        lease_identity_record_envelope_from_row(_lease_identity_row()),
        authorization_receipt_envelope_from_row(_authorization_row()),
        dependency_receipt_envelope_from_row(_dependency_row()),
        work_item_record_envelope_from_row(_work_item_row()),
        admitted_backlog_record_envelope_from_row(_admitted_backlog_row()),
        global_stop_current_envelope_from_row(_global_stop_clear_row()),
    )
    for envelope in envelopes:
        assert not hasattr(envelope, "to_dict")
        assert not hasattr(envelope, "canonical_json")
        assert not hasattr(envelope, "report")


def test_b3b1_docs_pin_pure_row_scope_and_timestamp_posture() -> None:
    doc = (ROOT / ".docs/b3b1-pure-row-contracts.md").read_text(encoding="utf-8")
    normalized = " ".join(doc.split())
    for phrase in (
        "Status: implemented pure/model row contracts; no SQLite readers or fixtures",
        "already-fetched explicit-column SQLite row mappings",
        "Every adapter requires the complete explicit SQL column set",
        "operational row timestamps",
        "do not change the canonical semantic identity or digest",
        "The compatibility function `work_item_record_from_row(payload)` delegates",
        "does not validate cross-record lease/backlog/work-item authority by itself",
        "The row has no canonical JSON or digest",
        "adds no SQLite `SELECT`",
        "B3b1 tests are repo-hermetic",
        "do not require sibling checkouts",
        "related-repo cleanliness is closeout and audit evidence",
        "retained exception chains or tracebacks",
        "safe field-class failures",
        "B3b2 remains future",
    ):
        assert phrase in normalized


def test_b3b1_contract_path_has_no_sqlite_import_sql_io_reader_or_runtime_mutation_surface() -> None:
    persistence_path = PACKAGE_DIR / "persistence_contracts.py"
    source = persistence_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    assert "sqlite3" not in imported_modules
    assert not any(name.startswith("sqlite3") for name in imported_modules)

    b3b1_objects = (
        LeaseIdentityRecordEnvelope,
        AuthorizationReceiptEnvelope,
        DependencyReceiptEnvelope,
        WorkItemRecordEnvelope,
        AdmittedBacklogRecordEnvelope,
        GlobalStopCurrentRecordEnvelope,
        admitted_backlog_record_envelope_from_row,
        authorization_receipt_envelope_from_row,
        dependency_receipt_envelope_from_row,
        global_stop_current_envelope_from_row,
        lease_identity_record_envelope_from_row,
        work_item_record_envelope_from_row,
    )
    b3b1_source = "\n".join(inspect.getsource(obj) for obj in b3b1_objects)
    for token in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "BEGIN ", "COMMIT", "ROLLBACK"):
        assert token not in b3b1_source
    for forbidden in (
        "connect(",
        "Connection",
        "database_path",
        "row_factory",
        "read_scope",
        "TransitionContext",
        "apply_transition",
        "apply_global_stop",
        "event_sequence",
        "expected_version",
        "idempotency",
        "operator_policy_verifier",
        "seed_authorization",
        "seed_work_item",
    ):
        assert forbidden not in b3b1_source


def test_b3b1_public_export_schema_and_local_boundaries_are_unchanged() -> None:
    for name in (
        "LeaseIdentityRecordEnvelope",
        "AuthorizationReceiptEnvelope",
        "DependencyReceiptEnvelope",
        "WorkItemRecordEnvelope",
        "AdmittedBacklogRecordEnvelope",
        "GlobalStopCurrentRecordEnvelope",
        "admitted_backlog_record_envelope_from_row",
        "global_stop_current_envelope_from_row",
    ):
        assert name not in ge_nwp_coordinator.__all__

    assert not (PACKAGE_DIR / "sqlite_transition_readers.py").exists()
    assert not (PACKAGE_DIR / "sqlite_transition_fixtures.py").exists()
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == ["0001_initial.sql"]
    migration_bytes = (PACKAGE_DIR / "sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM

    assert validate_b3_work_item_authority_binding.__name__ not in ge_nwp_coordinator.__all__
