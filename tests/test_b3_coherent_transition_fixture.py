from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

import ge_nwp_coordinator
import b3_coherent_transition_fixture as fixture_module
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
    _C2B2_PHYSICAL_TABLES,
    _FIXTURE_EMPTY_PHYSICAL_TABLES,
    _RW0_C1_PHYSICAL_TABLES,
    _SECTION41_PHYSICAL_TABLES,
    _require_c2b2_physical_tables_empty_for_test,
    _require_rw0_c1_physical_tables_empty_for_test,
    _require_section41_physical_tables_empty_for_test,
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
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import DatabaseClassification, validate_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_machine import WorkItemState
from ge_nwp_coordinator.state_store import StateStore, WriterSession


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TEST_FIXTURE_PATH = ROOT / "tests/b3_coherent_transition_fixture.py"
MIGRATION_PATH = PACKAGE_DIR / "sqlite_migrations/0001_initial.sql"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
EXPECTED_C2B2_PHYSICAL_TABLES = (
    "development_program_heads",
    "development_program_versions",
    "development_accepted_intent_revisions",
    "development_work_item_heads",
    "development_work_item_revisions",
    "development_program_version_work_items",
    "development_revision_edges",
    "development_work_spec_bindings",
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_authority_evaluations",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
    "development_decisions",
    "development_mutation_receipts",
)
EXPECTED_SECTION41_PHYSICAL_TABLES = (
    "development_model_source_invocations",
    "development_pre_execution_planning_contexts",
    "development_private_proposal_artifact_bindings",
    "development_model_proposals",
    "development_pre_execution_plan_projections",
    "development_model_proposal_evidence_bindings",
    "development_pre_execution_dispositions",
    "development_pre_execution_selection_heads",
    "development_cognitive_mutation_receipts",
)
EXPECTED_RW0_C1_PHYSICAL_TABLES = (
    "rw0_phase_instances",
    "rw0_evidence_values",
    "rw0_evidence_memberships",
    "rw0_relation_bindings",
    "rw0_relation_operands",
    "rw0_c1_mutation_receipts",
    "rw0_authority_verification_observations",
    "rw0_subordinate_authorization_proposals",
    "rw0_custody_availability_observations",
    "rw0_retrieval_capability_event_observations",
    "rw0_remote_host_readiness_observations",
    "rw0_effect_host_qualifications",
    "rw0_worker_mechanism_capability_declarations",
    "rw0_worker_mechanism_capability_observations",
    "rw0_worker_mechanism_capability_qualifications",
    "rw0_wire_cancellation_request_observations",
    "rw0_wire_process_observations",
    "rw0_c2a_worker_observations",
    "rw0_wire_worker_result_bindings",
    "rw0_wire_process_result_classification_bindings",
    "rw0_section41_post_execution_proposal_family_members",
    "rw0_authority_observation_effect_classes",
    "rw0_c2a_worker_observation_evidence_refs",
)
_PROHIBITED_FIXTURE_DEPENDENCY_SEGMENTS = frozenset(
    {
        "c2b_values",
        "c2b_readers",
        "c2b_mutation",
        "c2b3_replay",
    }
)
_PROHIBITED_FIXTURE_DEPENDENCY_DIAGNOSTIC = "prohibited_fixture_dependency"


