from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import inspect
from pathlib import Path

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, FiniteBacklog, WorkItem
from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.lease import (
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    AuthorizationModel,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
    LeaseRevocationState,
    Permission,
    StandingLease,
)
from ge_nwp_coordinator.persistence_contracts import validate_b3_work_item_authority_binding
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.state_machine import (
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluationKind,
    WorkItemRecord,
    WorkItemState,
    transition,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"


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


def _item(
    work_item_id: str,
    *,
    api_calls: int,
    compute_seconds: int,
    dependencies: tuple[str, ...] = (),
) -> WorkItem:
    return WorkItem(
        work_item_id=work_item_id,
        objective_label=f"{work_item_id} objective",
        opaque_private_assignment_ref=f"private-ref-{work_item_id}",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src", "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": api_calls, "compute_seconds": compute_seconds},
        dependencies=dependencies,
        stop_conditions=("global-stop",),
    )


def _backlog(
    *,
    backlog_id: str = "backlog-a2-p1",
    lease_reference: str = "lease-a2-p1",
    items: tuple[WorkItem, ...] | None = None,
) -> FiniteBacklog:
    backlog = FiniteBacklog(
        schema_id=BACKLOG_SCHEMA_ID,
        schema_version=1,
        backlog_id=backlog_id,
        lease_reference=lease_reference,
        work_items=items
        or (
            _item("wi-1", api_calls=1, compute_seconds=10),
            _item("wi-2", api_calls=2, compute_seconds=20, dependencies=("wi-1",)),
        ),
        content_digest="0" * 64,
    )
    return backlog.with_digest()


def _lease(backlog: FiniteBacklog, **overrides: object) -> StandingLease:
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
        "finite_backlog_reference": backlog.backlog_id,
        "finite_backlog_digest": backlog.content_digest,
        "max_work_items": 2,
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


def _record(
    lease: StandingLease,
    backlog: FiniteBacklog,
    *,
    work_item_id: str = "wi-1",
    max_attempts: int | None = None,
    max_repairs: int | None = None,
) -> WorkItemRecord:
    return WorkItemRecord(
        work_item_id=work_item_id,
        lease_id=lease.lease_id,
        backlog_id=backlog.backlog_id,
        max_attempts=lease.max_attempts if max_attempts is None else max_attempts,
        max_repairs=lease.max_repairs if max_repairs is None else max_repairs,
    )


def _assert_integrity_failure(call: object) -> None:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()  # type: ignore[operator]
    assert exc_info.value.error_class == "database_integrity_failure"
    assert str(exc_info.value) == "database_integrity_failure"
    assert "private-ref" not in repr(exc_info.value)
    assert "allowed_paths" not in repr(exc_info.value)


def test_b3b_authority_binding_passes_and_returns_matched_backlog_work_item() -> None:
    backlog = _backlog()
    lease = _lease(backlog)
    record = _record(lease, backlog)

    matched = validate_b3_work_item_authority_binding(lease, backlog, record)

    assert matched == backlog.work_items[0]
    assert matched.work_item_id == record.work_item_id
    assert record.budget_consumed == 0
    assert record.budget_limit == 0
    assert matched.budget_allocation["api_calls"] == 1
    assert matched.budget_allocation["compute_seconds"] == 10


@pytest.mark.parametrize(
    "mutate",
    (
        lambda lease, backlog, record: (lease, backlog, replace(record, backlog_id="backlog-other")),
        lambda lease, backlog, record: (_lease(_backlog(lease_reference="lease-other")), _backlog(lease_reference="lease-other"), record),
        lambda lease, backlog, record: (replace(lease, finite_backlog_digest="b" * 64), backlog, record),
        lambda lease, backlog, record: (lease, backlog, replace(record, work_item_id="wi-missing")),
        lambda lease, backlog, record: (_lease(backlog, max_work_items=1), backlog, record),
    ),
)
def test_b3b_authority_binding_rejects_backlog_chain_mismatches(mutate: object) -> None:
    backlog = _backlog()
    lease = _lease(backlog)
    record = _record(lease, backlog)
    changed_lease, changed_backlog, changed_record = mutate(lease, backlog, record)  # type: ignore[operator]

    _assert_integrity_failure(
        lambda: validate_b3_work_item_authority_binding(changed_lease, changed_backlog, changed_record)
    )


@pytest.mark.parametrize(
    "mutate_record",
    (
        lambda record: replace(record, max_attempts=record.max_attempts - 1),
        lambda record: replace(record, max_attempts=record.max_attempts + 1),
        lambda record: replace(record, max_repairs=record.max_repairs - 1),
        lambda record: replace(record, max_repairs=record.max_repairs + 1),
        lambda record: replace(record, attempt_count=record.max_attempts + 1),
        lambda record: replace(record, repair_count=record.max_repairs + 1),
    ),
)
def test_b3b_authority_binding_rejects_limit_provenance_mismatches(mutate_record: object) -> None:
    backlog = _backlog()
    lease = _lease(backlog)
    record = _record(lease, backlog)

    _assert_integrity_failure(
        lambda: validate_b3_work_item_authority_binding(lease, backlog, mutate_record(record))  # type: ignore[operator]
    )


@pytest.mark.parametrize(
    "mutate_record",
    (
        lambda record: replace(record, budget_consumed=1),
        lambda record: replace(record, budget_limit=1),
    ),
)
def test_b3b_bounded_slice_requires_zero_scalar_budget_fields(mutate_record: object) -> None:
    backlog = _backlog()
    lease = _lease(backlog)
    record = _record(lease, backlog)

    _assert_integrity_failure(
        lambda: validate_b3_work_item_authority_binding(lease, backlog, mutate_record(record))  # type: ignore[operator]
    )


def test_b3b_static_multidimensional_budget_policy_rejects_per_item_and_sum_overages() -> None:
    item_over = _backlog(items=(_item("wi-1", api_calls=4, compute_seconds=10),))
    item_over_lease = _lease(item_over, compute_api_budget={"api_calls": 3, "compute_seconds": 30})
    _assert_integrity_failure(
        lambda: validate_b3_work_item_authority_binding(item_over_lease, item_over, _record(item_over_lease, item_over))
    )

    sum_over = _backlog(
        items=(
            _item("wi-1", api_calls=2, compute_seconds=10),
            _item("wi-2", api_calls=2, compute_seconds=10, dependencies=("wi-1",)),
        )
    )
    sum_over_lease = _lease(sum_over, compute_api_budget={"api_calls": 3, "compute_seconds": 30})
    _assert_integrity_failure(
        lambda: validate_b3_work_item_authority_binding(sum_over_lease, sum_over, _record(sum_over_lease, sum_over))
    )


def _transition_context(dependency: DependencyDecision | None = None) -> TransitionContext:
    identity = LeaseIdentityValidation(
        identity_valid=True,
        digest="a" * 64,
        issues=(),
        decision_ref="lease-identity-lease-a2-p1",
        lease_ref="lease-a2-p1",
    )
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
        lease_runtime=LeaseRuntimeDecision(
            lease_ref=identity.lease_ref,
            evaluated_at="2026-07-14T00:00:02Z",
            status=LeaseRuntimeStatus.ACTIVE,
            reason="lease_runtime_active",
        ),
        global_stop=GlobalStopState(),
        dependency_decision=dependency if dependency is not None else DependencyDecision(),
    )


