from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

import ge_nwp_coordinator._sqlite_development_author_effect_establishment as runtime
import ge_nwp_coordinator.sqlite_connection as connection_module
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator import _development_decision_row_values as decision_rows
from ge_nwp_coordinator import _development_effect_row_values as effect_rows
from ge_nwp_coordinator import _development_program_row_values as program_rows
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1,
    DevelopmentAuthorEffectEstablishmentRecoveryResultV1,
    _development_author_effect_establishment_write_plan,
)
from ge_nwp_coordinator._development_row_value_support import (
    _domain_separated_digest,
)
from ge_nwp_coordinator._worker_execution_semantic_values import (
    DeliveryEnvelopeV1,
    create_effect_fence,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_store import WriterSessionError
from test_c2b3d_private_atomic_author_effect_establishment import (
    FAMILY_TABLES,
    family_counts,
    make_author_effect_fixture,
)


LATER = "2098-01-02T03:04:05Z"
LATER_TWO = "2098-01-02T03:04:06Z"
EARLIER = "2000-01-02T03:04:05Z"


def _row_with_digest(
    *,
    fields: dict[str, object],
    domain: str,
    digest_field: str,
    adapter: object,
) -> object:
    identity = dict(fields)
    fields[digest_field] = _domain_separated_digest(domain, identity)
    return adapter(tuple(fields.values()))


def _insert(
    connection: sqlite3.Connection,
    table: str,
    columns: tuple[str, ...],
    parameters: tuple[object, ...],
) -> None:
    cursor = connection.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES "
        f"({', '.join('?' for _ in columns)})",
        parameters,
    )
    try:
        assert cursor.rowcount == 1
    finally:
        cursor.close()


def _replace_head(
    connection: sqlite3.Connection,
    *,
    table: str,
    columns: tuple[str, ...],
    values: tuple[object, ...],
    effect_intent_ref: str,
) -> None:
    cursor = connection.execute(
        f"UPDATE {table} SET "
        + ", ".join(f"{column} = ?" for column in columns)
        + " WHERE effect_intent_ref = ?",
        values + (effect_intent_ref,),
    )
    try:
        assert cursor.rowcount == 1
    finally:
        cursor.close()


def _decision_row(
    fixture: object,
    *,
    decision_ref: str,
    mutation_ref: str,
    variant: str,
    target_delivery_attempt_ref: str | None,
    preassigned_delivery_attempt_ref: str,
    timestamp: str,
    wrong_target_class: bool = False,
) -> decision_rows.DevelopmentDecisionRowValue:
    command = fixture.command
    is_cancel = variant == "effect_cancellation"
    fields: dict[str, object] = {
        "schema_id": "governed-execution.nwp-development-decision.v1",
        "mutation_ref": mutation_ref,
        "decision_ref": decision_ref,
        "program_ref": command.program_ref,
        "decision_kind": "cancel" if is_cancel else "redeliver",
        "decision_variant": variant,
        "basis_decision_ref": command.basis_decision_ref,
        "basis_program_version_ref": command.program_version_ref,
        "basis_program_version_number": command.program_version_number,
        "expected_program_head_revision": 0,
        "resulting_program_version_ref": None,
        "resulting_program_version_number": None,
        "selected_semantic_attempt_ref": command.semantic_attempt_ref,
        "selected_candidate_ref": command.candidate_ref,
        "selected_attempt_fence_ref": command.attempt_fence_ref,
        "selected_attempt_fence_digest": command.attempt_fence.attempt_fence_digest,
        "target_effect_intent_ref": command.effect_intent_ref,
        "target_effect_class": (
            "validate_candidate" if wrong_target_class else "author_candidate"
        ),
        "target_effect_fence_ref": command.effect_fence_ref,
        "target_effect_fence_digest": command.effect_fence.effect_fence_digest,
        "expected_target_effect_head_revision": 0,
        "target_delivery_attempt_ref": (
            None if is_cancel else target_delivery_attempt_ref
        ),
        "originating_command_ref": command.command_ref,
        "originating_command_digest": command.worker_command.command_digest,
        "target_capsule_manifest_ref": (
            "capsule-wrong-class" if wrong_target_class else None
        ),
        "target_portable_capsule_digest": ("9" * 64 if wrong_target_class else None),
        "coding_global_stop_ref": command.coding_global_stop_ref,
        "coding_global_stop_version": command.coding_global_stop_version,
        "source_directive_ref": "directive-cancel" if is_cancel else None,
        "source_directive_digest": "a" * 64 if is_cancel else None,
        "source_evidence_ref": "evidence-cancel" if is_cancel else None,
        "source_evidence_digest": "b" * 64 if is_cancel else None,
        "preassigned_semantic_attempt_ref": None,
        "preassigned_candidate_ref": None,
        "preassigned_effect_intent_ref": (
            f"effect-intent-{decision_ref}" if is_cancel else None
        ),
        "preassigned_effect_fence_ref": (
            f"effect-fence-{decision_ref}" if is_cancel else None
        ),
        "preassigned_delivery_attempt_ref": preassigned_delivery_attempt_ref,
        "resulting_accepted_intent_revision_ref": None,
        "resulting_work_item_ref": None,
        "resulting_work_item_revision_ref": None,
        "reason_code": "decision.recorded",
        "decided_at": timestamp,
    }
    identity = dict(fields)
    fields["decision_digest"] = _domain_separated_digest(
        "governed-execution.nwp-development-decision.v1.identity",
        identity,
    )
    return decision_rows.development_decision_row_value_from_row_tuple(
        tuple(fields[column] for column in decision_rows._DEVELOPMENT_DECISION_COLUMNS)
    )