def _fixture_import_source_bindings(tree: ast.AST) -> tuple[tuple[str, str | None], ...]:
    source_bindings: list[tuple[str, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            source_bindings.extend((alias.name, alias.asname) for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue

        relative_module = f"{'.' * node.level}{node.module or ''}"
        if node.module is not None:
            source_bindings.append((relative_module, None))
        for alias in node.names:
            separator = "." if node.module is not None else ""
            source_bindings.append(
                (f"{relative_module}{separator}{alias.name}", alias.asname)
            )
    return tuple(source_bindings)


def _assert_fixture_import_boundary(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    imported_sources = tuple(
        source_path
        for source_path, _local_binding in _fixture_import_source_bindings(tree)
    )
    if any(
        segment.casefold() in _PROHIBITED_FIXTURE_DEPENDENCY_SEGMENTS
        for source_path in imported_sources
        for segment in source_path.split(".")
        if segment
    ):
        raise AssertionError(_PROHIBITED_FIXTURE_DEPENDENCY_DIAGNOSTIC)
    return imported_sources


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


def test_fixture_has_no_c2b_row_adapter_reader_or_mutation_dependency() -> None:
    source = TEST_FIXTURE_PATH.read_text(encoding="utf-8")
    imported_modules = _assert_fixture_import_boundary(source)
    assert "sqlite3" in imported_modules
    assert "ge_nwp_coordinator.sqlite_migration" in imported_modules
    assert EXPECTED_C2B2_PHYSICAL_TABLES == _C2B2_PHYSICAL_TABLES
    assert EXPECTED_SECTION41_PHYSICAL_TABLES == _SECTION41_PHYSICAL_TABLES
    assert EXPECTED_RW0_C1_PHYSICAL_TABLES == _RW0_C1_PHYSICAL_TABLES
    assert len(EXPECTED_C2B2_PHYSICAL_TABLES) == 19
    assert len(EXPECTED_SECTION41_PHYSICAL_TABLES) == 9
    assert len(EXPECTED_RW0_C1_PHYSICAL_TABLES) == 23
    assert len(set(EXPECTED_C2B2_PHYSICAL_TABLES)) == 19
    assert len(set(EXPECTED_SECTION41_PHYSICAL_TABLES)) == 9
    assert len(set(EXPECTED_RW0_C1_PHYSICAL_TABLES)) == 23
    assert not set(EXPECTED_C2B2_PHYSICAL_TABLES).intersection(
        EXPECTED_SECTION41_PHYSICAL_TABLES
    )
    assert _FIXTURE_EMPTY_PHYSICAL_TABLES == (
        *EXPECTED_C2B2_PHYSICAL_TABLES,
        *EXPECTED_SECTION41_PHYSICAL_TABLES,
        *EXPECTED_RW0_C1_PHYSICAL_TABLES,
    )
    assert len(_FIXTURE_EMPTY_PHYSICAL_TABLES) == 51
    assert len(set(_FIXTURE_EMPTY_PHYSICAL_TABLES)) == 51
    empty_guard_source = inspect.getsource(_require_c2b2_physical_tables_empty_for_test)
    section41_guard_source = inspect.getsource(
        _require_section41_physical_tables_empty_for_test
    )
    rw0_c1_guard_source = inspect.getsource(
        _require_rw0_c1_physical_tables_empty_for_test
    )
    assert empty_guard_source.count('connection.execute(f"SELECT COUNT(*) FROM {table_name}")') == 1
    assert section41_guard_source.count(
        'connection.execute(f"SELECT COUNT(*) FROM {table_name}")'
    ) == 1
    assert rw0_c1_guard_source.count(
        'connection.execute(f"SELECT COUNT(*) FROM {table_name}")'
    ) == 1
    fixture_source = inspect.getsource(make_coherent_transition_fixture_for_test)
    assert fixture_source.count(
        "_require_c2b2_physical_tables_empty_for_test(location)"
    ) == 2
    assert fixture_source.count(
        "_require_section41_physical_tables_empty_for_test(location)"
    ) == 2
    assert fixture_source.count(
        "_require_rw0_c1_physical_tables_empty_for_test(location)"
    ) == 2
    for forbidden in (
        "INSERT INTO development_",
        "UPDATE development_",
        "DELETE FROM development_",
        "apply_development",
        "read_development",
    ):
        assert forbidden not in source


def _assert_prohibited_fixture_dependency(import_statement: str) -> None:
    source = TEST_FIXTURE_PATH.read_text(encoding="utf-8")
    with pytest.raises(AssertionError) as exc_info:
        _assert_fixture_import_boundary(f"{source}\n{import_statement}\n")
    assert str(exc_info.value) == _PROHIBITED_FIXTURE_DEPENDENCY_DIAGNOSTIC
    assert exc_info.value.args == (_PROHIBITED_FIXTURE_DEPENDENCY_DIAGNOSTIC,)


def test_fixture_import_boundary_rejects_ast_import_c2b_values() -> None:
    _assert_prohibited_fixture_dependency("import ge_nwp_coordinator.c2b_values")


def test_fixture_importfrom_rejects_package_alias_c2b_values() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator import c2b_values"
    )


def test_fixture_importfrom_rejects_package_alias_c2b_readers() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator import c2b_readers"
    )


def test_fixture_importfrom_rejects_package_alias_c2b_mutation() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator import c2b_mutation"
    )


def test_fixture_importfrom_rejects_package_alias_c2b3_replay() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator import c2b3_replay"
    )


