from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator._sqlite_development_author_effect_establishment as runtime
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentConflictReasonV1,
    DevelopmentAuthorEffectEstablishmentConflictV1,
    DevelopmentAuthorEffectEstablishmentResultV1,
    _development_author_effect_establishment_write_plan,
    _development_effect_authorization_safe_binding,
    _development_review_requirement_evidence,
    _development_validation_requirement_evidence,
)
from ge_nwp_coordinator._development_program_initialization_contracts import (
    _development_program_initialization_write_plan,
)
from ge_nwp_coordinator._sqlite_development_author_effect_establishment import (
    _reduce_development_author_effect_establishment_command,
)
from ge_nwp_coordinator._sqlite_development_program_initialization import (
    _reduce_development_program_initialization_command,
)
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CeilingsV1,
    WorkSpecV1,
)
from ge_nwp_coordinator.global_stop import GlobalStopOperatorDecision
from ge_nwp_coordinator.persistence_contracts import (
    global_stop_operator_decision_canonical_digest,
    global_stop_operator_decision_canonical_json,
)
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session


PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
FAMILY_TABLES = (
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_authority_evaluations",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
)


@dataclass
class AuthorEffectFixture:
    location: CoordinatorStateLocation
    writer: object
    work_spec: WorkSpecV1
    command: object
    ingress: dict[str, object]


def make_author_effect_fixture(
    tmp_path: Path,
    *,
    suffix: str = "one",
) -> AuthorEffectFixture:
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
    genesis_command = _reduce_development_program_initialization_command(
        mutation_ref=f"mutation-genesis-{suffix}",
        program_ref=work_spec.program_ref,
        program_version_ref=work_spec.program_version_ref,
        accepted_intent_revision_ref=work_spec.accepted_intent_revision_ref,
        decision_ref=f"decision-{suffix}",
        preassigned_semantic_attempt_ref=f"semantic-attempt-{suffix}",
        preassigned_candidate_ref=f"candidate-{suffix}",
        coding_global_stop_ref="global-stop-clear",
        coding_global_stop_version=0,
        source_intent_ref=f"source-intent-{suffix}",
        source_intent_digest="1" * 64,
        work_spec=work_spec,
    )
    writer = acquire_sqlite_writer_session(location)
    genesis_result = writer._apply_development_program_initialization(genesis_command)
    genesis_plan = _development_program_initialization_write_plan(
        genesis_command,
        genesis_result.transaction_timestamp,
    )
    aggregate = CeilingsV1.create(
        max_active_invocations=1,
        max_candidate_bytes=1_048_576,
        max_changed_files=3,
        max_cost_microusd=100_000,
        max_cpu_seconds=600,
        max_deliveries=3,
        max_deployments=0,
        max_local_commits=1,
        max_memory_bytes=2_147_483_648,
        max_merges=0,
        max_model_input_tokens=200_000,
        max_model_output_tokens=50_000,
        max_pull_requests=0,
        max_pushes=0,
        max_wall_seconds=1_800,
    )
    effect = CeilingsV1.create(
        **{
            **aggregate.to_mapping(),
            "max_deliveries": 1,
            "max_local_commits": 0,
        }
    )
    attempt_fence = AttemptFenceV1.create(
        attempt_fence_ref=f"attempt-fence-{suffix}",
        parent_standing_grant_ref=f"standing-grant-{suffix}",
        parent_standing_grant_digest="3" * 64,
        attempt_authorization_ref=f"attempt-authorization-{suffix}",
        attempt_authorization_digest="4" * 64,
        program_ref=work_spec.program_ref,
        program_version_ref=work_spec.program_version_ref,
        accepted_intent_revision_ref=work_spec.accepted_intent_revision_ref,
        work_item_ref=work_spec.work_item_ref,
        work_item_revision_ref=work_spec.work_item_revision_ref,
        semantic_attempt_ref=f"semantic-attempt-{suffix}",
        repository_ref=work_spec.repository_ref,
        base_git_oid=work_spec.base_git_oid,
        path_ceiling=list(PATHS),
        allowed_effect_classes=[
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate",
        ],
        aggregate_ceilings=aggregate,
        expires_at="2099-01-01T00:00:00Z",
        global_stop_ref="global-stop-clear",
        global_stop_version=0,
    )
    validation = _development_validation_requirement_evidence(
        requirement_ref=work_spec.validation_requirement_ref,
        requirement_digest="6" * 64,
        work_spec_ref=work_spec.work_spec_ref,
        work_spec_digest=work_spec.work_spec_digest,
    )
    review = _development_review_requirement_evidence(
        requirement_ref=work_spec.review_requirement_ref,
        requirement_digest="7" * 64,
        work_spec_ref=work_spec.work_spec_ref,
        work_spec_digest=work_spec.work_spec_digest,
    )
    binding = _development_effect_authorization_safe_binding(
        parent_standing_grant_ref=attempt_fence.parent_standing_grant_ref,
        parent_standing_grant_digest=attempt_fence.parent_standing_grant_digest,
        effect_authorization_ref=f"effect-authorization-{suffix}",
        effect_authorization_digest="5" * 64,
        attempt_fence_ref=attempt_fence.attempt_fence_ref,
        attempt_fence_digest=attempt_fence.attempt_fence_digest,
        semantic_attempt_ref=attempt_fence.semantic_attempt_ref,
        effect_intent_ref=f"effect-intent-{suffix}",
        effect_class="author_candidate",
        path_ceiling=attempt_fence.path_ceiling,
        effect_ceilings=effect,
        expires_at="2099-01-01T00:00:00Z",
        global_stop_ref=attempt_fence.global_stop_ref,
        global_stop_version=attempt_fence.global_stop_version,
    )
    ingress: dict[str, object] = {
        "mutation_ref": f"mutation-author-{suffix}",
        "program_ref": work_spec.program_ref,
        "program_version_ref": work_spec.program_version_ref,
        "program_version_number": 1,
        "accepted_intent_revision_ref": work_spec.accepted_intent_revision_ref,
        "work_item_ref": work_spec.work_item_ref,
        "work_item_revision_ref": work_spec.work_item_revision_ref,
        "basis_decision_ref": f"decision-{suffix}",
        "basis_decision_digest": genesis_plan.initialize_decision.decision_digest,
        "semantic_attempt_ref": f"semantic-attempt-{suffix}",
        "candidate_ref": f"candidate-{suffix}",
        "attempt_number": 1,
        "attempt_fence_ref": attempt_fence.attempt_fence_ref,
        "effect_intent_ref": f"effect-intent-{suffix}",
        "effect_fence_ref": f"effect-fence-{suffix}",
        "command_ref": f"command-{suffix}",
        "authority_evaluation_ref": f"authority-evaluation-{suffix}",
        "delivery_attempt_ref": f"delivery-attempt-{suffix}",
        "adapter_safe_correlation_ref": f"adapter-correlation-{suffix}",
        "coding_global_stop_ref": "global-stop-clear",
        "coding_global_stop_version": 0,
        "work_spec": work_spec,
        "validation_requirement_evidence": validation,
        "review_requirement_evidence": review,
        "attempt_fence": attempt_fence,
        "effect_authorization_safe_binding": binding,
    }
    command = _reduce_development_author_effect_establishment_command(**ingress)
    return AuthorEffectFixture(location, writer, work_spec, command, ingress)


