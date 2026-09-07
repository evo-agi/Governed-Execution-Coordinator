from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import select
import sqlite3
import threading

import pytest

import ge_nwp_coordinator._development_decision_row_values as decision_rows
import ge_nwp_coordinator._development_program_row_values as program_rows
import ge_nwp_coordinator._sqlite_development_program_initialization as initialization_module
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module
import ge_nwp_coordinator.state_authority_lock as authority_lock_module
from ge_nwp_coordinator._development_program_initialization_contracts import (
    DevelopmentProgramInitializationRecoveryDispositionV1,
    DevelopmentProgramInitializationRecoveryResultV1,
    _development_program_initialization_write_plan,
    _initialization_result,
    _program_row,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import (
    acquire_sqlite_writer_session,
)
from ge_nwp_coordinator.state_authority_lock import StateAuthorityLockError
from test_c2b3_private_atomic_program_initialization import (
    command_from_work_spec,
    make_genesis_fixture,
    table_counts,
)


_LATER_TIMESTAMP = "2099-01-02T03:04:05Z"


@dataclass(frozen=True)
class HistoricalHeadState:
    program_head: program_rows.DevelopmentProgramHeadRowValue
    work_item_head: program_rows.DevelopmentWorkItemHeadRowValue
    later_program_version: program_rows.DevelopmentProgramVersionRowValue
    later_work_item_revision: program_rows.DevelopmentWorkItemRevisionRowValue
    foreign_key_check: tuple[tuple[object, ...], ...]
    integrity_check: tuple[tuple[object, ...], ...]


def _fetch_all(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[object, ...] = (),
) -> tuple[tuple[object, ...], ...]:
    cursor = connection.execute(sql, parameters)
    try:
        return tuple(cursor.fetchall())
    finally:
        cursor.close()


def _update_exact_row(
    connection: sqlite3.Connection,
    *,
    table: str,
    columns: tuple[str, ...],
    values: tuple[object, ...],
    where: str,
    parameters: tuple[object, ...],
) -> None:
    cursor = connection.execute(
        f"UPDATE {table} SET "
        + ", ".join(f"{column} = ?" for column in columns)
        + f" WHERE {where}",
        values + parameters,
    )
    try:
        assert cursor.rowcount == 1
    finally:
        cursor.close()


def _install_later_rows_and_replace_heads(
    fixture: object,
    *,
    program_ref_kind: str,
    program_number: int,
    work_ref_kind: str,
    work_number: int,
) -> HistoricalHeadState:
    command = fixture.command
    work = command.work_spec_safe_projection
    later_program_version_ref = f"{command.program_version_ref}.later"
    later_work_item_revision_ref = f"{work.work_item_revision_ref}.later"
    later_program_version = _program_row(
        adapter=program_rows.development_program_version_row_value_from_row_tuple,
        domain="governed-execution.nwp-development-program-version.v1.identity",
        digest_field="program_version_digest",
        fields={
            "schema_id": "governed-execution.nwp-development-program-version.v1",
            "program_version_ref": later_program_version_ref,
            "program_ref": command.program_ref,
            "program_version_number": 2,
            "program_version_kind": "replan",
            "creating_decision_ref": command.decision_ref,
            "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
            "created_at": _LATER_TIMESTAMP,
        },
    )
    later_work_item_revision = _program_row(
        adapter=program_rows.development_work_item_revision_row_value_from_row_tuple,
        domain="governed-execution.nwp-development-work-item-revision.v1.identity",
        digest_field="work_item_revision_digest",
        fields={
            "schema_id": "governed-execution.nwp-development-work-item-revision.v1",
            "work_item_revision_ref": later_work_item_revision_ref,
            "program_ref": command.program_ref,
            "work_item_ref": work.work_item_ref,
            "work_item_revision_number": 2,
            "work_item_revision_kind": "replan",
            "prior_work_item_revision_ref": work.work_item_revision_ref,
            "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
            "created_at": _LATER_TIMESTAMP,
        },
    )
    selected_program_ref = {
        "genesis": command.program_version_ref,
        "later": later_program_version_ref,
    }[program_ref_kind]
    selected_work_ref = {
        "genesis": work.work_item_revision_ref,
        "later": later_work_item_revision_ref,
    }[work_ref_kind]
    program_head = _program_row(
        adapter=program_rows.development_program_head_row_value_from_row_tuple,
        domain="governed-execution.nwp-development-program-head.v1.identity",
        digest_field="head_digest",
        fields={
            "schema_id": "governed-execution.nwp-development-program-head.v1",
            "program_ref": command.program_ref,
            "current_program_version_ref": selected_program_ref,
            "current_program_version_number": program_number,
            "head_revision": 1,
            "program_state": "active",
            "updated_at": _LATER_TIMESTAMP,
        },
    )
    work_item_head = _program_row(
        adapter=program_rows.development_work_item_head_row_value_from_row_tuple,
        domain="governed-execution.nwp-development-work-item-head.v1.identity",
        digest_field="head_digest",
        fields={
            "schema_id": "governed-execution.nwp-development-work-item-head.v1",
            "work_item_ref": work.work_item_ref,
            "program_ref": command.program_ref,
            "current_work_item_revision_ref": selected_work_ref,
            "current_work_item_revision_number": work_number,
            "head_revision": 1,
            "work_state": "planned",
            "updated_at": _LATER_TIMESTAMP,
        },
    )

    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        initialization_module._execute_insert(
            connection,
            "development_program_versions",
            program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
            tuple(later_program_version._values),
        )
        initialization_module._execute_insert(
            connection,
            "development_work_item_revisions",
            program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
            tuple(later_work_item_revision._values),
        )
        _update_exact_row(
            connection,
            table="development_program_heads",
            columns=program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
            values=tuple(program_head._values),
            where="program_ref = ?",
            parameters=(command.program_ref,),
        )
        _update_exact_row(
            connection,
            table="development_work_item_heads",
            columns=program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
            values=tuple(work_item_head._values),
            where="program_ref = ? AND work_item_ref = ?",
            parameters=(command.program_ref, work.work_item_ref),
        )
        connection.commit()
        foreign_key_check = _fetch_all(connection, "PRAGMA foreign_key_check")
        integrity_check = _fetch_all(connection, "PRAGMA integrity_check")
    finally:
        connection.close()
    return HistoricalHeadState(
        program_head=program_head,
        work_item_head=work_item_head,
        later_program_version=later_program_version,
        later_work_item_revision=later_work_item_revision,
        foreign_key_check=foreign_key_check,
        integrity_check=integrity_check,
    )


def _read_receipt_value(
    fixture: object,
) -> decision_rows.DevelopmentMutationReceiptRowValue:
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        rows = _fetch_all(
            connection,
            "SELECT "
            + ", ".join(decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS)
            + " FROM development_mutation_receipts WHERE mutation_ref = ? LIMIT 2",
            (fixture.command.mutation_ref,),
        )
    finally:
        connection.close()
    assert len(rows) == 1
    return decision_rows.development_mutation_receipt_row_value_from_row_tuple(rows[0])


def _forbid_replay_or_recovery_side_effect(
    *args: object, **kwargs: object
) -> object:
    raise AssertionError("historical verification crossed a write, COMMIT, or clock boundary")


def _assert_relation_integrity_failure(session: object, command: object) -> None:
    try:
        result = session._apply_development_program_initialization(command)
    except SQLiteMutationStoreError as error:
        assert error.error_class == "database_integrity_failure"
        assert error.args == ("database_integrity_failure",)
        assert error.internal_detail is None
        assert error.__cause__ is None
        assert error.__context__ is None
        return
    raise AssertionError(
        "contradictory current immutable relation replayed through the real verifier: "
        f"{result.disposition}"
    )


def test_recovery_returns_definitely_not_committed_without_clock_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    try:
        before = table_counts(fixture.location)

        def forbidden(*args: object, **kwargs: object) -> object:
            raise AssertionError("read-only recovery crossed a prohibited boundary")

        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", forbidden)
        monkeypatch.setattr(transaction_module, "_commit_transaction", forbidden)
        monkeypatch.setattr(
            initialization_module,
            "_execute_development_program_initialization_writes",
            forbidden,
        )
        result = fixture.writer_session._resolve_development_program_initialization_commit_outcome(
            fixture.command
        )
        assert type(result) is DevelopmentProgramInitializationRecoveryResultV1
        assert (
            result.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
        assert result.committed_result is None
        assert table_counts(fixture.location) == before
    finally:
        fixture.writer_session.close()


def test_fresh_writer_recovers_committed_exact_from_reconstructed_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    first_generation = fixture.writer_session.metadata.generation
    committed = fixture.writer_session._apply_development_program_initialization(
        fixture.command
    )
    fixture.writer_session.close()

    reconstructed_work_spec = WorkSpecV1.from_mapping(fixture.work_spec.to_mapping())
    reconstructed = command_from_work_spec(reconstructed_work_spec, suffix="one")
    assert reconstructed is not fixture.command
    assert reconstructed == fixture.command

    fresh = acquire_sqlite_writer_session(fixture.location)
    try:
        assert fresh.metadata.generation == first_generation + 1

        def forbidden(*args: object, **kwargs: object) -> object:
            raise AssertionError("recovery called fresh-only clock or COMMIT")

        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", forbidden)
        monkeypatch.setattr(transaction_module, "_commit_transaction", forbidden)
        result = fresh._resolve_development_program_initialization_commit_outcome(
            reconstructed
        )
        assert (
            result.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.COMMITTED_EXACT
        )
        assert result.committed_result is not None
        assert result.committed_result.disposition == "exact_replay"
        assert (
            result.committed_result.transaction_timestamp
            == committed.transaction_timestamp
        )
    finally:
        fresh.close()


def test_valid_later_heads_preserve_original_historical_replay_and_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path, suffix="later-valid")
    committed = fixture.writer_session._apply_development_program_initialization(
        fixture.command
    )
    original_plan = _development_program_initialization_write_plan(
        fixture.command, committed.transaction_timestamp
    )
    original_receipt = _read_receipt_value(fixture)
    fixture.writer_session.close()

    state = _install_later_rows_and_replace_heads(
        fixture,
        program_ref_kind="later",
        program_number=2,
        work_ref_kind="later",
        work_number=2,
    )
    assert state.foreign_key_check == ()
    assert state.integrity_check == (("ok",),)
    assert state.program_head != original_plan.program_head
    assert state.work_item_head != original_plan.work_item_head
    assert original_receipt == original_plan.mutation_receipt
    assert len(original_plan.graph_entries) == 8
    assert tuple(entry.role for entry in original_plan.graph_entries) == (
        "program_head_postimage",
        "accepted_intent_revision",
        "initialize_decision",
        "program_version",
        "work_item_head_postimage",
        "work_item_revision",
        "program_version_work_item",
        "work_spec_binding",
    )

    replay_session = acquire_sqlite_writer_session(fixture.location)
    monkeypatch.setattr(
        transaction_module,
        "_utc_transaction_timestamp",
        _forbid_replay_or_recovery_side_effect,
    )
    monkeypatch.setattr(
        transaction_module,
        "_commit_transaction",
        _forbid_replay_or_recovery_side_effect,
    )
    monkeypatch.setattr(
        initialization_module,
        "_execute_development_program_initialization_writes",
        _forbid_replay_or_recovery_side_effect,
    )
    try:
        before_replay = table_counts(fixture.location)
        replay = replay_session._apply_development_program_initialization(
            fixture.command
        )
        assert replay == _initialization_result(
            fixture.command, committed.transaction_timestamp, "exact_replay"
        )
        assert replay.transaction_timestamp == committed.transaction_timestamp
        assert table_counts(fixture.location) == before_replay
        assert _read_receipt_value(fixture) == original_receipt
    finally:
        replay_session.close()

    recovery_session = acquire_sqlite_writer_session(fixture.location)
    try:
        before_recovery = table_counts(fixture.location)
        recovery = recovery_session._resolve_development_program_initialization_commit_outcome(
            fixture.command
        )
        assert (
            recovery.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.COMMITTED_EXACT
        )
        assert recovery.committed_result == replay
        assert table_counts(fixture.location) == before_recovery
        assert _read_receipt_value(fixture) == original_receipt
    finally:
        recovery_session.close()


@pytest.mark.parametrize(
    ("program_ref_kind", "program_number"),
    (("genesis", 2), ("later", 1)),
    ids=("genesis-ref-claims-two", "later-ref-claims-one"),
)
def test_program_head_ref_number_contradictions_fail_apply_and_recover_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    program_ref_kind: str,
    program_number: int,
) -> None:
    suffix = f"program-{program_ref_kind}-{program_number}"
    fixture = make_genesis_fixture(tmp_path, suffix=suffix)
    fixture.writer_session._apply_development_program_initialization(fixture.command)
    original_receipt = _read_receipt_value(fixture)
    fixture.writer_session.close()
    state = _install_later_rows_and_replace_heads(
        fixture,
        program_ref_kind=program_ref_kind,
        program_number=program_number,
        work_ref_kind="later",
        work_number=2,
    )
    assert state.foreign_key_check == ()
    assert state.integrity_check == (("ok",),)

    apply_session = acquire_sqlite_writer_session(fixture.location)
    monkeypatch.setattr(
        transaction_module,
        "_utc_transaction_timestamp",
        _forbid_replay_or_recovery_side_effect,
    )
    monkeypatch.setattr(
        transaction_module,
        "_commit_transaction",
        _forbid_replay_or_recovery_side_effect,
    )
    monkeypatch.setattr(
        initialization_module,
        "_execute_development_program_initialization_writes",
        _forbid_replay_or_recovery_side_effect,
    )
    try:
        before_apply = table_counts(fixture.location)
        _assert_relation_integrity_failure(apply_session, fixture.command)
        assert table_counts(fixture.location) == before_apply
        assert _read_receipt_value(fixture) == original_receipt
    finally:
        apply_session.close()

    recovery_session = acquire_sqlite_writer_session(fixture.location)
    try:
        before_recovery = table_counts(fixture.location)
        recovery = recovery_session._resolve_development_program_initialization_commit_outcome(
            fixture.command
        )
        assert (
            recovery.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.UNRESOLVED
        )
        assert recovery.committed_result is None
        assert table_counts(fixture.location) == before_recovery
        assert _read_receipt_value(fixture) == original_receipt
    finally:
        recovery_session.close()


