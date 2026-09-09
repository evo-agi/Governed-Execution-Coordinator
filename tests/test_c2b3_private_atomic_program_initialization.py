from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sqlite3

import pytest

import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator._development_program_initialization_contracts import (
    DevelopmentProgramInitializationCommandV1,
    DevelopmentProgramInitializationConflictReasonV1,
    DevelopmentProgramInitializationConflictV1,
    DevelopmentProgramInitializationResultV1,
)
from ge_nwp_coordinator._sqlite_development_program_initialization import (
    _reduce_development_program_initialization_command,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"
PLANNING_PATH = ROOT / ".docs" / "c2b3-program-initialization.md"
VS1B_SECTION_HEADING = "## 38. Coordinator VS1B Route-Neutral Program Genesis"
C2B3C_SECTION_HEADING = "## 39. Coordinator C2B3C Author-Effect Contract Freeze"
VS1B_OWNER_BEGIN_MARKER = (
    "<!-- COORDINATOR_VS1B_ROUTE_NEUTRAL_PROGRAM_GENESIS_BEGIN -->"
)
VS1B_OWNER_END_MARKER = (
    "<!-- COORDINATOR_VS1B_ROUTE_NEUTRAL_PROGRAM_GENESIS_END -->"
)
HISTORICAL_PLANNING_END_MARKER = "<!-- C2B3A_PLANNING_PROJECTION_END -->"
VS1B_STATUS_BEGIN_MARKER = (
    "<!-- COORDINATOR_VS1B_IMPLEMENTED_CURRENT_STATUS_BEGIN -->"
)
VS1B_STATUS_END_MARKER = "<!-- COORDINATOR_VS1B_IMPLEMENTED_CURRENT_STATUS_END -->"
EXPECTED_VS1B_OWNER_PREFIX = """## 38. Coordinator VS1B Route-Neutral Program Genesis

This section is the finite owner for the VS1B private implementation. It
re-adopts the Section-35 single-work-item command, projections, row values,
digests, result projection, and conflict algebra except where the explicit
cross-session gate below supersedes an initialization-only X-gate statement.
The new source bytes are implementation evidence pending a fresh independent
audit; this section is not an audit acceptance claim.

<!-- COORDINATOR_VS1B_ROUTE_NEUTRAL_PROGRAM_GENESIS_BEGIN -->
"""
EXPECTED_VS1B_OWNER_KEYS = (
    "status",
    "safe_values",
    "route_neutrality",
    "fresh_transaction",
    "apply_order",
    "receipt_first",
    "historical_head_relational_verification",
    "read_only_recovery",
    "cross_session_gate",
    "finite_X_gate_supersession",
    "safe_command_and_privacy",
    "absent",
    "non_widening",
)
PATHS = [
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
]
GENESIS_TABLES = (
    "development_program_heads",
    "development_accepted_intent_revisions",
    "development_work_item_heads",
    "development_work_item_revisions",
    "development_decisions",
    "development_program_versions",
    "development_program_version_work_items",
    "development_work_spec_bindings",
    "development_mutation_receipts",
)
ABSENT_TABLES = (
    "development_revision_edges",
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_authority_evaluations",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
)


def _read_current_contract_document(path: Path) -> str:
    assert path in (OWNER_PATH, PLANNING_PATH)
    assert not path.is_symlink()
    assert path.resolve(strict=True) == path
    return path.read_text(encoding="utf-8")


def _vs1b_owner_contract() -> dict[str, object]:
    source = _read_current_contract_document(OWNER_PATH)
    assert source.count(VS1B_SECTION_HEADING) == 1
    assert source.count(C2B3C_SECTION_HEADING) == 1
    assert source.count(VS1B_OWNER_BEGIN_MARKER) == 1
    assert source.count(VS1B_OWNER_END_MARKER) == 1
    section = source.split(VS1B_SECTION_HEADING, 1)[1]
    section, separator, _section_39 = section.partition(C2B3C_SECTION_HEADING)
    assert separator == C2B3C_SECTION_HEADING
    section = VS1B_SECTION_HEADING + section
    assert section.startswith(EXPECTED_VS1B_OWNER_PREFIX)
    before, remainder = section.split(VS1B_OWNER_BEGIN_MARKER, 1)
    payload, after = remainder.split(VS1B_OWNER_END_MARKER, 1)
    assert before + VS1B_OWNER_BEGIN_MARKER + "\n" == EXPECTED_VS1B_OWNER_PREFIX
    assert after == "\n\n"
    lines = payload.strip().splitlines()
    assert len(lines) >= 3
    assert lines[0] == "```python"
    assert lines[-1] == "```"
    value = ast.literal_eval("\n".join(lines[1:-1]))
    assert type(value) is dict
    assert tuple(value) == ("coordinator_vs1b_route_neutral_program_genesis",)
    contract = value["coordinator_vs1b_route_neutral_program_genesis"]
    assert type(contract) is dict
    assert tuple(contract) == EXPECTED_VS1B_OWNER_KEYS
    return contract


def _vs1b_current_status_text() -> str:
    source = _read_current_contract_document(PLANNING_PATH)
    assert source.count(HISTORICAL_PLANNING_END_MARKER) == 1
    assert source.count(VS1B_STATUS_BEGIN_MARKER) == 1
    assert source.count(VS1B_STATUS_END_MARKER) == 1
    historical, current = source.split(VS1B_STATUS_BEGIN_MARKER, 1)
    assert historical.endswith(HISTORICAL_PLANNING_END_MARKER + "\n")
    status, after = current.split(VS1B_STATUS_END_MARKER, 1)
    assert after == "\n"
    return " ".join(status.split())


@dataclass
class GenesisFixture:
    location: CoordinatorStateLocation
    writer_session: object
    work_spec: WorkSpecV1
    command: DevelopmentProgramInitializationCommandV1


def make_genesis_fixture(tmp_path: Path, *, suffix: str = "one") -> GenesisFixture:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / f"state-{suffix}")
    initialize_database(location)
    work_spec = WorkSpecV1.create(
        work_spec_ref=f"work-spec-{suffix}",
        program_ref=f"program-{suffix}",
        program_version_ref=f"program-version-{suffix}",
        accepted_intent_revision_ref=f"accepted-intent-{suffix}",
        work_item_ref=f"work-item-{suffix}",
        work_item_revision_ref=f"work-item-revision-{suffix}",
        repository_ref=f"repository-{suffix}",
        base_git_oid="2" * 40,
        authorized_paths=list(PATHS),
        objective="PRIVATE OBJECTIVE SENTINEL",
        requirements=["PRIVATE REQUIREMENT SENTINEL"],
        exclusions=["PRIVATE EXCLUSION SENTINEL"],
        validation_requirement_ref=f"validation-{suffix}",
        review_requirement_ref=f"review-{suffix}",
    )
    command = command_from_work_spec(work_spec, suffix=suffix)
    return GenesisFixture(
        location=location,
        writer_session=acquire_sqlite_writer_session(location),
        work_spec=work_spec,
        command=command,
    )