def family_counts(location: CoordinatorStateLocation) -> dict[str, int]:
    connection = sqlite3.connect(location.database_path)
    try:
        return {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in FAMILY_TABLES
        }
    finally:
        connection.close()


def _insert_semantic_attempt_collision(fixture: AuthorEffectFixture) -> None:
    plan = _development_author_effect_establishment_write_plan(
        fixture.command,
        "2026-08-22T12:34:56Z",
    )
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.execute(
            runtime._SEMANTIC_ATTEMPT_INSERT,
            tuple(plan.semantic_attempt._values),
        )
        try:
            assert cursor.rowcount == 1
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()


def _command_for_active_global_stop(fixture: AuthorEffectFixture) -> object:
    original = fixture.command.attempt_fence
    attempt_fence = AttemptFenceV1.create(
        attempt_fence_ref=original.attempt_fence_ref,
        parent_standing_grant_ref=original.parent_standing_grant_ref,
        parent_standing_grant_digest=original.parent_standing_grant_digest,
        attempt_authorization_ref=original.attempt_authorization_ref,
        attempt_authorization_digest=original.attempt_authorization_digest,
        program_ref=original.program_ref,
        program_version_ref=original.program_version_ref,
        accepted_intent_revision_ref=original.accepted_intent_revision_ref,
        work_item_ref=original.work_item_ref,
        work_item_revision_ref=original.work_item_revision_ref,
        semantic_attempt_ref=original.semantic_attempt_ref,
        repository_ref=original.repository_ref,
        base_git_oid=original.base_git_oid,
        path_ceiling=list(original.path_ceiling),
        allowed_effect_classes=list(original.allowed_effect_classes),
        aggregate_ceilings=original.aggregate_ceilings,
        expires_at=original.expires_at,
        global_stop_ref="active-global-stop",
        global_stop_version=1,
    )
    original_binding = fixture.command.effect_authorization_safe_binding
    binding = _development_effect_authorization_safe_binding(
        parent_standing_grant_ref=original_binding.parent_standing_grant_ref,
        parent_standing_grant_digest=original_binding.parent_standing_grant_digest,
        effect_authorization_ref=original_binding.effect_authorization_ref,
        effect_authorization_digest=original_binding.effect_authorization_digest,
        attempt_fence_ref=attempt_fence.attempt_fence_ref,
        attempt_fence_digest=attempt_fence.attempt_fence_digest,
        semantic_attempt_ref=original_binding.semantic_attempt_ref,
        effect_intent_ref=original_binding.effect_intent_ref,
        effect_class=original_binding.effect_class,
        path_ceiling=original_binding.path_ceiling,
        effect_ceilings=original_binding.effect_ceilings,
        expires_at=original_binding.expires_at,
        global_stop_ref="active-global-stop",
        global_stop_version=1,
    )
    ingress = dict(fixture.ingress)
    ingress.update(
        {
            "coding_global_stop_ref": "active-global-stop",
            "coding_global_stop_version": 1,
            "attempt_fence": attempt_fence,
            "effect_authorization_safe_binding": binding,
        }
    )
    return _reduce_development_author_effect_establishment_command(**ingress)