def _delivery_row(
    fixture: object,
    *,
    delivery_attempt_ref: str,
    predecessor_delivery_attempt_ref: str,
    delivery_number: int,
    decision_ref: str,
    timestamp: str,
) -> effect_rows.DevelopmentDeliveryAttemptRowValue:
    command = fixture.command
    envelope = DeliveryEnvelopeV1.create(
        delivery_attempt_ref=delivery_attempt_ref,
        adapter_kind="direct_local_bootstrap",
        adapter_safe_correlation_ref=f"correlation-{delivery_attempt_ref}",
        author_command=command.worker_command,
        attempt_fence=command.attempt_fence,
        author_effect_fence=command.effect_fence,
        effect_fence=command.effect_fence,
    )
    identity = {
        "schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
        "delivery_envelope_digest": envelope.delivery_envelope_digest,
        "delivery_kind": "redelivery",
        "delivery_number": delivery_number,
        "predecessor_delivery_attempt_ref": predecessor_delivery_attempt_ref,
        "basis_decision_ref": decision_ref,
        "recorded_at": timestamp,
    }
    digest = _domain_separated_digest(
        "governed-execution.nwp-development-delivery-attempt.v1.identity",
        identity,
    )
    return effect_rows.development_delivery_attempt_row_value_from_row_tuple(
        tuple(envelope.to_mapping().values())
        + (
            "redelivery",
            delivery_number,
            predecessor_delivery_attempt_ref,
            decision_ref,
            timestamp,
            digest,
        )
    )


