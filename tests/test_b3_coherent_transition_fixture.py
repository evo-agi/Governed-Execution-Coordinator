from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pytest

import ge_nwp_coordinator
from b3_coherent_transition_fixture import (
    FIXTURE_TIMESTAMP,
    BlockedFixtureAuthorityContract,
    CoherentTransitionFixture,
    authorization_receipt_rows_for_test,
    dependency_receipt_count_for_test,
    exact_replay_for_test,
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    read_back_fixture_for_test,
    transition_event_count_for_test,
    _replace_work_item_budget_limit_for_test,
    _replace_work_item_lease_for_test,
)
from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.lease import AuthorizationModel, LeaseRuntimeStatus
from ge_nwp_coordinator.persistence_contracts import (
    validate_b3_work_item_authority_binding,
)
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_migration import DatabaseClassification, validate_database
from ge_nwp_coordinator.state_machine import WorkItemState
from ge_nwp_coordinator.state_store import StateStore, WriterSession


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TEST_FIXTURE_PATH = ROOT / "tests/b3_coherent_transition_fixture.py"
MIGRATION_PATH = PACKAGE_DIR / "sqlite_migrations/0001_initial.sql"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"


def _writer_generations_for_test(fixture: CoherentTransitionFixture) -> tuple[int, ...]:
    connection = open_existing_sqlite_connection(fixture.location, read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT generation
            FROM writer_ownership
            ORDER BY singleton_id
            """
        ).fetchall()
        return tuple(int(row[0]) for row in rows)
    finally:
        connection.close()


def _transition_outcomes_for_test(fixture: CoherentTransitionFixture) -> tuple[str, ...]:
    connection = open_existing_sqlite_connection(fixture.location, read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT outcome
            FROM transition_events
            ORDER BY event_sequence
            """
        ).fetchall()
        return tuple(str(row[0]) for row in rows)
    finally:
        connection.close()


def _assert_integrity_failure(call: object) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()  # type: ignore[operator]
    assert exc_info.value.error_class == "database_integrity_failure"
    assert str(exc_info.value) == "database_integrity_failure"
    assert exc_info.value.args == ("database_integrity_failure",)
    return exc_info.value