def test_fixture_importfrom_rejects_aliased_package_member() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator import c2b_values as values_alias"
    )


def test_fixture_importfrom_rejects_aliased_submodule_member() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator.c2b_readers import Reader as ReaderAlias"
    )


def test_fixture_importfrom_rejects_module_none_relative_member() -> None:
    _assert_prohibited_fixture_dependency("from . import c2b_mutation")


def test_fixture_importfrom_rejects_parent_relative_package_member() -> None:
    _assert_prohibited_fixture_dependency(
        "from ..ge_nwp_coordinator import c2b3_replay"
    )


def test_fixture_importfrom_rejects_star_import_from_protected_module() -> None:
    _assert_prohibited_fixture_dependency(
        "from ge_nwp_coordinator.c2b_values import *"
    )


def test_fixture_import_boundary_accepts_current_fixture_source() -> None:
    source = TEST_FIXTURE_PATH.read_text(encoding="utf-8")
    imported_sources = _assert_fixture_import_boundary(source)
    assert "sqlite3" in imported_sources
    assert "ge_nwp_coordinator.sqlite_migration" in imported_sources


def test_fixture_import_boundary_accepts_ordinary_aliased_imports() -> None:
    imported_sources = _assert_fixture_import_boundary(
        "import json.tool as json_tool\n"
        "from pathlib import Path as LocalPath\n"
    )
    assert imported_sources == ("json.tool", "pathlib", "pathlib.Path")


def test_fixture_import_boundary_accepts_benign_near_name_segments() -> None:
    imported_sources = _assert_fixture_import_boundary(
        "import ge_nwp_coordinator.not_c2b_values\n"
        "from ge_nwp_coordinator import my_c2b_values_note as note_alias\n"
        "from . import not_c2b_readers\n"
    )
    assert "ge_nwp_coordinator.not_c2b_values" in imported_sources
    assert "ge_nwp_coordinator.my_c2b_values_note" in imported_sources
    assert ".not_c2b_readers" in imported_sources


def test_fixture_nonempty_c2b_table_rejection_closes_read_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _NonemptyCursor:
        def fetchone(self) -> tuple[int]:
            return (1,)

    class _ReadConnection:
        def __init__(self) -> None:
            self.statements: list[str] = []
            self.closed = False

        def execute(self, statement: str) -> _NonemptyCursor:
            self.statements.append(statement)
            return _NonemptyCursor()

        def close(self) -> None:
            self.closed = True

    connection = _ReadConnection()
    monkeypatch.setattr(
        fixture_module,
        "open_existing_sqlite_connection",
        lambda location, *, read_only: connection,
    )
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "nonempty-c2b-state")

    with pytest.raises(RuntimeError, match="^fixture-c2b2-physical-table-not-empty$"):
        _require_c2b2_physical_tables_empty_for_test(location)

    assert connection.statements == [
        f"SELECT COUNT(*) FROM {EXPECTED_C2B2_PHYSICAL_TABLES[0]}"
    ]
    assert connection.closed is True