def _install_delivery(
    fixture: object,
    *,
    delivery_attempt_ref: str,
    predecessor_delivery_attempt_ref: str,
    delivery_number: int,
    timestamp: str,
    head_revision: int,
) -> effect_rows.DevelopmentDeliveryAttemptRowValue:
    decision_ref = f"decision-{delivery_attempt_ref}"
    decision = _decision_row(
        fixture,
        decision_ref=decision_ref,
        mutation_ref=f"mutation-{delivery_attempt_ref}",
        variant="productive_redelivery",
        target_delivery_attempt_ref=predecessor_delivery_attempt_ref,
        preassigned_delivery_attempt_ref=delivery_attempt_ref,
        timestamp=timestamp,
    )
    delivery = _delivery_row(
        fixture,
        delivery_attempt_ref=delivery_attempt_ref,
        predecessor_delivery_attempt_ref=predecessor_delivery_attempt_ref,
        delivery_number=delivery_number,
        decision_ref=decision_ref,
        timestamp=timestamp,
    )
    head = _row_with_digest(
        fields={
            "schema_id": "governed-execution.nwp-development-delivery-head.v1",
            "effect_intent_ref": fixture.command.effect_intent_ref,
            "program_ref": fixture.command.program_ref,
            "current_delivery_attempt_ref": delivery_attempt_ref,
            "head_revision": head_revision,
            "delivery_state": "planned",
            "updated_at": timestamp,
        },
        domain="governed-execution.nwp-development-delivery-head.v1.identity",
        digest_field="head_digest",
        adapter=effect_rows.development_delivery_head_row_value_from_row_tuple,
    )
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        _insert(
            connection,
            "development_decisions",
            decision_rows._DEVELOPMENT_DECISION_COLUMNS,
            tuple(decision.decision._values) + (decision.decision_digest,),
        )
        _insert(
            connection,
            "development_delivery_attempts",
            effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS,
            runtime._delivery_attempt_parameters(delivery),
        )
        _replace_head(
            connection,
            table="development_delivery_heads",
            columns=effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
            values=tuple(head._values),
            effect_intent_ref=fixture.command.effect_intent_ref,
        )
        connection.commit()
    finally:
        connection.close()
    return delivery


def _install_effect_head(
    fixture: object,
    *,
    revision: int,
    state: str,
    cancellation_ref: str | None,
    timestamp: str,
    fence_ref: str | None = None,
    foreign_keys: bool = True,
) -> object:
    head = _row_with_digest(
        fields={
            "schema_id": "governed-execution.nwp-development-effect-head.v1",
            "effect_intent_ref": fixture.command.effect_intent_ref,
            "program_ref": fixture.command.program_ref,
            "current_effect_fence_ref": fence_ref or fixture.command.effect_fence_ref,
            "head_revision": revision,
            "effect_state": state,
            "cancellation_effect_intent_ref": cancellation_ref,
            "updated_at": timestamp,
        },
        domain="governed-execution.nwp-development-effect-head.v1.identity",
        digest_field="head_digest",
        adapter=effect_rows.development_effect_head_row_value_from_row_tuple,
    )
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute(f"PRAGMA foreign_keys = {'ON' if foreign_keys else 'OFF'}")
        connection.execute("BEGIN IMMEDIATE")
        _replace_head(
            connection,
            table="development_effect_heads",
            columns=effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS,
            values=tuple(head._values),
            effect_intent_ref=fixture.command.effect_intent_ref,
        )
        connection.commit()
    finally:
        connection.close()
    return head


def _install_delivery_head(
    fixture: object,
    *,
    delivery_attempt_ref: str,
    revision: int,
    state: str,
    timestamp: str,
    foreign_keys: bool = True,
) -> object:
    head = _row_with_digest(
        fields={
            "schema_id": "governed-execution.nwp-development-delivery-head.v1",
            "effect_intent_ref": fixture.command.effect_intent_ref,
            "program_ref": fixture.command.program_ref,
            "current_delivery_attempt_ref": delivery_attempt_ref,
            "head_revision": revision,
            "delivery_state": state,
            "updated_at": timestamp,
        },
        domain="governed-execution.nwp-development-delivery-head.v1.identity",
        digest_field="head_digest",
        adapter=effect_rows.development_delivery_head_row_value_from_row_tuple,
    )
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute(f"PRAGMA foreign_keys = {'ON' if foreign_keys else 'OFF'}")
        connection.execute("BEGIN IMMEDIATE")
        _replace_head(
            connection,
            table="development_delivery_heads",
            columns=effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
            values=tuple(head._values),
            effect_intent_ref=fixture.command.effect_intent_ref,
        )
        connection.commit()
    finally:
        connection.close()
    return head