def _transition_command(
    record: WorkItemRecord,
    target: WorkItemState,
    context: TransitionContext,
    *,
    dependency_decision_ref: str | None,
) -> TransitionCommand:
    return TransitionCommand.create(
        work_item_id=record.work_item_id,
        idempotency_key=f"transition-{target.value.replace('_', '-')}",
        expected_version=record.version,
        target_state=target,
        lease_identity_decision_ref=context.lease_identity.decision_ref,
        authorization_decision_ref=context.authorization.decision_ref,
        global_stop_ref=context.global_stop.stop_ref,
        global_stop_version=context.global_stop.version,
        dependency_decision_ref=dependency_decision_ref,
    )


def test_b3b_dependency_refs_are_ready_only_and_invalid_cases_create_no_event() -> None:
    admitted = WorkItemRecord(
        work_item_id="wi-1",
        lease_id="lease-a2-p1",
        backlog_id="backlog-a2-p1",
        state=WorkItemState.LEASE_ADMITTED,
    )
    ready_context = _transition_context(DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1"))

    ready_missing_ref = transition(
        admitted,
        _transition_command(admitted, WorkItemState.READY, ready_context, dependency_decision_ref=None),
        ready_context,
    )
    assert ready_missing_ref.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert ready_missing_ref.reason == "dependency_reference_mismatch"
    assert ready_missing_ref.event is None

    ready_false_context = _transition_context(
        DependencyDecision(
            decision_ref="deps-ready",
            work_item_id="wi-1",
            dependencies_satisfied=False,
            reason="dependencies_not_satisfied",
        )
    )
    ready_false = transition(
        admitted,
        _transition_command(admitted, WorkItemState.READY, ready_false_context, dependency_decision_ref="deps-ready"),
        ready_false_context,
    )
    assert ready_false.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    assert ready_false.reason == "dependencies_not_satisfied"
    assert ready_false.event is not None

    proposed = replace(admitted, state=WorkItemState.PROPOSED, version=0)
    neutral_context = _transition_context(DependencyDecision())
    non_ready_null = transition(
        proposed,
        _transition_command(proposed, WorkItemState.LEASE_ADMITTED, neutral_context, dependency_decision_ref=None),
        neutral_context,
    )
    assert non_ready_null.accepted

    matching_ref_context = _transition_context(DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1"))
    non_ready_with_ref = transition(
        proposed,
        _transition_command(proposed, WorkItemState.LEASE_ADMITTED, matching_ref_context, dependency_decision_ref="deps-ready"),
        matching_ref_context,
    )
    assert non_ready_with_ref.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    assert non_ready_with_ref.reason == "dependency_reference_mismatch"
    assert non_ready_with_ref.event is None


def test_b3b_prerequisite_docs_pin_zero_cost_schema_and_internal_timestamp_contracts() -> None:
    doc = (ROOT / ".docs/b3b-reader-prerequisite-contract.md").read_text(encoding="utf-8")
    normalized = " ".join(doc.split())
    for phrase in (
        "Status: contract-only prerequisite plus later B3b2b private SELECT readers",
        "B3b2b is a later implementation slice",
        "No production SQLite reader integration is added",
        "No test database fixture insertion helper exists in this tranche",
        "WorkItemRecord.budget_consumed == 0",
        "TransitionCommand.budget_cost == 0",
        "dependency receipts are READY-only",
        "schema 0001 is sufficient for the bounded B3b reader slice",
        "Future multidimensional dynamic consumption accounting requires a separately audited versioned contract",
        "operational timestamps may be retained only in internal typed envelopes",
    ):
        assert phrase in normalized


def test_b3b_prerequisite_boundary_has_no_reader_fixture_export_or_schema_change() -> None:
    package_dir = ROOT / "src/ge_nwp_coordinator"
    source_paths = tuple(
        path
        for path in package_dir.rglob("*.py")
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
    helper_source = inspect.getsource(validate_b3_work_item_authority_binding)

    assert "sqlite3" not in (package_dir / "persistence_contracts.py").read_text(encoding="utf-8")
    for token in ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "BEGIN", "COMMIT", "ROLLBACK"):
        assert token not in helper_source
    for forbidden in (
        "sqlite_transition_readers",
        "B3ReadScope",
        "seed_authorization",
        "seed_work_item",
        "seed_b3",
        "INSERT INTO transition_events",
        "INSERT INTO global_stop_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
        "lookup_idempotency",
        "operator_policy_verifier",
        "CoordinatorService",
        "Scheduler",
        "QueueConsumer",
        "socket",
        "urllib",
    ):
        assert forbidden not in source
    assert validate_b3_work_item_authority_binding.__name__ not in ge_nwp_coordinator.__all__
    assert not (package_dir / "sqlite_transition_readers.py").exists()
    assert not (package_dir / "sqlite_transition_fixtures.py").exists()
    assert sorted(path.name for path in (package_dir / "sqlite_migrations").glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
        "0004_rw0_c1_durable_evidence.sql",
        "0005_section41_post_execution_proposal_family.sql",
    ]
    migration_bytes = (package_dir / "sqlite_migrations/0001_initial.sql").read_bytes()
    assert hashlib.sha256(migration_bytes).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