def test_fixture_nonempty_section41_table_rejection_closes_read_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _NonemptyCursor:
        def fetchone(self) -> tuple[int]:
            return (1,)

    class _ReadConnection:
        def __init__(self) -> None:
            self.statements: list[str] = []
            self.closed = False

        def execute(self, statement: str) -> _NonemptyCursor:
            self.statements.append(statement)
            return _NonemptyCursor()

        def close(self) -> None:
            self.closed = True

    mutation_calls = 0

    def mutation_forbidden(*args: object, **kwargs: object) -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        raise AssertionError("fixture Section 41 emptiness guard attempted mutation")

    connection = _ReadConnection()
    monkeypatch.setattr(
        fixture_module,
        "open_existing_sqlite_connection",
        lambda location, *, read_only: connection,
    )
    monkeypatch.setattr(fixture_module, "_insert_row_for_test", mutation_forbidden)
    monkeypatch.setattr(
        fixture_module,
        "acquire_sqlite_writer_session",
        mutation_forbidden,
    )
    location = CoordinatorStateLocation.from_trusted_root(
        tmp_path / "nonempty-section41-state"
    )

    with pytest.raises(
        RuntimeError,
        match="^fixture-section41-physical-table-not-empty$",
    ):
        _require_section41_physical_tables_empty_for_test(location)

    assert connection.statements == [
        f"SELECT COUNT(*) FROM {EXPECTED_SECTION41_PHYSICAL_TABLES[0]}"
    ]
    assert connection.closed is True
    assert mutation_calls == 0


def test_base_fixture_uses_current_physical_schema_and_builds_historical_exact_graph(
    tmp_path: Path,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        assert fixture.location.state_root.is_relative_to(tmp_path)
        assert not fixture.location.state_root.is_relative_to(ROOT)
        inspection = validate_database(fixture.location)
        assert inspection.classification is DatabaseClassification.MANAGED
        assert inspection.current_sequence == 5
        assert inspection.latest_sequence == 5
        assert inspection.current_migration_id == "0005_section41_post_execution_proposal_family"

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

        connection = open_existing_sqlite_connection(fixture.location, read_only=True)
        try:
            assert tuple(
                (table_name, connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone())
                for table_name in _FIXTURE_EMPTY_PHYSICAL_TABLES
            ) == tuple(
                (table_name, (0,))
                for table_name in (
                    *EXPECTED_C2B2_PHYSICAL_TABLES,
                    *EXPECTED_SECTION41_PHYSICAL_TABLES,
                    *EXPECTED_RW0_C1_PHYSICAL_TABLES,
                )
            )
        finally:
            connection.close()


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


def test_real_writer_issuance_is_generation_two_and_session_closes_deterministically(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        session = fixture.writer_session
        location = fixture.location
        assert session.active is True
        assert fixture.metadata == session.metadata
        assert fixture.metadata.generation == 2
        assert _writer_generations_for_test(fixture) == (2,)
        assert validate_database(fixture.location).classification is DatabaseClassification.MANAGED
    assert session.active is False
    session.close()
    assert session.active is False

    downstream_session = acquire_sqlite_writer_session(location)
    try:
        assert downstream_session.metadata.generation == 3
    finally:
        downstream_session.close()


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
        "B3c3 rollback-only dry-run runtime remains private",
        "B3c4b now implements private atomic persistence",
        "current cumulative application generation `2`",
            "terminal migration `0004_rw0_c1_durable_evidence`",
        "first acquisition has generation `1` and is closed",
        "retains its second acquisition at generation `2`",
        "next downstream acquisition is therefore generation `3`",
            "All nineteen C2B core tables, all nine cognitive proposal-selection tables, and all twenty-three RW0-C1 tables remain empty",
            "does not populate or consume C2B2, cognitive-selection, or RW0-C1 durable records",
        "does not prove C2B2 row/value, reader, mutation, family replay, or recovery behavior",
    ):
        assert phrase in normalized
    for stale in (
        "generation `1` for a fresh temporary database",
        "No migration 0002 is required for this tests-only tranche",
    ):
        assert stale not in doc


def test_migration_boundary_related_surfaces_and_repo_artifacts_remain_frozen() -> None:
    assert hashlib.sha256(MIGRATION_PATH.read_bytes()).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
        "0004_rw0_c1_durable_evidence.sql",
        "0005_section41_post_execution_proposal_family.sql",
    ]

    source_paths = tuple(
        path
        for path in (ROOT / "src/ge_nwp_coordinator").glob("*.py")
        if path.name != "sqlite_transition_write_contracts.py"
    )
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