def _install_active_global_stop(fixture: AuthorEffectFixture) -> None:
    decision = GlobalStopOperatorDecision(
        decision_ref="active-global-stop-decision",
        authorized=True,
        reason="accepted",
    )
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO global_stop_operator_decision_receipts "
            "(decision_ref, authorized, reason, schema_id, canonical_json, "
            "canonical_digest, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                decision.decision_ref,
                1,
                decision.reason,
                decision.schema_id,
                global_stop_operator_decision_canonical_json(decision),
                global_stop_operator_decision_canonical_digest(decision),
                "2098-01-02T03:04:05Z",
            ),
        )
        cursor = connection.execute(
            "UPDATE global_stop_current SET version = ?, active = ?, stop_id = ?, "
            "reason_class = ?, issuer_ref = ?, issued_at = ?, "
            "operator_decision_ref = ?, updated_at = ? WHERE singleton_id = 1",
            (
                1,
                1,
                "active-global-stop",
                "operator_stop",
                "operator-test",
                "2098-01-02T03:04:05Z",
                decision.decision_ref,
                "2098-01-02T03:04:05Z",
            ),
        )
        try:
            assert cursor.rowcount == 1
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()


def test_real_private_path_persists_exact_ten_row_family_and_replays(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path)
    try:
        committed = fixture.writer._establish_development_author_effect_intent(
            **fixture.ingress
        )
        assert type(committed) is DevelopmentAuthorEffectEstablishmentResultV1
        assert committed.disposition == "committed"
        assert family_counts(fixture.location) == dict.fromkeys(FAMILY_TABLES, 1)

        replay = fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
        assert type(replay) is DevelopmentAuthorEffectEstablishmentResultV1
        assert replay.disposition == "exact_replay"
        assert replay.identity_mapping() | {"disposition": "committed"} == (
            committed.identity_mapping()
        )
        assert family_counts(fixture.location) == dict.fromkeys(FAMILY_TABLES, 1)
    finally:
        fixture.writer.close()


def test_real_write_order_has_one_commit_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="ordered")
    statements: list[str] = []
    commits = 0
    original_insert = runtime._execute_author_effect_insert
    original_commit = transaction._ControllerConnectionScope.commit

    def recording_insert(
        connection: sqlite3.Connection,
        statement: str,
        parameters: tuple[object, ...],
    ) -> None:
        statements.append(statement)
        original_insert(connection, statement, parameters)

    def recording_commit(scope: object) -> object:
        nonlocal commits
        commits += 1
        return original_commit(scope)

    monkeypatch.setattr(runtime, "_execute_author_effect_insert", recording_insert)
    monkeypatch.setattr(
        transaction._ControllerConnectionScope,
        "commit",
        recording_commit,
    )
    try:
        result = fixture.writer._establish_development_author_effect_intent(
            **fixture.ingress
        )
        assert type(result) is DevelopmentAuthorEffectEstablishmentResultV1
        assert statements == list(runtime._AUTHOR_EFFECT_INSERT_STATEMENTS)
        assert commits == 1
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("failure_ordinal", (1, 5, 10))
def test_early_middle_and_late_insert_failures_rollback_every_family_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_ordinal: int,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix=f"rollback-{failure_ordinal}")
    calls = 0
    original_insert = runtime._execute_author_effect_insert

    def failing_insert(
        connection: sqlite3.Connection,
        statement: str,
        parameters: tuple[object, ...],
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == failure_ordinal:
            raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)
        original_insert(connection, statement, parameters)

    monkeypatch.setattr(runtime, "_execute_author_effect_insert", failing_insert)
    try:
        with pytest.raises(SQLiteMutationStoreError) as captured:
            fixture.writer._establish_development_author_effect_intent(
                **fixture.ingress
            )
        assert captured.value.error_class == "mutation_failed"
        assert calls == failure_ordinal
        assert family_counts(fixture.location) == dict.fromkeys(FAMILY_TABLES, 0)
        connection = sqlite3.connect(fixture.location.database_path)
        try:
            assert connection.execute(
                "SELECT count(*) FROM development_mutation_receipts "
                "WHERE mutation_ref = ?",
                (fixture.command.mutation_ref,),
            ).fetchone() == (0,)
        finally:
            connection.close()
    finally:
        fixture.writer.close()