def test_fixture_module_exists_only_under_tests_and_exports_no_production_surface() -> None:
    assert TEST_FIXTURE_PATH.exists()
    assert not (PACKAGE_DIR / "b3_coherent_transition_fixture.py").exists()
    assert not (PACKAGE_DIR / "sqlite_transition_fixtures.py").exists()
    assert not list(PACKAGE_DIR.rglob("*fixture*.py"))
    assert not list(PACKAGE_DIR.rglob("*seed*.py"))
    assert not list(PACKAGE_DIR.rglob("*admission*.py"))

    source = TEST_FIXTURE_PATH.read_text(encoding="utf-8")
    for phrase in (
        "Tests-only synthetic",
        "not admission",
        "not authorization",
        "not production state initialization",
        "not runtime authority",
        "The setup transaction is not the future B3c transaction path",
    ):
        assert phrase in source

    for name in (
        "CoherentTransitionFixture",
        "make_coherent_transition_fixture_for_test",
        "read_back_fixture_for_test",
        "acquire_sqlite_writer_session",
    ):
        assert name not in ge_nwp_coordinator.__all__
        assert not hasattr(ge_nwp_coordinator, name)

    assert list(inspect.signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(inspect.signature(StateStore.read_global_stop).parameters) == ["self"]
    assert list(inspect.signature(WriterSession.apply_transition).parameters) == ["self", "transition_command"]
    assert list(inspect.signature(WriterSession.apply_global_stop_update).parameters) == [
        "self",
        "global_stop_command",
        "typed_operator_decision",
    ]


def test_base_fixture_uses_temp_managed_schema_0001_and_builds_exact_graph(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        assert fixture.location.state_root.is_relative_to(tmp_path)
        assert not fixture.location.state_root.is_relative_to(ROOT)
        inspection = validate_database(fixture.location)
        assert inspection.classification is DatabaseClassification.MANAGED
        assert inspection.current_sequence == 1
        assert inspection.latest_sequence == 1

        assert fixture.lease_identity_validation.identity_valid is True
        assert fixture.lease_identity_validation.lease_ref == fixture.lease.lease_id
        assert fixture.authorization.authorization_model is AuthorizationModel.UNSUPPORTED
        assert fixture.authorization.authorized is False
        assert fixture.authorization.executable is False
        assert fixture.authorization.reason == "unsupported_authorization_model"

        assert len(fixture.backlog.work_items) == 1
        assert fixture.work_item.work_item_id == fixture.backlog.work_items[0].work_item_id
        assert fixture.work_item.lease_id == fixture.lease.lease_id == fixture.backlog.lease_reference
        assert fixture.work_item.backlog_id == fixture.backlog.backlog_id == fixture.lease.finite_backlog_reference
        assert fixture.backlog.content_digest == fixture.lease.finite_backlog_digest
        assert fixture.work_item.max_attempts == fixture.lease.max_attempts
        assert fixture.work_item.max_repairs == fixture.lease.max_repairs
        assert fixture.work_item.budget_consumed == 0
        assert fixture.work_item.budget_limit == 0
        assert fixture.backlog.work_items[0].budget_allocation["api_calls"] <= fixture.lease.compute_api_budget["api_calls"]
        assert fixture.backlog.work_items[0].budget_allocation["compute_seconds"] <= fixture.lease.compute_api_budget["compute_seconds"]

        assert fixture.global_stop == GlobalStopState()
        assert fixture.command.target_state is WorkItemState.LEASE_ADMITTED
        assert fixture.command.dependency_decision_ref is None
        assert dependency_receipt_count_for_test(fixture) == 0
        assert global_stop_event_count_for_test(fixture) == 0
        assert transition_event_count_for_test(fixture) == 0


def test_b3b2b_readers_reconstruct_exact_seeded_rows_and_binding_passes(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        readback = read_back_fixture_for_test(fixture)

        assert readback.work_item.record == fixture.work_item
        assert readback.lease_identity.reconstruction.lease == fixture.lease
        assert readback.lease_identity.reconstruction.validation == fixture.lease_identity_validation
        assert readback.authorization.decision == fixture.authorization
        assert readback.dependency is None
        assert readback.admitted_backlog.backlog == fixture.backlog
        assert readback.global_stop.state == fixture.global_stop
        assert readback.global_stop.updated_at == "1970-01-01T00:00:00Z"

        matched = validate_b3_work_item_authority_binding(
            readback.lease_identity.reconstruction.lease,
            readback.admitted_backlog.backlog,
            readback.work_item.record,
        )
        assert matched == fixture.backlog.work_items[0]


def test_optional_ready_dependency_graph_is_coherent_and_no_neutral_receipt_is_seeded(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
        assert fixture.dependency_decision is not None
        assert fixture.dependency_decision.work_item_id == fixture.work_item.work_item_id
        assert fixture.dependency_decision.dependencies_satisfied is True
        assert fixture.dependency_decision.reason == "accepted"
        assert fixture.command.target_state is WorkItemState.READY
        assert fixture.command.dependency_decision_ref == fixture.dependency_decision.decision_ref
        assert dependency_receipt_count_for_test(fixture) == 1

        readback = read_back_fixture_for_test(fixture)
        assert readback.dependency is not None
        assert readback.dependency.decision == fixture.dependency_decision
        assert readback.work_item.record.state is WorkItemState.LEASE_ADMITTED
        assert validate_b3_work_item_authority_binding(
            fixture.lease,
            readback.admitted_backlog.backlog,
            readback.work_item.record,
        ) == fixture.backlog.work_items[0]


def test_real_writer_issuance_is_generation_one_and_session_closes_deterministically(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        session = fixture.writer_session
        assert session.active is True
        assert fixture.metadata == session.metadata
        assert fixture.metadata.generation == 1
        assert _writer_generations_for_test(fixture) == (1,)
        assert validate_database(fixture.location).classification is DatabaseClassification.MANAGED
    assert session.active is False
    session.close()
    assert session.active is False


def test_fixture_repr_hides_location_session_models_and_private_material(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        rendered = repr(fixture)
        assert "SafeWriterMetadata" in rendered
        for forbidden in (
            str(tmp_path),
            "coordinator-state.sqlite",
            "coordinator-state.migration.lock",
            "credential",
            "proof",
            "digest",
            "lock",
            "assignment-b3-fixture",
            "canonical_json",
            "lease-b3-fixture",
            "backlog-b3-fixture",
            "wi-b3-fixture",
            "TransitionEvent",
            "WorkItemRecord",
            "StandingLease",
            "FiniteBacklog",
        ):
            assert forbidden not in rendered
        for method_name in ("to_dict", "canonical_json", "report"):
            assert not hasattr(fixture, method_name)


def test_optional_domain_rejected_event_replay_and_idempotency_are_exact(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        envelope = fixture.transition_event_envelope
        assert envelope is not None
        assert envelope.event_sequence == 0
        assert envelope.created_at == FIXTURE_TIMESTAMP
        assert envelope.event.lease_runtime.evaluated_at == FIXTURE_TIMESTAMP
        assert envelope.event.lease_runtime.status is LeaseRuntimeStatus.ACTIVE
        assert envelope.event.outcome.value == "domain_rejected"
        assert envelope.event.reason == "lease_not_authorized"
        assert envelope.event.authorization_decision_ref == fixture.authorization.decision_ref
        assert envelope.event.lease_identity_decision_ref == fixture.lease_identity_validation.decision_ref
        assert envelope.event.dependency_decision_ref is None
        assert envelope.replay_record == fixture.work_item
        assert _transition_outcomes_for_test(fixture) == ("domain_rejected",)
        assert transition_event_count_for_test(fixture) == 1

        replay = exact_replay_for_test(fixture)
        assert replay.replayed is True
        assert replay.record == fixture.work_item
        assert replay.event == envelope.event
        assert transition_event_count_for_test(fixture) == 1


def test_ready_dependency_event_variant_requires_truthful_domain_rejection(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
        existing_event=True,
        dependencies_satisfied=False,
    ) as fixture:
        envelope = fixture.transition_event_envelope
        assert envelope is not None
        assert envelope.event.reason == "dependencies_not_satisfied"
        assert envelope.event.dependency_decision_ref == fixture.dependency_decision.decision_ref
        assert exact_replay_for_test(fixture).record == fixture.work_item

    with pytest.raises(BlockedFixtureAuthorityContract):
        make_coherent_transition_fixture_for_test(
            tmp_path / "accepted-ready",
            ready_dependency=True,
            existing_event=True,
            dependencies_satisfied=True,
        )


def test_no_accepted_operator_policy_or_executable_authority_is_seeded(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        assert authorization_receipt_rows_for_test(fixture) == (("unsupported", 0, 0),)
        assert fixture.authorization.authorization_model is AuthorizationModel.UNSUPPORTED
        assert fixture.authorization.authorized is False
        assert fixture.authorization.executable is False
        assert "accepted" not in _transition_outcomes_for_test(fixture)

        fixture_source = TEST_FIXTURE_PATH.read_text(encoding="utf-8")
        assert "AuthorizationModel.OPERATOR_POLICY" not in fixture_source
        assert "authorized=True" not in fixture_source
        assert "executable=True" not in fixture_source


@pytest.mark.parametrize(
    "corrupt",
    (
        _replace_work_item_lease_for_test,
        _replace_work_item_budget_limit_for_test,
    ),
)
def test_tests_only_corruption_helpers_fail_through_existing_binding_contracts(
    tmp_path: Path,
    corrupt: object,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        corrupt(fixture)  # type: ignore[operator]
        readback = read_back_fixture_for_test(fixture)

        _assert_integrity_failure(
            lambda: validate_b3_work_item_authority_binding(
                fixture.lease,
                readback.admitted_backlog.backlog,
                readback.work_item.record,
            )
        )


def test_docs_and_static_contracts_record_tests_only_fixture_status() -> None:
    doc = (ROOT / ".docs/b3-tests-only-coherent-fixtures.md").read_text(encoding="utf-8")
    normalized = " ".join(doc.split())
    for phrase in (
        "Status: implemented tests-only fixture graph",
        "no production admission or runtime authority",
        "fixtures live under `tests/` only",
        "directly seed synthetic authoritative rows",
        "direct seeding is not admission or product mutation",
        "real writer issuance is temporary test evidence only",
        "unsupported authorization remains production/default",
        "optional persisted event is domain-rejected",
        "no accepted executable transition is proved",
        "B3c1 prerequisites plus B3c1a private authority plumbing",
        "B3c1b rollback-only mechanics are private test-executed only",
        "B3c2 event/idempotency/sequence readers are private transaction-internal tests only",
        "B3c3/B3c4 remain future",
    ):
        assert phrase in normalized


def test_migration_boundary_related_surfaces_and_repo_artifacts_remain_frozen() -> None:
    assert hashlib.sha256(MIGRATION_PATH.read_bytes()).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == ["0001_initial.sql"]

    source_paths = tuple((ROOT / "src/ge_nwp_coordinator").glob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)
    for forbidden in (
        "CoherentTransitionFixture",
        "make_coherent_transition_fixture_for_test",
        "INSERT INTO transition_events",
        "UPDATE work_items",
        "class _B3cTransitionReadCapability",
        "def assemble_transition_context",
        "def verify_writer_fencing",
        "authorization_verifier",
        "trusted_local",
        "allow_all",
        "CoordinatorService",
        "Scheduler",
        "QueueConsumer",
    ):
        assert forbidden not in source

    forbidden_artifacts: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        name = path.name
        if path.is_dir() and name in {"__pycache__", ".pytest_cache"}:
            forbidden_artifacts.append(str(path.relative_to(ROOT)))
        if name.endswith((".db", ".sqlite", ".sqlite3", ".pyc")):
            forbidden_artifacts.append(str(path.relative_to(ROOT)))
        if name.endswith(("-journal", "-wal", "-shm")):
            forbidden_artifacts.append(str(path.relative_to(ROOT)))
        if name == "coordinator-state.migration.lock":
            forbidden_artifacts.append(str(path.relative_to(ROOT)))
    assert forbidden_artifacts == []