def _install_cancellation(
    fixture: object,
    *,
    timestamp: str,
    foreign_candidate: bool = False,
    wrong_target_class: bool = False,
) -> tuple[object, object]:
    command = fixture.command
    decision_ref = f"cancel-decision-{command.effect_intent_ref}"
    intent_ref = f"effect-intent-{decision_ref}"
    fence_ref = f"effect-fence-{decision_ref}"
    decision = _decision_row(
        fixture,
        decision_ref=decision_ref,
        mutation_ref=f"mutation-{decision_ref}",
        variant="effect_cancellation",
        target_delivery_attempt_ref=None,
        preassigned_delivery_attempt_ref=f"delivery-{decision_ref}",
        timestamp=timestamp,
        wrong_target_class=wrong_target_class,
    )
    intent = _row_with_digest(
        fields={
            "schema_id": "governed-execution.nwp-development-effect-intent.v1",
            "effect_intent_ref": intent_ref,
            "program_ref": command.program_ref,
            "program_version_ref": command.program_version_ref,
            "semantic_attempt_ref": command.semantic_attempt_ref,
            "effect_class": "cancel_effect",
            "candidate_ref": (
                "foreign-candidate" if foreign_candidate else command.candidate_ref
            ),
            "command_ref": command.command_ref,
            "basis_decision_ref": decision_ref,
            "cancellation_target_effect_intent_ref": command.effect_intent_ref,
            "expected_target_effect_head_revision": 0,
            "portable_capsule_digest": None,
            "created_at": timestamp,
        },
        domain="governed-execution.nwp-development-effect-intent.v1.identity",
        digest_field="effect_intent_digest",
        adapter=effect_rows.development_effect_intent_row_value_from_row_tuple,
    )
    fence = create_effect_fence(
        attempt_fence=command.attempt_fence,
        author_command=command.worker_command,
        author_effect_fence=command.effect_fence,
        effect_fence_ref=fence_ref,
        effect_intent_ref=intent_ref,
        effect_class="cancel_effect",
        effect_authorization_ref=f"effect-authorization-{decision_ref}",
        effect_authorization_digest="c" * 64,
        effect_ceilings=command.effect_authorization_safe_binding.effect_ceilings,
        expires_at=command.effect_fence.expires_at,
        cancellation_target=command.effect_fence,
    )
    fence_row = effect_rows.development_effect_fence_row_value_from_row_tuple(
        runtime._effect_fence_parameters(
            effect_rows.DevelopmentEffectFenceRowValue._from_validated(
                fence,
                timestamp,
            )
        )
    )
    head = _row_with_digest(
        fields={
            "schema_id": "governed-execution.nwp-development-effect-head.v1",
            "effect_intent_ref": command.effect_intent_ref,
            "program_ref": command.program_ref,
            "current_effect_fence_ref": command.effect_fence_ref,
            "head_revision": 1,
            "effect_state": "cancellation_effect_established",
            "cancellation_effect_intent_ref": intent_ref,
            "updated_at": timestamp,
        },
        domain="governed-execution.nwp-development-effect-head.v1.identity",
        digest_field="head_digest",
        adapter=effect_rows.development_effect_head_row_value_from_row_tuple,
    )
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        _insert(
            connection,
            "development_decisions",
            decision_rows._DEVELOPMENT_DECISION_COLUMNS,
            tuple(decision.decision._values) + (decision.decision_digest,),
        )
        _insert(
            connection,
            "development_effect_intents",
            effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS,
            tuple(intent._values),
        )
        _insert(
            connection,
            "development_effect_fences",
            effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS,
            runtime._effect_fence_parameters(fence_row),
        )
        _replace_head(
            connection,
            table="development_effect_heads",
            columns=effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS,
            values=tuple(head._values),
            effect_intent_ref=command.effect_intent_ref,
        )
        connection.commit()
    finally:
        connection.close()
    return intent, fence_row


def _receipt_bytes(fixture: object) -> tuple[object, ...]:
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        row = connection.execute(
            "SELECT "
            + ", ".join(decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS)
            + " FROM development_mutation_receipts WHERE mutation_ref = ?",
            (fixture.command.mutation_ref,),
        ).fetchone()
    finally:
        connection.close()
    assert type(row) is tuple
    return row


