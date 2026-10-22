"""Real private writer proof for D2 checking effect families."""

from __future__ import annotations

import sqlite3

import pytest

import ge_nwp_coordinator.sqlite_transition_transaction as transaction
import ge_nwp_coordinator._development_effect_row_values as _effect_rows
import ge_nwp_coordinator._development_decision_row_values as _decision_rows
from ge_nwp_coordinator._development_bound_effect_establishment_contracts import (
    DevelopmentBoundEffectEstablishmentConflictReasonV1,
    DevelopmentBoundEffectEstablishmentConflictV1,
    DevelopmentBoundEffectEstablishmentRecoveryDispositionV1,
    _development_bound_effect_authorization_safe_binding,
    _development_bound_effect_establishment_write_plan,
    _reduce_development_bound_effect_establishment_command,
    DevelopmentBoundEffectEstablishmentResultV1,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_bound_effect_contracts import _bound_command


def _original_heads(location: object, handback: object) -> tuple[tuple[object, ...], ...]:
    author = handback.author_command
    connection = sqlite3.connect(location.database_path)
    try:
        return tuple(
            connection.execute(sql, parameters).fetchone()
            for sql, parameters in (
                ("SELECT * FROM development_program_heads WHERE program_ref=?",
                 (author.program_ref,)),
                ("SELECT * FROM development_work_item_heads WHERE work_item_ref=?",
                 (author.work_item_ref,)),
                ("SELECT * FROM development_effect_heads WHERE effect_intent_ref=?",
                 (author.effect_intent_ref,)),
                ("SELECT * FROM development_delivery_heads WHERE effect_intent_ref=?",
                 (author.effect_intent_ref,)),
            )
        )
    finally:
        connection.close()


def test_two_native_bound_effect_families_commit_and_replay() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        original_heads = _original_heads(run.location, run.handback)
        validation = _bound_command(run.handback, work, "validate_candidate")
        review = _bound_command(run.handback, work, "review_candidate")
        for command in (validation, review):
            with acquire_sqlite_writer_session(run.location) as writer:
                result = writer._establish_development_bound_effect_intent(command)
            assert type(result) is DevelopmentBoundEffectEstablishmentResultV1
            assert result.disposition == "committed"
            assert result.command_digest == command.command_digest
        for command in (validation, review):
            with acquire_sqlite_writer_session(run.location) as writer:
                replay = writer._establish_development_bound_effect_intent(command)
            assert type(replay) is DevelopmentBoundEffectEstablishmentResultV1
            assert replay.disposition == "exact_replay"
            assert replay.command_digest == command.command_digest
        assert _original_heads(run.location, run.handback) == original_heads


@pytest.mark.parametrize("effect_class", ("validate_candidate", "review_candidate"))
@pytest.mark.parametrize("commit_reaches_disk", (False, True))
def test_native_bound_effect_commit_uncertainty_is_resolved_without_retry(
    effect_class: str, commit_reaches_disk: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        if effect_class == "review_candidate":
            validation = _bound_command(run.handback, work, "validate_candidate")
            with acquire_sqlite_writer_session(run.location) as writer:
                assert writer._establish_development_bound_effect_intent(
                    validation,
                ).disposition == "committed"
        command = _bound_command(run.handback, work, effect_class)
        original_commit = transaction._commit_transaction
        writes = 0
        original_writes = transaction._execute_development_bound_effect_establishment_writes

        def uncertain_commit(connection: sqlite3.Connection) -> object:
            if commit_reaches_disk:
                assert original_commit(connection) is None
            return transaction._SQLITE_COMMIT_FAILED

        def counted_writes(connection: object, plan: object) -> None:
            nonlocal writes
            writes += 1
            original_writes(connection, plan)

        with monkeypatch.context() as patch:
            patch.setattr(transaction, "_commit_transaction", uncertain_commit)
            patch.setattr(transaction, "_execute_development_bound_effect_establishment_writes", counted_writes)
            with acquire_sqlite_writer_session(run.location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as captured:
                    writer._establish_development_bound_effect_intent(command)
                assert captured.value.error_class == "commit_outcome_unknown"
                assert writer.active is False
        assert writes == 1
        with acquire_sqlite_writer_session(run.location) as writer:
            recovered = writer._resolve_development_bound_effect_establishment_commit_outcome(
                command,
            )
        assert recovered.disposition is (
            DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
            if commit_reaches_disk
            else DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
        assert writes == 1
        connection = sqlite3.connect(run.location.database_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM development_mutation_receipts WHERE mutation_ref=?",
                (command.mutation_ref,),
            ).fetchone()[0]
        finally:
            connection.close()
        assert count == int(commit_reaches_disk)
        if commit_reaches_disk:
            with acquire_sqlite_writer_session(run.location) as writer:
                replay = writer._establish_development_bound_effect_intent(command)
            assert replay.disposition == "exact_replay"
            assert writes == 1

# These fixed whole-second values are independent of the writer's clock helper.
_EQUAL_EXPIRY = "2099-01-01T00:00:00Z"
_NARROW_EXPIRY = "2098-01-01T00:00:00Z"
_PREDECESSOR_TIME = "2097-01-01T00:00:00Z"
_EXPIRY_CASES = (
    ("equal-before", _EQUAL_EXPIRY, "2098-12-31T23:59:59Z", True),
    ("equal-at", _EQUAL_EXPIRY, _EQUAL_EXPIRY, False),
    ("equal-after", _EQUAL_EXPIRY, "2099-01-01T00:00:01Z", False),
    ("narrow-before", _NARROW_EXPIRY, "2097-12-31T23:59:59Z", True),
    ("narrow-at", _NARROW_EXPIRY, _NARROW_EXPIRY, False),
    ("narrow-after", _NARROW_EXPIRY, "2098-01-01T00:00:01Z", False),
)
_TARGETS = (
    ("intent", "development_effect_intents", "effect_intent_ref"),
    ("fence", "development_effect_fences", "effect_fence_ref"),
    ("authority", "development_authority_evaluations", "authority_evaluation_ref"),
    ("delivery", "development_delivery_attempts", "delivery_attempt_ref"),
    ("effect_head", "development_effect_heads", "effect_intent_ref"),
    ("delivery_head", "development_delivery_heads", "effect_intent_ref"),
    ("receipt", "development_mutation_receipts", "mutation_ref"),
)


def _command_with_binding_expiry(handback: object, work: object, effect_class: str, expiry: str) -> object:
    command = _bound_command(handback, work, effect_class)
    if expiry == command.effect_authorization_safe_binding.expires_at:
        return command
    old = command.effect_authorization_safe_binding
    binding = _development_bound_effect_authorization_safe_binding(
        parent_standing_grant_ref=old.parent_standing_grant_ref,
        parent_standing_grant_digest=old.parent_standing_grant_digest,
        effect_authorization_ref=old.effect_authorization_ref,
        effect_authorization_digest=old.effect_authorization_digest,
        attempt_fence_ref=old.attempt_fence_ref,
        attempt_fence_digest=old.attempt_fence_digest,
        semantic_attempt_ref=old.semantic_attempt_ref,
        effect_intent_ref=old.effect_intent_ref,
        effect_class=old.effect_class,
        path_ceiling=old.path_ceiling,
        effect_ceilings=old.effect_ceilings,
        expires_at=expiry,
        global_stop_ref=old.global_stop_ref,
        global_stop_version=old.global_stop_version,
    )
    return _reduce_development_bound_effect_establishment_command(
        mutation_ref=command.mutation_ref,
        effect_class=effect_class,
        effect_intent_ref=command.effect_intent_ref,
        effect_fence_ref=command.effect_fence_ref,
        authority_evaluation_ref=command.authority_evaluation_ref,
        delivery_attempt_ref=command.delivery_attempt_ref,
        adapter_safe_correlation_ref=command.adapter_safe_correlation_ref,
        author_command=handback.author_command,
        selected_disposition=handback.section41_result,
        phase_basis=handback.phase_basis,
        work_spec=work,
        capture=handback.capture,
        capsule_manifest=handback.capsule_manifest,
        requirement_evidence=(handback.author_command.validation_requirement_evidence
                              if effect_class == "validate_candidate"
                              else handback.author_command.review_requirement_evidence),
        effect_authorization_safe_binding=binding,
    )


def _target_family_rows(location: object, command: object) -> dict[str, tuple[dict[str, object], ...]]:
    connection = sqlite3.connect(location.database_path)
    try:
        found = {}
        for label, table, key in _TARGETS:
            cursor = connection.execute(
                f"SELECT * FROM {table} WHERE {key}=?", (getattr(command, key),)
            )
            try:
                columns = tuple(column[0] for column in cursor.description)
                found[label] = tuple(dict(zip(columns, row, strict=True)) for row in cursor.fetchall())
            finally:
                cursor.close()
        return found
    finally:
        connection.close()


def _all_family_rows(location: object) -> tuple[tuple[tuple[object, ...], ...], ...]:
    connection = sqlite3.connect(location.database_path)
    try:
        return tuple(
            tuple(connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall())
            for _label, table, _key in _TARGETS
        )
    finally:
        connection.close()


def _assert_exact_target_family(
    rows: dict[str, tuple[dict[str, object], ...]], command: object, committed_at: str,
) -> None:
    assert all(len(member) == 1 for member in rows.values())
    plan = _development_bound_effect_establishment_write_plan(command, committed_at)
    expected = (
        ("intent", plan.effect_intent, _effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS),
        ("fence", plan.effect_fence, _effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS),
        ("authority", plan.authority_evaluation, _effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS),
        ("delivery", plan.delivery_attempt, _effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS),
        ("effect_head", plan.effect_head, _effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS),
        ("delivery_head", plan.delivery_head, _effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS),
    )
    for label, value, columns in expected:
        assert tuple(rows[label][0][column] for column in columns) == tuple(
            getattr(value, column) for column in columns
        )
    assert tuple(rows["receipt"][0][column] for column in _decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS) == tuple(
        plan.mutation_receipt._values[:19]
    )
    assert rows["intent"][0]["effect_class"] == command.effect_class
    assert rows["intent"][0]["candidate_ref"] == command.candidate_ref
    assert rows["fence"][0]["expires_at"] == command.effect_authorization_safe_binding.expires_at
    assert rows["fence"][0]["attempt_fence_ref"] == command.attempt_fence_ref
    assert rows["authority"][0]["authority_state"] == "pending"
    assert rows["authority"][0]["evaluated_at"] == committed_at
    assert rows["delivery"][0]["delivery_number"] == 1
    assert rows["effect_head"][0]["current_effect_fence_ref"] == command.effect_fence_ref
    assert rows["delivery_head"][0]["current_delivery_attempt_ref"] == command.delivery_attempt_ref
    assert rows["receipt"][0]["command_digest"] == command.command_digest
    assert rows["receipt"][0]["committed_at"] == committed_at


def _establish_review_predecessor(
    run: object, work: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation = _bound_command(run.handback, work, "validate_candidate")
    with monkeypatch.context() as patch:
        patch.setattr(transaction, "_capture_transaction_timestamp", lambda: _PREDECESSOR_TIME)
        with acquire_sqlite_writer_session(run.location) as writer:
            result = writer._establish_development_bound_effect_intent(validation)
    assert type(result) is DevelopmentBoundEffectEstablishmentResultV1
    assert result.disposition == "committed"
    _assert_exact_target_family(_target_family_rows(run.location, validation), validation, _PREDECESSOR_TIME)


@pytest.mark.parametrize(
    "effect_class,case,expiry,clock,commits",
    (
        pytest.param(effect_class, name, expiry, clock, commits, id=f"{effect_class}-{name}")
        for effect_class in ("validate_candidate", "review_candidate")
        for name, expiry, clock, commits in _EXPIRY_CASES
    ),
)
def test_native_bound_effect_strict_expiry_fresh_matrix(
    effect_class: str, case: str, expiry: str, clock: str, commits: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        assert run.handback.author_command.attempt_fence.expires_at == _EQUAL_EXPIRY
        if effect_class == "review_candidate":
            _establish_review_predecessor(run, work, monkeypatch)
        command = _command_with_binding_expiry(run.handback, work, effect_class, expiry)
        assert command.effect_authorization_safe_binding.expires_at == expiry
        assert command.effect_fence.expires_at == expiry
        assert command.effect_authorization_safe_binding.expires_at <= command.effect_fence.expires_at
        assert command.effect_fence.expires_at <= run.handback.author_command.attempt_fence.expires_at
        assert command.computed_digest() == command.command_digest
        target_before = _target_family_rows(run.location, command)
        assert all(not member for member in target_before.values())
        family_before = _all_family_rows(run.location)
        heads_before = _original_heads(run.location, run.handback)
        writes = 0
        original_writes = transaction._execute_development_bound_effect_establishment_writes

        def counted_writes(connection: object, plan: object) -> None:
            nonlocal writes
            writes += 1
            original_writes(connection, plan)

        with monkeypatch.context() as patch:
            patch.setattr(transaction, "_capture_transaction_timestamp", lambda: clock)
            patch.setattr(transaction, "_execute_development_bound_effect_establishment_writes", counted_writes)
            with acquire_sqlite_writer_session(run.location) as writer:
                result = writer._establish_development_bound_effect_intent(command)
        target_after = _target_family_rows(run.location, command)
        assert _original_heads(run.location, run.handback) == heads_before
        if commits:
            assert type(result) is DevelopmentBoundEffectEstablishmentResultV1
            assert result.disposition == "committed"
            assert result.transaction_timestamp == clock
            assert result.command_digest == command.command_digest
            assert writes == 1
            _assert_exact_target_family(target_after, command, clock)
        else:
            assert type(result) is DevelopmentBoundEffectEstablishmentConflictV1
            assert result.reason is DevelopmentBoundEffectEstablishmentConflictReasonV1.CURRENT_STATE_CONFLICT
            assert result.mutation_ref == command.mutation_ref
            assert result.command_digest == command.command_digest
            assert writes == 0
            assert all(not member for member in target_after.values())
            assert _all_family_rows(run.location) == family_before


@pytest.mark.parametrize("effect_class", ("validate_candidate", "review_candidate"))
def test_native_bound_effect_replay_and_recovery_keep_preexpiry_family(
    effect_class: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        if effect_class == "review_candidate":
            _establish_review_predecessor(run, work, monkeypatch)
        command = _bound_command(run.handback, work, effect_class)
        before_expiry = "2098-12-31T23:59:59Z"
        with monkeypatch.context() as patch:
            patch.setattr(transaction, "_capture_transaction_timestamp", lambda: before_expiry)
            with acquire_sqlite_writer_session(run.location) as writer:
                original = writer._establish_development_bound_effect_intent(command)
        assert type(original) is DevelopmentBoundEffectEstablishmentResultV1
        assert original.disposition == "committed"
        _assert_exact_target_family(_target_family_rows(run.location, command), command, before_expiry)
        durable_original = _all_family_rows(run.location)
        target_original = _target_family_rows(run.location, command)
        heads_original = _original_heads(run.location, run.handback)
        for later in (_EQUAL_EXPIRY, "2099-01-01T00:00:01Z"):
            clock_reads = 0
            writes = 0
            original_writes = transaction._execute_development_bound_effect_establishment_writes

            def later_clock() -> str:
                nonlocal clock_reads
                clock_reads += 1
                return later

            def counted_writes(connection: object, plan: object) -> None:
                nonlocal writes
                writes += 1
                original_writes(connection, plan)

            with monkeypatch.context() as patch:
                patch.setattr(transaction, "_capture_transaction_timestamp", later_clock)
                patch.setattr(transaction, "_execute_development_bound_effect_establishment_writes", counted_writes)
                with acquire_sqlite_writer_session(run.location) as writer:
                    replay = writer._establish_development_bound_effect_intent(command)
            assert clock_reads == 1  # The current apply path samples time before receipt lookup.
            assert writes == 0
            assert type(replay) is DevelopmentBoundEffectEstablishmentResultV1
            assert replay.disposition == "exact_replay"
            assert replay.transaction_timestamp == original.transaction_timestamp
            assert replay.command_digest == original.command_digest
            assert _all_family_rows(run.location) == durable_original
            assert _target_family_rows(run.location, command) == target_original
            assert _original_heads(run.location, run.handback) == heads_original

            recovery_clock_reads = 0

            def unused_recovery_clock() -> str:
                nonlocal recovery_clock_reads
                recovery_clock_reads += 1
                return later

            with monkeypatch.context() as patch:
                patch.setattr(transaction, "_capture_transaction_timestamp", unused_recovery_clock)
                with acquire_sqlite_writer_session(run.location) as writer:
                    recovered = writer._resolve_development_bound_effect_establishment_commit_outcome(command)
            assert recovery_clock_reads == 0
            assert recovered.disposition is DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
            assert type(recovered.committed_result) is DevelopmentBoundEffectEstablishmentResultV1
            assert recovered.committed_result.disposition == "exact_replay"
            assert recovered.committed_result.transaction_timestamp == original.transaction_timestamp
            assert recovered.committed_result.command_digest == original.command_digest
            assert _all_family_rows(run.location) == durable_original
            assert _target_family_rows(run.location, command) == target_original
            assert _original_heads(run.location, run.handback) == heads_original