@pytest.mark.parametrize(
    ("work_ref_kind", "work_number"),
    (("genesis", 2), ("later", 1)),
    ids=("genesis-ref-claims-two", "later-ref-claims-one"),
)
def test_work_head_ref_number_contradictions_fail_apply_and_recover_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    work_ref_kind: str,
    work_number: int,
) -> None:
    suffix = f"work-{work_ref_kind}-{work_number}"
    fixture = make_genesis_fixture(tmp_path, suffix=suffix)
    fixture.writer_session._apply_development_program_initialization(fixture.command)
    original_receipt = _read_receipt_value(fixture)
    fixture.writer_session.close()
    state = _install_later_rows_and_replace_heads(
        fixture,
        program_ref_kind="later",
        program_number=2,
        work_ref_kind=work_ref_kind,
        work_number=work_number,
    )
    assert state.foreign_key_check == ()
    assert state.integrity_check == (("ok",),)

    apply_session = acquire_sqlite_writer_session(fixture.location)
    monkeypatch.setattr(
        transaction_module,
        "_utc_transaction_timestamp",
        _forbid_replay_or_recovery_side_effect,
    )
    monkeypatch.setattr(
        transaction_module,
        "_commit_transaction",
        _forbid_replay_or_recovery_side_effect,
    )
    monkeypatch.setattr(
        initialization_module,
        "_execute_development_program_initialization_writes",
        _forbid_replay_or_recovery_side_effect,
    )
    try:
        before_apply = table_counts(fixture.location)
        _assert_relation_integrity_failure(apply_session, fixture.command)
        assert table_counts(fixture.location) == before_apply
        assert _read_receipt_value(fixture) == original_receipt
    finally:
        apply_session.close()

    recovery_session = acquire_sqlite_writer_session(fixture.location)
    try:
        before_recovery = table_counts(fixture.location)
        recovery = recovery_session._resolve_development_program_initialization_commit_outcome(
            fixture.command
        )
        assert (
            recovery.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.UNRESOLVED
        )
        assert recovery.committed_result is None
        assert table_counts(fixture.location) == before_recovery
        assert _read_receipt_value(fixture) == original_receipt
    finally:
        recovery_session.close()