def command_from_work_spec(
    work_spec: WorkSpecV1,
    *,
    suffix: str,
    mutation_suffix: str | None = None,
    decision_suffix: str | None = None,
    attempt_suffix: str | None = None,
    candidate_suffix: str | None = None,
    stop_ref: str = "global-stop-clear",
    stop_version: int = 0,
) -> DevelopmentProgramInitializationCommandV1:
    mutation_part = mutation_suffix if mutation_suffix is not None else suffix
    decision_part = decision_suffix if decision_suffix is not None else suffix
    attempt_part = attempt_suffix if attempt_suffix is not None else suffix
    candidate_part = candidate_suffix if candidate_suffix is not None else suffix
    return _reduce_development_program_initialization_command(
        mutation_ref=f"mutation-{mutation_part}",
        program_ref=work_spec.program_ref,
        program_version_ref=work_spec.program_version_ref,
        accepted_intent_revision_ref=work_spec.accepted_intent_revision_ref,
        decision_ref=f"decision-{decision_part}",
        preassigned_semantic_attempt_ref=f"semantic-attempt-{attempt_part}",
        preassigned_candidate_ref=f"candidate-{candidate_part}",
        coding_global_stop_ref=stop_ref,
        coding_global_stop_version=stop_version,
        source_intent_ref=f"source-intent-{suffix}",
        source_intent_digest="1" * 64,
        work_spec=work_spec,
    )