def _assert_apply_integrity_and_recovery_unresolved(fixture: object) -> None:
    with pytest.raises(SQLiteMutationStoreError) as captured:
        fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
    assert captured.value.error_class == "database_integrity_failure"
    recovered = (
        fixture.writer._resolve_development_author_effect_establishment_commit_outcome(
            fixture.command
        )
    )
    assert (
        recovered.disposition
        is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.UNRESOLVED
    )


def _forbidden_side_effect(*args: object, **kwargs: object) -> object:
    raise AssertionError("recovery or replay crossed a write, clock, or COMMIT seam")


def _assert_unknown(error: SQLiteMutationStoreError) -> None:
    assert error.error_class == "commit_outcome_unknown"
    assert error.args == ("commit_outcome_unknown",)
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None


def test_total_absence_recovers_definitely_not_committed_without_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="absent")
    before = family_counts(fixture.location)
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", _forbidden_side_effect
    )
    monkeypatch.setattr(transaction, "_commit_transaction", _forbidden_side_effect)
    monkeypatch.setattr(
        transaction,
        "_execute_development_author_effect_establishment_writes",
        _forbidden_side_effect,
    )
    try:
        result = fixture.writer._resolve_development_author_effect_establishment_commit_outcome(
            fixture.command
        )
        assert type(result) is DevelopmentAuthorEffectEstablishmentRecoveryResultV1
        assert (
            result.disposition
            is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
        assert result.committed_result is None
        assert family_counts(fixture.location) == before
    finally:
        fixture.writer.close()


def test_complete_family_recovers_committed_exact_under_fresh_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="complete")
    generation = fixture.writer.metadata.generation
    committed = fixture.writer._establish_development_author_effect_intent(
        **fixture.ingress
    )
    fixture.writer.close()
    fresh = acquire_sqlite_writer_session(fixture.location)
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", _forbidden_side_effect
    )
    monkeypatch.setattr(transaction, "_commit_transaction", _forbidden_side_effect)
    monkeypatch.setattr(
        transaction,
        "_execute_development_author_effect_establishment_writes",
        _forbidden_side_effect,
    )
    try:
        assert fresh.metadata.generation == generation + 1
        recovered = (
            fresh._resolve_development_author_effect_establishment_commit_outcome(
                fixture.command
            )
        )
        assert (
            recovered.disposition
            is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
        )
        assert recovered.committed_result is not None
        assert recovered.committed_result.disposition == "exact_replay"
        assert (
            recovered.committed_result.transaction_timestamp
            == committed.transaction_timestamp
        )
        assert family_counts(fixture.location) == dict.fromkeys(FAMILY_TABLES, 1)
    finally:
        fresh.close()


def test_partial_family_without_receipt_recovers_unresolved(tmp_path: Path) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="partial")
    plan = _development_author_effect_establishment_write_plan(
        fixture.command,
        "2026-08-22T12:34:56Z",
    )
    fixture.writer.close()
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        _insert(
            connection,
            "development_semantic_attempts",
            program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
            tuple(plan.semantic_attempt._values),
        )
        connection.commit()
    finally:
        connection.close()

    fresh = acquire_sqlite_writer_session(fixture.location)
    try:
        recovered = (
            fresh._resolve_development_author_effect_establishment_commit_outcome(
                fixture.command
            )
        )
        assert (
            recovered.disposition
            is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.UNRESOLVED
        )
        assert recovered.committed_result is None
        assert family_counts(fixture.location)["development_semantic_attempts"] == 1
        assert all(
            count == 0
            for table, count in family_counts(fixture.location).items()
            if table != "development_semantic_attempts"
        )
    finally:
        fresh.close()