def test_receipt_first_replay_and_mutation_conflict_do_not_read_current_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="receipt-first")
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)

        def forbidden_stop_read(capability: object) -> object:
            raise AssertionError("receipt path consulted current global stop")

        monkeypatch.setattr(runtime, "_read_global_stop_current", forbidden_stop_read)
        replay = fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
        assert replay.disposition == "exact_replay"

        changed = dict(fixture.ingress)
        changed["adapter_safe_correlation_ref"] = "adapter-correlation-other"
        conflict_command = _reduce_development_author_effect_establishment_command(
            **changed
        )
        conflict = (
            fixture.writer._run_development_author_effect_establishment_operation(
                command=conflict_command,
                recovery=False,
            )
        )
        assert type(conflict) is DevelopmentAuthorEffectEstablishmentConflictV1
        assert (
            conflict.reason
            is DevelopmentAuthorEffectEstablishmentConflictReasonV1.MUTATION_REF_REUSE_CONFLICT
        )
    finally:
        fixture.writer.close()


def test_real_semantic_identity_collision_is_bounded_and_non_durable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="semantic-collision")
    _insert_semantic_attempt_collision(fixture)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: (_ for _ in ()).throw(
            AssertionError("identity collision reached the fresh-plan clock")
        ),
    )
    try:
        result = fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
        assert type(result) is DevelopmentAuthorEffectEstablishmentConflictV1
        assert (
            result.reason
            is DevelopmentAuthorEffectEstablishmentConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
        )
        assert family_counts(fixture.location) == {
            **dict.fromkeys(FAMILY_TABLES, 0),
            "development_semantic_attempts": 1,
        }
        connection = sqlite3.connect(fixture.location.database_path)
        try:
            assert connection.execute(
                "SELECT count(*) FROM development_mutation_receipts WHERE mutation_ref = ?",
                (fixture.command.mutation_ref,),
            ).fetchone() == (0,)
        finally:
            connection.close()
    finally:
        fixture.writer.close()


def test_global_stop_version_then_active_precede_lower_identity_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="global-stop-precedence")
    active_command = _command_for_active_global_stop(fixture)
    _insert_semantic_attempt_collision(fixture)
    _install_active_global_stop(fixture)

    def forbidden_lower_check(*args: object, **kwargs: object) -> object:
        raise AssertionError("global-stop conflict reached a lower-priority check")

    monkeypatch.setattr(
        runtime,
        "_genesis_basis_is_current_and_exact",
        forbidden_lower_check,
    )
    monkeypatch.setattr(
        runtime,
        "_selected_author_effect_identity_exists",
        forbidden_lower_check,
    )
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        forbidden_lower_check,
    )
    try:
        version_conflict = (
            fixture.writer._run_development_author_effect_establishment_operation(
                command=fixture.command,
                recovery=False,
            )
        )
        assert type(version_conflict) is DevelopmentAuthorEffectEstablishmentConflictV1
        assert (
            version_conflict.reason
            is DevelopmentAuthorEffectEstablishmentConflictReasonV1.GLOBAL_STOP_VERSION_CONFLICT
        )

        active_conflict = (
            fixture.writer._run_development_author_effect_establishment_operation(
                command=active_command,
                recovery=False,
            )
        )
        assert type(active_conflict) is DevelopmentAuthorEffectEstablishmentConflictV1
        assert (
            active_conflict.reason
            is DevelopmentAuthorEffectEstablishmentConflictReasonV1.CODING_GLOBAL_STOP_ACTIVE
        )
        assert family_counts(fixture.location) == {
            **dict.fromkeys(FAMILY_TABLES, 0),
            "development_semantic_attempts": 1,
        }
    finally:
        fixture.writer.close()