def table_counts(location: CoordinatorStateLocation) -> dict[str, int]:
    connection = sqlite3.connect(location.database_path)
    try:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (*GENESIS_TABLES, *ABSENT_TABLES)
        }
    finally:
        connection.close()


def test_fresh_program_genesis_commits_exactly_nine_rows_and_no_later_rows(
    tmp_path: Path,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    try:
        result = fixture.writer_session._apply_development_program_initialization(
            fixture.command
        )
        assert type(result) is DevelopmentProgramInitializationResultV1
        assert result.disposition == "committed"
        assert result.command_digest == fixture.command.command_digest
        assert result.preassigned_semantic_attempt_ref == "semantic-attempt-one"
        assert result.preassigned_candidate_ref == "candidate-one"
        counts = table_counts(fixture.location)
        assert {table: counts[table] for table in GENESIS_TABLES} == {
            table: 1 for table in GENESIS_TABLES
        }
        assert {table: counts[table] for table in ABSENT_TABLES} == {
            table: 0 for table in ABSENT_TABLES
        }
    finally:
        fixture.writer_session.close()


def test_receipt_first_exact_replay_does_not_read_stop_or_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    try:
        committed = fixture.writer_session._apply_development_program_initialization(
            fixture.command
        )
        before = table_counts(fixture.location)

        def forbidden(*args: object, **kwargs: object) -> object:
            raise AssertionError("receipt replay crossed a fresh-only boundary")

        import ge_nwp_coordinator._sqlite_development_program_initialization as initialization_module

        monkeypatch.setattr(initialization_module, "_read_global_stop_current", forbidden)
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", forbidden)
        replay = fixture.writer_session._apply_development_program_initialization(
            fixture.command
        )
        assert type(committed) is DevelopmentProgramInitializationResultV1
        assert type(replay) is DevelopmentProgramInitializationResultV1
        assert replay.disposition == "exact_replay"
        assert replay.transaction_timestamp == committed.transaction_timestamp
        assert table_counts(fixture.location) == before
    finally:
        fixture.writer_session.close()


def test_mutation_ref_reuse_precedes_stop_and_semantic_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    try:
        fixture.writer_session._apply_development_program_initialization(fixture.command)
        changed = command_from_work_spec(
            fixture.work_spec,
            suffix="one",
            candidate_suffix="changed",
        )

        def forbidden(*args: object, **kwargs: object) -> object:
            raise AssertionError("mutation-ref conflict disclosed later state")

        import ge_nwp_coordinator._sqlite_development_program_initialization as initialization_module

        monkeypatch.setattr(initialization_module, "_read_global_stop_current", forbidden)
        result = fixture.writer_session._apply_development_program_initialization(changed)
        assert type(result) is DevelopmentProgramInitializationConflictV1
        assert (
            result.reason
            is DevelopmentProgramInitializationConflictReasonV1.MUTATION_REF_REUSE_CONFLICT
        )
    finally:
        fixture.writer_session.close()


def test_fresh_stop_version_and_semantic_identity_conflicts_write_nothing(
    tmp_path: Path,
) -> None:
    stop_fixture = make_genesis_fixture(tmp_path, suffix="stop")
    try:
        wrong_stop = command_from_work_spec(
            stop_fixture.work_spec,
            suffix="stop",
            stop_version=1,
        )
        before = table_counts(stop_fixture.location)
        stop_result = stop_fixture.writer_session._apply_development_program_initialization(
            wrong_stop
        )
        assert type(stop_result) is DevelopmentProgramInitializationConflictV1
        assert (
            stop_result.reason
            is DevelopmentProgramInitializationConflictReasonV1.GLOBAL_STOP_VERSION_CONFLICT
        )
        assert table_counts(stop_fixture.location) == before
    finally:
        stop_fixture.writer_session.close()

    identity_fixture = make_genesis_fixture(tmp_path, suffix="identity")
    try:
        identity_fixture.writer_session._apply_development_program_initialization(
            identity_fixture.command
        )
        colliding = command_from_work_spec(
            identity_fixture.work_spec,
            suffix="identity",
            mutation_suffix="other",
            decision_suffix="other",
            attempt_suffix="other",
            candidate_suffix="other",
        )
        before = table_counts(identity_fixture.location)
        collision = identity_fixture.writer_session._apply_development_program_initialization(
            colliding
        )
        assert type(collision) is DevelopmentProgramInitializationConflictV1
        assert (
            collision.reason
            is DevelopmentProgramInitializationConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
        )
        assert table_counts(identity_fixture.location) == before
    finally:
        identity_fixture.writer_session.close()


def test_safe_command_reconstruction_has_equal_value_not_identity(tmp_path: Path) -> None:
    fixture = make_genesis_fixture(tmp_path)
    try:
        reconstructed_work_spec = WorkSpecV1.from_mapping(
            fixture.work_spec.to_mapping()
        )
        reconstructed = command_from_work_spec(
            reconstructed_work_spec,
            suffix="one",
        )
        assert reconstructed is not fixture.command
        assert reconstructed == fixture.command
        result = fixture.writer_session._apply_development_program_initialization(
            reconstructed
        )
        assert type(result) is DevelopmentProgramInitializationResultV1
        assert result.disposition == "committed"
    finally:
        fixture.writer_session.close()


def test_section_38_owns_exact_vs1b_route_neutral_genesis_contract() -> None:
    value = _vs1b_owner_contract()
    assert value["status"] == (
        "implementation evidence pending fresh independent audit"
    )
    assert value["safe_values"] == (
        "DevelopmentAcceptedIntentSafeProjectionV1",
        "DevelopmentProgramInitializationCommandV1",
        "DevelopmentProgramInitializationResultV1",
        "DevelopmentProgramInitializationConflictReasonV1",
        "DevelopmentProgramInitializationConflictV1",
        "DevelopmentProgramInitializationRecoveryDispositionV1",
        "DevelopmentProgramInitializationRecoveryResultV1",
    )
    assert value["route_neutrality"] == {
        "adapter_host_transport_endpoint_or_route_field": False,
        "external_request_or_IO": False,
        "Git_effect": False,
    }
    assert value["fresh_transaction"]["row_order"] == (
        "development_program_heads",
        "development_accepted_intent_revisions",
        "development_work_item_heads",
        "development_work_item_revisions",
        "development_decisions",
        "development_program_versions",
        "development_program_version_work_items",
        "development_work_spec_bindings",
        "development_mutation_receipts",
    )
    assert value["fresh_transaction"]["graph_entries"] == (
        (0, "program_head_postimage", 0, "program_ref"),
        (1, "accepted_intent_revision", 0, "accepted_intent_revision_ref"),
        (2, "initialize_decision", 0, "decision_ref"),
        (3, "program_version", 0, "program_version_ref"),
        (4, "work_item_head_postimage", 0, "work_item_ref"),
        (5, "work_item_revision", 0, "work_item_revision_ref"),
        (6, "program_version_work_item", 0, "work_item_ref"),
        (7, "work_spec_binding", 0, "work_spec_ref"),
    )
    assert value["fresh_transaction"]["receipt_is_graph_envelope_not_entry"] is True
    assert value["apply_order"] == (
        "writer_fencing",
        "receipt_lookup",
        "current_coding_global_stop_read",
        "expected_stop_ref_and_version_comparison",
        "active_stop_rejection",
        "identity_and_collision_checks",
    )
    assert value["read_only_recovery"]["dispositions"] == (
        "committed_exact",
        "definitely_not_committed",
        "unresolved",
    )
    relation = value["historical_head_relational_verification"]
    assert relation["genesis_postimages_remain_receipt_graph_members"] is True
    assert relation["current_advanced_heads_replace_genesis_postimages"] is False
    assert relation["genesis_current_ref_reuses_already_verified_immutable_row"] is True
    assert relation["later_current_ref_uses_family_local_bounded_LIMIT_2_read"] is True
    assert relation["program_current_relation"] == (
        "referenced_version exists exactly once and validates",
        "referenced_version.program_ref == current_head.program_ref == command.program_ref",
        "referenced_version.program_version_ref == current_head.current_program_version_ref",
        "referenced_version.program_version_number == current_head.current_program_version_number",
    )
    assert relation["work_current_relation"] == (
        "referenced_revision exists exactly once and validates",
        "referenced_revision.program_ref == current_head.program_ref == command.program_ref",
        "referenced_revision.work_item_ref == current_head.work_item_ref == command.work_spec_safe_projection.work_item_ref",
        "referenced_revision.work_item_revision_ref == current_head.current_work_item_revision_ref",
        "referenced_revision.work_item_revision_number == current_head.current_work_item_revision_number",
    )
    assert relation["coherent_later_apply"] == "original exact_replay"
    assert relation["coherent_later_recovery"] == "committed_exact"
    assert relation["contradictory_apply"] == "database_integrity_failure"
    assert relation["contradictory_recovery"] == "unresolved"
    assert relation["contradiction_calls_clock_writes_or_COMMIT"] is False
    privacy = value["safe_command_and_privacy"]
    assert privacy["supplied_refs_exactly_validated_before_WorkSpec_comparison"] is True
    assert privacy["caller_comparison_string_or_repr_method_before_rejection"] is False
    assert {
        "worker",
        "route selection",
        "external I/O",
        "Git effect",
        "bootstrap latch",
        "automatic semantic retry",
    }.issubset(value["absent"])
    assert value["non_widening"] == {
        "application_generation": 2,
        "terminal_migration": "0002_development_program_and_effect_state",
        "migration_0003": False,
        "schema_change": False,
        "public_StateStore_or_WriterSession_change": False,
        "package_export": False,
    }


def test_section_38_finitely_corrects_x_gate_without_weakening_old_x() -> None:
    value = _vs1b_owner_contract()
    gate = value["cross_session_gate"]
    assert gate["rule"] == (
        "successful acquisition and fencing of a fresh concrete SQLite writer session"
    )
    assert gate["successful_fresh_acquisition_proves_old_resource_X"] is False
    assert "after H2 and before old T1/X" in gate["same_process"]
    assert "after L1 kernel-lock release" in gate["different_process"]
    assert gate["old_resource_or_session_received_as_recovery_authority"] is False
    assert gate["active_session_registry_or_process_local_resource_scan"] is False
    assert gate["terminal_witness_cross_session_proof_or_durable_gate"] is False
    supersession = value["finite_X_gate_supersession"]
    assert supersession["old_resource_X_remains_local_terminal_truth"] is True
    assert supersession["preserves_cleanup_order"] == (
        "P0", "C1", "C2", "R1", "R2", "R3", "L1", "H1", "H2", "T1", "H3"
    )
    assert supersession["transition_and_global_stop_behavior_changed"] is False


def test_vs1b_current_status_supersedes_historical_planning_labels() -> None:
    status = _vs1b_current_status_text()
    for required in (
        "retained as historical contract and planning evidence",
        "not current implementation claims",
        "route-neutral, single-work-item program-genesis implementation",
        "not proof of the old resource's T1/X state",
        "after H2 and before old T1",
        "after L1 kernel-lock release",
        "immutable row named by its current ref exists exactly once",
        "does not replace its genesis postimage",
        "database_integrity_failure` for apply and `unresolved` for recovery",
        "scalar refs are exactly validated before any comparison",
        "no public API or package export",
        "restart-safe command custody",
        "current committed private implementation at",
        "327aa4ef6f043a94f700374546fedc456027ae83",
        "exact VS1B pre-commit candidate received externally classified, provenance-bound independent acceptance",
        "post-acceptance commit gate passed",
        "Git owns the commit/ref fact",
        "external evidence rather than Coordinator durable authority",
        "C2B3C is currently an uncommitted contract-freeze candidate awaiting fresh independent re-audit",
        "C2B3D source, worker execution, and production or external effects remain unauthorized",
    ):
        assert required in status