@pytest.mark.parametrize("commit_reaches_disk", (False, True))
def test_commit_uncertainty_requires_readback_and_never_retries_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    commit_reaches_disk: bool,
) -> None:
    fixture = make_author_effect_fixture(
        tmp_path,
        suffix=f"uncertain-{commit_reaches_disk}",
    )
    original_commit = transaction._commit_transaction
    writes = 0
    original_writes = (
        transaction._execute_development_author_effect_establishment_writes
    )

    def uncertain_commit(connection: sqlite3.Connection) -> object:
        if commit_reaches_disk:
            assert original_commit(connection) is None
        return transaction._SQLITE_COMMIT_FAILED

    def counted_writes(connection: object, plan: object) -> None:
        nonlocal writes
        writes += 1
        original_writes(connection, plan)

    monkeypatch.setattr(transaction, "_commit_transaction", uncertain_commit)
    monkeypatch.setattr(
        transaction,
        "_execute_development_author_effect_establishment_writes",
        counted_writes,
    )
    with pytest.raises(SQLiteMutationStoreError) as captured:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
    _assert_unknown(captured.value)
    assert writes == 1
    assert fixture.writer.active is False
    fixture.writer.close()

    fresh = acquire_sqlite_writer_session(fixture.location)
    try:
        recovered = (
            fresh._resolve_development_author_effect_establishment_commit_outcome(
                fixture.command
            )
        )
        expected = (
            DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
            if commit_reaches_disk
            else DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
        assert recovered.disposition is expected
        expected_count = 1 if commit_reaches_disk else 0
        assert family_counts(fixture.location) == dict.fromkeys(
            FAMILY_TABLES, expected_count
        )
        assert writes == 1
    finally:
        fresh.close()


def test_close_uncertainty_retains_custody_and_blocks_old_session_until_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="close-proof")
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    close_calls = 0

    def fail_first_close(retained: object) -> object:
        nonlocal close_calls
        close_calls += 1
        if close_calls == 1:
            raise RuntimeError("private-close-sentinel")
        return original_close(retained)

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        fail_first_close,
    )
    committed = fixture.writer._establish_development_author_effect_intent(
        **fixture.ingress
    )
    assert committed.disposition == "committed"
    resource = fixture.writer._resource
    assert resource._state == "commit_succeeded_quarantined"
    assert resource._mutation_slot is not None
    assert resource._retained_connection is not None
    with pytest.raises(WriterSessionError):
        resource.operation_guard(fixture.writer)
    fixture.writer.close()
    assert resource._state == "closed"
    assert resource._mutation_slot is None
    assert resource._retained_connection is None
    assert close_calls >= 2