def test_program_relation_guard_is_causal_for_real_apply_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path, suffix="causal-program")
    fixture.writer_session._apply_development_program_initialization(fixture.command)
    fixture.writer_session.close()
    state = _install_later_rows_and_replace_heads(
        fixture,
        program_ref_kind="genesis",
        program_number=2,
        work_ref_kind="later",
        work_number=2,
    )
    assert state.foreign_key_check == ()
    assert state.integrity_check == (("ok",),)

    def old_head_only_check(**kwargs: object) -> bool:
        return initialization_module._program_head_is_genesis_or_valid_later(
            kwargs["actual_head"],
            kwargs["genesis_head"],
            kwargs["committed_at"],
        )

    session = acquire_sqlite_writer_session(fixture.location)
    monkeypatch.setattr(
        initialization_module,
        "_program_head_and_current_version_are_coherent",
        old_head_only_check,
    )
    try:
        with pytest.raises(
            AssertionError,
            match="contradictory current immutable relation replayed through the real verifier",
        ):
            _assert_relation_integrity_failure(session, fixture.command)
    finally:
        session.close()


def test_changed_command_or_partial_family_resolves_unresolved(tmp_path: Path) -> None:
    fixture = make_genesis_fixture(tmp_path, suffix="changed")
    fixture.writer_session._apply_development_program_initialization(fixture.command)
    changed_command = command_from_work_spec(
        fixture.work_spec,
        suffix="changed",
        candidate_suffix="different",
    )
    result = fixture.writer_session._resolve_development_program_initialization_commit_outcome(
        changed_command
    )
    assert (
        result.disposition
        is DevelopmentProgramInitializationRecoveryDispositionV1.UNRESOLVED
    )
    fixture.writer_session.close()

    partial = make_genesis_fixture(tmp_path, suffix="partial")
    partial.writer_session.close()
    plan = _development_program_initialization_write_plan(
        partial.command, "2026-08-21T12:34:56Z"
    )
    ordered = (
        (
            "development_program_heads",
            program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
            initialization_module._program_head_parameters(plan.program_head),
        ),
        (
            "development_accepted_intent_revisions",
            program_rows._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
            initialization_module._accepted_intent_parameters(
                plan.accepted_intent_revision
            ),
        ),
        (
            "development_work_item_heads",
            program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
            initialization_module._work_head_parameters(plan.work_item_head),
        ),
        (
            "development_work_item_revisions",
            program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
            initialization_module._work_revision_parameters(plan.work_item_revision),
        ),
        (
            "development_decisions",
            decision_rows._DEVELOPMENT_DECISION_COLUMNS,
            initialization_module._decision_parameters(plan.initialize_decision),
        ),
        (
            "development_program_versions",
            program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
            initialization_module._program_version_parameters(plan.program_version),
        ),
        (
            "development_program_version_work_items",
            program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
            initialization_module._membership_parameters(
                plan.program_version_work_item
            ),
        ),
        (
            "development_work_spec_bindings",
            program_rows._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
            initialization_module._binding_parameters(plan.work_spec_binding),
        ),
    )
    connection = sqlite3.connect(partial.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        for table, columns, parameters in ordered:
            initialization_module._execute_insert(
                connection, table, columns, parameters
            )
        connection.execute("COMMIT")
    finally:
        connection.close()

    fresh = acquire_sqlite_writer_session(partial.location)
    try:
        partial_result = fresh._resolve_development_program_initialization_commit_outcome(
            partial.command
        )
        assert (
            partial_result.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.UNRESOLVED
        )
    finally:
        fresh.close()


def test_fresh_writer_cannot_coexist_with_held_writer_lock(tmp_path: Path) -> None:
    fixture = make_genesis_fixture(tmp_path)
    try:
        with pytest.raises(StateAuthorityLockError):
            acquire_sqlite_writer_session(fixture.location)
    finally:
        fixture.writer_session.close()


def test_same_process_recovery_can_start_after_h2_before_old_t1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path, suffix="pre-x")
    old_session = fixture.writer_session
    old_resource = old_session._resource
    old_generation = old_session.metadata.generation
    reconstructed = command_from_work_spec(
        WorkSpecV1.from_mapping(fixture.work_spec.to_mapping()),
        suffix="pre-x",
    )
    reached_pre_t1 = threading.Event()
    release_t1 = threading.Event()
    original_advance = writer_module._WriterSessionResource._advance_claimed_cleanup_once
    original_commit = transaction_module._commit_transaction

    def commit_then_report_unknown(connection: sqlite3.Connection) -> object:
        assert original_commit(connection) is None
        return transaction_module._SQLITE_COMMIT_FAILED

    def pause_before_t1(self: object, claim: object) -> object:
        if self is old_resource:
            with self._condition:
                state = self._lifecycle_state
                pending = state.pending_state
                cursor = writer_module._cleanup_continuation(pending).cursor
            if type(cursor) is writer_module._CleanupBeforeT1:
                reached_pre_t1.set()
                if not release_t1.wait(10):
                    raise AssertionError("pre-T1 recovery test timed out")
        return original_advance(self, claim)

    monkeypatch.setattr(transaction_module, "_commit_transaction", commit_then_report_unknown)
    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_advance_claimed_cleanup_once",
        pause_before_t1,
    )
    observed_errors: list[BaseException] = []

    def uncertain_apply() -> None:
        try:
            old_session._apply_development_program_initialization(fixture.command)
        except BaseException as error:
            observed_errors.append(error)
        finally:
            old_session.close()

    thread = threading.Thread(target=uncertain_apply)
    thread.start()
    assert reached_pre_t1.wait(10), (
        f"errors={observed_errors!r}; state={type(old_resource._lifecycle_state)!r}; "
        f"alive={thread.is_alive()}"
    )
    assert type(old_resource._lifecycle_state) is not writer_module._WriterSessionTerminalX
    assert old_session.active is False

    fresh = acquire_sqlite_writer_session(fixture.location)
    try:
        assert fresh.metadata.generation == old_generation + 1
        recovered = fresh._resolve_development_program_initialization_commit_outcome(
            reconstructed
        )
        assert (
            recovered.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.COMMITTED_EXACT
        )
        assert type(old_resource._lifecycle_state) is not writer_module._WriterSessionTerminalX
    finally:
        release_t1.set()
        thread.join(10)
        fresh.close()

    assert not thread.is_alive()
    assert len(observed_errors) == 1
    assert type(observed_errors[0]) is SQLiteMutationStoreError
    assert observed_errors[0].error_class == "commit_outcome_unknown"
    assert type(old_resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires POSIX fork")
def test_cross_process_recovery_can_start_after_l1_before_old_h2_or_t1(
    tmp_path: Path,
) -> None:
    fixture = make_genesis_fixture(tmp_path, suffix="cross-process")
    fixture.writer_session.close()
    reconstructed = command_from_work_spec(
        WorkSpecV1.from_mapping(fixture.work_spec.to_mapping()),
        suffix="cross-process",
    )
    reached_read, reached_write = os.pipe()
    release_read, release_write = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(reached_read)
        os.close(release_write)
        old_unlock = authority_lock_module._unlock_authority_descriptor_with_proof
        old_commit = transaction_module._commit_transaction

        def unlock_then_pause(descriptor: int) -> None:
            old_unlock(descriptor)
            os.write(reached_write, b"L1")
            if os.read(release_read, 1) != b"R":
                os._exit(91)

        def commit_then_report_unknown(connection: sqlite3.Connection) -> object:
            if old_commit(connection) is not None:
                os._exit(92)
            return transaction_module._SQLITE_COMMIT_FAILED

        authority_lock_module._unlock_authority_descriptor_with_proof = unlock_then_pause
        transaction_module._commit_transaction = commit_then_report_unknown
        try:
            old = acquire_sqlite_writer_session(fixture.location)
            try:
                old._apply_development_program_initialization(fixture.command)
            except SQLiteMutationStoreError as error:
                if error.error_class != "commit_outcome_unknown":
                    os._exit(93)
            else:
                os._exit(94)
            finally:
                try:
                    old.close()
                except BaseException:
                    pass
        except BaseException:
            os._exit(95)
        os._exit(0)

    os.close(reached_write)
    os.close(release_read)
    fresh = None
    try:
        ready, _, _ = select.select([reached_read], [], [], 10)
        assert ready == [reached_read]
        assert os.read(reached_read, 2) == b"L1"
        fresh = acquire_sqlite_writer_session(fixture.location)
        recovered = fresh._resolve_development_program_initialization_commit_outcome(
            reconstructed
        )
        assert (
            recovered.disposition
            is DevelopmentProgramInitializationRecoveryDispositionV1.COMMITTED_EXACT
        )
    finally:
        if fresh is not None:
            fresh.close()
        try:
            os.write(release_write, b"R")
        except OSError:
            pass
        os.close(reached_read)
        os.close(release_write)
        _, status = os.waitpid(child_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