def test_fresh_writer_recovers_while_old_resource_is_nonadmitting_before_t1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="pre-t1")
    old_session = fixture.writer
    old_resource = old_session._resource
    old_generation = old_session.metadata.generation
    reached_pre_t1 = threading.Event()
    release_t1 = threading.Event()
    original_advance = (
        writer_module._WriterSessionResource._advance_claimed_cleanup_once
    )
    original_commit = transaction._commit_transaction

    def commit_then_report_unknown(connection: sqlite3.Connection) -> object:
        assert original_commit(connection) is None
        return transaction._SQLITE_COMMIT_FAILED

    def pause_before_t1(self: object, claim: object) -> object:
        if self is old_resource:
            with self._condition:
                pending = self._lifecycle_state.pending_state
                cursor = writer_module._cleanup_continuation(pending).cursor
            if type(cursor) is writer_module._CleanupBeforeT1:
                reached_pre_t1.set()
                if not release_t1.wait(10):
                    raise AssertionError("pre-T1 recovery test timed out")
        return original_advance(self, claim)

    monkeypatch.setattr(transaction, "_commit_transaction", commit_then_report_unknown)
    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_advance_claimed_cleanup_once",
        pause_before_t1,
    )
    observed: list[BaseException] = []

    def uncertain_apply() -> None:
        try:
            old_session._establish_development_author_effect_intent(**fixture.ingress)
        except BaseException as error:
            observed.append(error)
        finally:
            old_session.close()

    thread = threading.Thread(target=uncertain_apply)
    thread.start()
    assert reached_pre_t1.wait(10)
    assert (
        type(old_resource._lifecycle_state) is not writer_module._WriterSessionTerminalX
    )
    assert old_session.active is False

    fresh = acquire_sqlite_writer_session(fixture.location)
    try:
        assert fresh.metadata.generation == old_generation + 1
        recovered = (
            fresh._resolve_development_author_effect_establishment_commit_outcome(
                fixture.command
            )
        )
        assert (
            recovered.disposition
            is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
        )
        assert (
            type(old_resource._lifecycle_state)
            is not writer_module._WriterSessionTerminalX
        )
    finally:
        release_t1.set()
        thread.join(10)
        fresh.close()

    assert not thread.is_alive()
    assert len(observed) == 1
    assert type(observed[0]) is SQLiteMutationStoreError
    _assert_unknown(observed[0])
    assert type(old_resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_advanced_heads_with_original_refs_preserve_receipt_graph_and_replay(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="advanced-heads")
    try:
        committed = fixture.writer._establish_development_author_effect_intent(
            **fixture.ingress
        )
        receipt = _receipt_bytes(fixture)
        counts = family_counts(fixture.location)
        _install_effect_head(
            fixture,
            revision=5,
            state="delivery_pending",
            cancellation_ref=None,
            timestamp=LATER,
        )
        _install_delivery_head(
            fixture,
            delivery_attempt_ref=fixture.command.delivery_attempt_ref,
            revision=8,
            state="submitted",
            timestamp=LATER_TWO,
        )
        replay = fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
        assert replay.disposition == "exact_replay"
        assert replay.transaction_timestamp == committed.transaction_timestamp
        assert _receipt_bytes(fixture) == receipt
        assert family_counts(fixture.location) == counts
    finally:
        fixture.writer.close()


def test_later_delivery_and_immediate_predecessor_preserve_original_receipt(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="redelivery")
    try:
        committed = fixture.writer._establish_development_author_effect_intent(
            **fixture.ingress
        )
        receipt = _receipt_bytes(fixture)
        second = _install_delivery(
            fixture,
            delivery_attempt_ref="delivery-redelivery-2",
            predecessor_delivery_attempt_ref=fixture.command.delivery_attempt_ref,
            delivery_number=2,
            timestamp=LATER,
            head_revision=3,
        )
        third = _install_delivery(
            fixture,
            delivery_attempt_ref="delivery-redelivery-3",
            predecessor_delivery_attempt_ref=second.delivery_attempt_ref,
            delivery_number=3,
            timestamp=LATER_TWO,
            head_revision=9,
        )
        assert third.predecessor_delivery_attempt_ref == second.delivery_attempt_ref
        replay = fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
        assert replay.disposition == "exact_replay"
        assert replay.transaction_timestamp == committed.transaction_timestamp
        assert _receipt_bytes(fixture) == receipt
    finally:
        fixture.writer.close()


def test_cancellation_reference_correspondence_preserves_original_receipt(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="cancellation")
    try:
        committed = fixture.writer._establish_development_author_effect_intent(
            **fixture.ingress
        )
        receipt = _receipt_bytes(fixture)
        intent, fence = _install_cancellation(fixture, timestamp=LATER)
        assert (
            intent.cancellation_target_effect_intent_ref
            == fixture.command.effect_intent_ref
        )
        assert (
            fence.cancellation_target_effect_fence_ref
            == fixture.command.effect_fence_ref
        )
        replay = fixture.writer._run_development_author_effect_establishment_operation(
            command=fixture.command,
            recovery=False,
        )
        assert replay.disposition == "exact_replay"
        assert replay.transaction_timestamp == committed.transaction_timestamp
        assert _receipt_bytes(fixture) == receipt
    finally:
        fixture.writer.close()


@pytest.mark.parametrize(
    "contradiction",
    (
        "revision-zero-change",
        "regressed-effect-time",
        "missing-effect-fence",
        "missing-delivery",
    ),
)
def test_self_digested_head_contradictions_fail_apply_and_recover_unresolved(
    tmp_path: Path,
    contradiction: str,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix=contradiction)
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
        receipt = _receipt_bytes(fixture)
        if contradiction == "revision-zero-change":
            _install_effect_head(
                fixture,
                revision=0,
                state="delivery_pending",
                cancellation_ref=None,
                timestamp=LATER,
            )
        elif contradiction == "regressed-effect-time":
            _install_effect_head(
                fixture,
                revision=1,
                state="delivery_pending",
                cancellation_ref=None,
                timestamp=EARLIER,
            )
        elif contradiction == "missing-effect-fence":
            _install_effect_head(
                fixture,
                revision=1,
                state="delivery_pending",
                cancellation_ref=None,
                timestamp=LATER,
                fence_ref="missing-effect-fence",
                foreign_keys=False,
            )
        else:
            _install_delivery_head(
                fixture,
                delivery_attempt_ref="missing-delivery-attempt",
                revision=1,
                state="submitted",
                timestamp=LATER,
                foreign_keys=False,
            )
        _assert_apply_integrity_and_recovery_unresolved(fixture)
        assert _receipt_bytes(fixture) == receipt
    finally:
        fixture.writer.close()


@pytest.mark.parametrize(
    ("foreign_candidate", "wrong_target_class"),
    ((True, False), (False, True)),
    ids=("wrong-family-candidate", "wrong-cancellation-target-class"),
)
def test_fk_valid_self_digested_cancellation_contradictions_are_rejected(
    tmp_path: Path,
    foreign_candidate: bool,
    wrong_target_class: bool,
) -> None:
    fixture = make_author_effect_fixture(
        tmp_path,
        suffix=f"cancel-negative-{foreign_candidate}-{wrong_target_class}",
    )
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
        receipt = _receipt_bytes(fixture)
        _install_cancellation(
            fixture,
            timestamp=LATER,
            foreign_candidate=foreign_candidate,
            wrong_target_class=wrong_target_class,
        )
        connection = sqlite3.connect(fixture.location.database_path)
        try:
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        finally:
            connection.close()
        _assert_apply_integrity_and_recovery_unresolved(fixture)
        assert _receipt_bytes(fixture) == receipt
    finally:
        fixture.writer.close()


def test_fk_valid_wrong_family_current_effect_fence_is_rejected(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="wrong-current-effect-fence")
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
        receipt = _receipt_bytes(fixture)
        intent, cancellation_fence = _install_cancellation(fixture, timestamp=LATER)
        _install_effect_head(
            fixture,
            revision=2,
            state="cancellation_effect_established",
            cancellation_ref=intent.effect_intent_ref,
            timestamp=LATER_TWO,
            fence_ref=cancellation_fence.effect_fence_ref,
        )
        connection = sqlite3.connect(fixture.location.database_path)
        try:
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        finally:
            connection.close()
        _assert_apply_integrity_and_recovery_unresolved(fixture)
        assert _receipt_bytes(fixture) == receipt
    finally:
        fixture.writer.close()


@pytest.mark.parametrize(
    ("number", "predecessor", "timestamp"),
    (
        (3, "original", LATER),
        (2, "original", EARLIER),
    ),
    ids=("inconsistent-predecessor-number", "predecessor-before-establishment"),
)
def test_redelivery_number_and_time_contradictions_are_rejected(
    tmp_path: Path,
    number: int,
    predecessor: str,
    timestamp: str,
) -> None:
    fixture = make_author_effect_fixture(
        tmp_path,
        suffix=f"redelivery-negative-{number}-{timestamp[:4]}",
    )
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
        receipt = _receipt_bytes(fixture)
        predecessor_ref = (
            fixture.command.delivery_attempt_ref
            if predecessor == "original"
            else predecessor
        )
        _install_delivery(
            fixture,
            delivery_attempt_ref=f"delivery-negative-{number}-{timestamp[:4]}",
            predecessor_delivery_attempt_ref=predecessor_ref,
            delivery_number=number,
            timestamp=timestamp,
            head_revision=4,
        )
        _assert_apply_integrity_and_recovery_unresolved(fixture)
        assert _receipt_bytes(fixture) == receipt
    finally:
        fixture.writer.close()
