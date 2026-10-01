from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
import ge_nwp_coordinator._rw0_c1_semantic_values as semantic_values
import ge_nwp_coordinator._sqlite_rw0_c1 as runtime
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator._rw0_c1_mutation_contracts import (
    RW0C1InsertSpecification,
    build_row,
    relation_reference,
)
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1AdmitEvidenceResultV1,
    RW0C1RecoveryDispositionV1,
    RW0C1RecoveryProbeV1,
    RW0C1RecoveryResultV1,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_c1_private_atomic_persistence import (
    _mechanics_values,
    admission_command,
    make_c1_harness,
    valid_rank1_value,
)
from test_rw0_b2_wire_values import worker_observation


def _phase_probe(harness: object) -> RW0C1RecoveryProbeV1:
    command = harness.phase_command
    result = harness.phase_result
    return RW0C1RecoveryProbeV1(
        "establish_rw0_phase",
        command.mutation_ref,
        command.command_digest,
        result.phase_basis_ref,
        result.phase_basis_digest,
        k8=tuple(member for _name, member in command.phase_basis.selection_key),
    )


def _evidence_selector(command: object) -> object:
    """Use the new stable selector, with a red-gate-only legacy fallback."""

    constructor = getattr(
        semantic_values,
        "evidence_admission_recovery_selector",
        None,
    )
    if callable(constructor):
        return constructor(command)
    return RW0C1RecoveryProbeV1(
        "admit_rw0_evidence",
        command.mutation_ref,
        command.command_digest,
        command.phase_basis_ref,
        command.phase_basis_digest,
        command.preassigned_membership_ref,
        "0" * 64,
    )


def _fresh_writer(harness: object) -> object:
    return acquire_sqlite_writer_session(
        harness.bundle["author_fixture"].location
    )


def _admit_valid_rank1(
    harness: object,
    monkeypatch: pytest.MonkeyPatch,
    *,
    sequence: int,
) -> tuple[object, RW0C1AdmitEvidenceResultV1]:
    command = admission_command(
        harness,
        rank=1,
        value=valid_rank1_value(harness),
        sequence=sequence,
    )
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    result = harness.writer._admit_rw0_evidence(command)
    assert type(result) is RW0C1AdmitEvidenceResultV1
    return command, result


def test_phase_recovery_is_committed_exact_without_clock_or_mutable_heads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="recover-phase")
    probe = _phase_probe(harness)
    harness.close()
    writer = _fresh_writer(harness)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("historical recovery consulted mutable state or clock")

    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", forbidden)
    monkeypatch.setattr(runtime, "_read_phase_selection_owner_rows", forbidden)
    monkeypatch.setattr(runtime, "_read_phase_development_owner_rows", forbidden)
    monkeypatch.setattr(runtime, "_read_global_stop_current", forbidden)
    try:
        recovered = writer._resolve_rw0_c1_phase_establishment_commit_outcome(
            probe
        )
        assert type(recovered) is RW0C1RecoveryResultV1
        assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
        assert recovered.operation_graph_digest == harness.phase_result.phase_graph_digest
        assert recovered.receipt_digest == harness.phase_result.receipt_digest
    finally:
        writer.close()


def test_evidence_recovery_reruns_owner_at_persisted_time_not_current_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix="recover-evidence-time",
        timestamp="2029-01-01T00:00:00Z",
    )
    command = admission_command(
        harness,
        rank=1,
        value=valid_rank1_value(harness),
        sequence=401,
    )
    selector = _evidence_selector(command)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    admitted = harness.writer._admit_rw0_evidence(command)
    assert type(admitted) is RW0C1AdmitEvidenceResultV1
    harness.close()
    writer = _fresh_writer(harness)
    observed_times: list[str] = []
    owner = b1.validate_authority_observation

    def counted_owner(**kwargs: object) -> None:
        observed_times.append(kwargs["now_utc"])
        owner(**kwargs)

    monkeypatch.setattr(b1, "validate_authority_observation", counted_owner)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: (_ for _ in ()).throw(AssertionError("recovery captured a clock")),
    )
    try:
        recovered = writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert type(recovered) is RW0C1RecoveryResultV1
        assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
        assert recovered.operation_graph_digest == admitted.admission_graph_digest
        assert observed_times == [admitted.committed_at]
    finally:
        writer.close()


def test_absent_phase_and_evidence_families_are_definitely_not_committed(
    tmp_path: Path,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="recover-absent")
    phase_probe = RW0C1RecoveryProbeV1(
        "establish_rw0_phase",
        "mutation.rw0-c1.absent.phase",
        "a" * 64,
        "phase.rw0-c1.absent",
        "b" * 64,
        k8=tuple(f"absent-k8-{index}" for index in range(8)),
    )
    evidence_command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=402,
    )
    evidence_selector = _evidence_selector(evidence_command)
    try:
        phase = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
            phase_probe
        )
        member = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            evidence_selector
        )
        assert phase.disposition is RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        assert member.disposition is RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        assert phase.receipt_digest is member.receipt_digest is None
    finally:
        harness.close()


def test_orphan_relation_operand_for_absent_member_is_unresolved(
    tmp_path: Path,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="recover-orphan")
    command = admission_command(
        harness,
        rank=1,
        value=valid_rank1_value(harness),
        sequence=403,
    )
    selector = _evidence_selector(command)
    relation_ref = relation_reference(
        phase_basis_ref=command.phase_basis_ref,
        phase_basis_digest=command.phase_basis_digest,
        subject_type="evidence_membership",
        subject_membership_ref=command.preassigned_membership_ref,
        relation_rank=0,
    )
    row = build_row(
        "rw0_relation_operands",
        {
            "schema_id": "governed-execution.nwp-rw0-c1-relation-operand.v1",
            "phase_basis_ref": command.phase_basis_ref,
            "relation_ref": relation_ref,
            "relation_digest": "3" * 64,
            "operand_ordinal": 0,
            "operand_role": "attempt_fence",
            "operand_source": "existing_owner_row",
            "source_membership_ref": None,
            "source_membership_digest": None,
            "source_kind_rank": None,
            "owner_role": "development_attempt_fence",
            "owner_locator_ref": "attempt.fence.orphan",
            "owner_locator_revision": None,
            "owner_locator_subrole": None,
            "owner_locator_ordinal": None,
            "transient_binding_kind": None,
            "transient_error_reason": None,
            "snapshot_binding_kind": None,
            "operand_schema_id": "governed-execution.nwp-attempt-fence.v1",
            "operand_ref": "attempt.fence.orphan",
            "operand_digest": "4" * 64,
            "operand_scope_digest": None,
        },
    )
    connection = sqlite3.connect(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (0,)
        connection.execute(
            "INSERT INTO rw0_relation_operands VALUES ("
            + ",".join("?" for _ in row.as_tuple())
            + ")",
            row.as_tuple(),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert type(recovered) is RW0C1RecoveryResultV1
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


@pytest.mark.parametrize("fragment", ("membership", "receipt"))
def test_evidence_recovery_rejects_membership_and_receipt_fragments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fragment: str,
) -> None:
    harness = make_c1_harness(tmp_path, suffix=f"recover-{fragment}-fragment")
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=404,
    )
    selector = _evidence_selector(command)
    if fragment == "membership":
        monkeypatch.setattr(
            runtime,
            "_read_membership_by_ref",
            lambda *_a: object(),
        )
    else:
        monkeypatch.setattr(runtime, "_read_receipt", lambda *_a: object())
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


@pytest.mark.parametrize("commit_reaches_disk", (False, True))
def test_commit_uncertainty_has_no_retry_and_resolves_three_ways(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    commit_reaches_disk: bool,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"uncertain-{commit_reaches_disk}",
        timestamp="2029-01-01T00:00:00Z",
    )
    command = admission_command(
        harness,
        rank=1,
        value=valid_rank1_value(harness),
        sequence=410 + int(commit_reaches_disk),
    )
    selector = _evidence_selector(command)
    original_commit = transaction._commit_transaction
    calls: list[sqlite3.Connection] = []

    def uncertain(connection: sqlite3.Connection) -> object:
        calls.append(connection)
        if commit_reaches_disk:
            assert original_commit(connection) is None
        return transaction._SQLITE_COMMIT_FAILED

    monkeypatch.setattr(transaction, "_commit_transaction", uncertain)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    with pytest.raises(SQLiteMutationStoreError) as caught:
        harness.writer._admit_rw0_evidence(command)
    assert caught.value.error_class == "commit_outcome_unknown"
    assert caught.value.args == ("commit_outcome_unknown",)
    assert len(calls) == 1
    harness.close()

    monkeypatch.setattr(transaction, "_commit_transaction", original_commit)
    writer = _fresh_writer(harness)
    try:
        recovered = writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        expected = (
            RW0C1RecoveryDispositionV1.COMMITTED_EXACT
            if commit_reaches_disk
            else RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
        assert recovered.disposition is expected
        assert len(calls) == 1
    finally:
        writer.close()


def test_recovery_read_and_rollback_cleanup_faults_collapse_to_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="recover-faults")
    probe = _phase_probe(harness)

    monkeypatch.setattr(
        runtime,
        "_read_receipt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("private")),
    )
    read_fault = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
        probe
    )
    assert read_fault.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED

    monkeypatch.undo()
    monkeypatch.setattr(
        transaction,
        "_rollback_transaction",
        lambda _connection: transaction._mutation_failed(),
    )
    cleanup_fault = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
        probe
    )
    assert cleanup_fault.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    harness.close()


@pytest.mark.parametrize(
    "boundary",
    ("write", "guarded_readback", "capability_invalidation"),
)
def test_precommit_write_readback_and_capability_faults_roll_back_without_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    safe_suffix = {
        "write": "precommit-write",
        "guarded_readback": "precommit-readback",
        "capability_invalidation": "precommit-capability",
    }[boundary]
    harness = make_c1_harness(tmp_path, suffix=safe_suffix)
    command = admission_command(
        harness,
        rank=1,
        value=valid_rank1_value(harness),
        sequence={
            "write": 451,
            "guarded_readback": 452,
            "capability_invalidation": 453,
        }[boundary],
    )
    original_commit = transaction._commit_transaction
    commits: list[sqlite3.Connection] = []

    def counted_commit(connection: sqlite3.Connection) -> object:
        commits.append(connection)
        return original_commit(connection)

    monkeypatch.setattr(transaction, "_commit_transaction", counted_commit)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    if boundary == "write":
        original = transaction._RW0_C1_INSERT_SPEC_BY_TABLE[
            "rw0_evidence_values"
        ]
        monkeypatch.setitem(
            transaction._RW0_C1_INSERT_SPEC_BY_TABLE,
            "rw0_evidence_values",
            RW0C1InsertSpecification(
                original.table_name,
                original.columns,
                "INSERT INTO rw0_c1_missing_fault_table VALUES (?)",
            ),
        )
    elif boundary == "guarded_readback":
        monkeypatch.setattr(
            transaction,
            "_readback_rw0_c1_evidence_admission",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("private")),
        )
    else:
        monkeypatch.setattr(
            transaction,
            "_invalidate_sqlite_mutation_read_capability",
            lambda *_args, **_kwargs: transaction._mutation_failed(),
        )

    try:
        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
        expected_error = (
            "database_integrity_failure"
            if boundary == "write"
            else "mutation_failed"
        )
        assert caught.value.error_class == expected_error
        assert caught.value.args == (expected_error,)
        assert commits == []
        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute(
                "SELECT count(*) FROM rw0_evidence_memberships "
                "WHERE membership_ref=?",
                (command.preassigned_membership_ref,),
            ).fetchone() == (0,)
            assert connection.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts "
                "WHERE mutation_ref=?",
                (command.mutation_ref,),
            ).fetchone() == (0,)
        finally:
            connection.close()
    finally:
        harness.close()


def test_recovery_unproved_connection_cleanup_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="recover-close-fault")
    probe = _phase_probe(harness)
    original_close = transaction._ControllerConnectionScope.close_before_commit

    def close_but_do_not_prove(self: object) -> bool:
        original_close(self)
        return False

    monkeypatch.setattr(
        transaction._ControllerConnectionScope,
        "close_before_commit",
        close_but_do_not_prove,
    )
    try:
        recovered = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
            probe
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


@pytest.mark.parametrize(
    "missing_prerequisite",
    ("phase", "membership", "owner"),
)
def test_evidence_recovery_requires_exact_immutable_prerequisites_for_dnc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing_prerequisite: str,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"recover-missing-{missing_prerequisite}",
    )
    values_by_rank = _mechanics_values(harness)
    if missing_prerequisite == "membership":
        missing = semantic_values.RW0C1MemberLocatorV1(
            "authority_observation",
            1,
            "membership.rw0-c1.recovery-missing",
            "a" * 64,
            "authority.observation.recovery-missing",
            "b" * 64,
        )
        command = admission_command(
            harness,
            rank=2,
            value=values_by_rank[2],
            sequence=470,
            dependencies=(missing,),
        )
    elif missing_prerequisite == "owner":
        command = admission_command(
            harness,
            rank=1,
            value=valid_rank1_value(harness),
            sequence=471,
        )
        monkeypatch.setattr(runtime, "_read_command_owner_row", lambda *_a: None)
    else:
        command = admission_command(
            harness,
            rank=5,
            value=values_by_rank[5],
            sequence=472,
        )
        monkeypatch.setattr(runtime, "_read_phase_by_pair", lambda *_a: None)
    selector = _evidence_selector(command)
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


@pytest.mark.parametrize(
    "registry_posture",
    ("ref_alias", "digest_alias", "registry_only", "payload_only"),
)
def test_evidence_recovery_rejects_registry_aliases_and_partial_families(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    registry_posture: str,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"recover-registry-{registry_posture.replace('_', '-')}",
    )
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=480,
    )
    selector = _evidence_selector(command)
    value_ref, value_digest, value_schema_id, scope_class, _mapping = (
        semantic_values.evidence_identity(command.evidence_value, command.kind_rank)
    )
    registry = build_row(
        "rw0_evidence_values",
        {
            "schema_id": "governed-execution.nwp-rw0-c1-evidence-value-row.v1",
            "kind_rank": command.kind_rank,
            "value_ref": value_ref,
            "value_digest": value_digest,
            "value_schema_id": value_schema_id,
            "scope_class": scope_class,
        },
    )
    monkeypatch.setattr(
        runtime,
        "_read_registry_by_kind_ref",
        lambda *_a: registry if registry_posture in {"ref_alias", "registry_only"} else None,
    )
    monkeypatch.setattr(
        runtime,
        "_read_registry_by_kind_digest",
        lambda *_a: registry if registry_posture in {"digest_alias", "registry_only"} else None,
    )
    monkeypatch.setattr(
        runtime,
        "_read_typed_payload_by_kind_ref",
        lambda *_a, **_kw: object() if registry_posture == "payload_only" else None,
    )
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


def test_evidence_recovery_allows_exact_reusable_registry_for_dnc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="recover-reusable-registry")
    evidence_value = _mechanics_values(harness)[5]
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    admitted = admission_command(
        harness,
        rank=5,
        value=evidence_value,
        sequence=490,
    )
    assert type(harness.writer._admit_rw0_evidence(admitted)) is RW0C1AdmitEvidenceResultV1
    retry = admission_command(
        harness,
        rank=5,
        value=evidence_value,
        sequence=491,
    )
    selector = _evidence_selector(retry)
    monkeypatch.setattr(
        runtime,
        "_read_membership_by_phase_kind_ref",
        lambda *_a: None,
    )
    monkeypatch.setattr(
        runtime,
        "_read_membership_by_phase_kind_digest",
        lambda *_a: None,
    )
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert (
            recovered.disposition
            is RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
    finally:
        harness.close()


@pytest.mark.parametrize(
    "cleanup_boundary",
    ("mutation_slot", "controller_connection", "operation_lease"),
)
def test_postcommit_cleanup_failures_are_unknown_and_selector_recovers_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cleanup_boundary: str,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"postcommit-{cleanup_boundary.replace('_', '-')}",
    )
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence={
            "mutation_slot": 501,
            "controller_connection": 502,
            "operation_lease": 503,
        }[cleanup_boundary],
    )
    selector = _evidence_selector(command)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )

    with monkeypatch.context() as fault:
        if cleanup_boundary == "mutation_slot":
            original = writer_module._WriterSessionMutationLease._close
            fired = False

            def fail_after_mutation_close(lease: object) -> None:
                nonlocal fired
                original(lease)
                if not fired:
                    fired = True
                    raise RuntimeError("private mutation-slot close fault")

            fault.setattr(
                writer_module._WriterSessionMutationLease,
                "_close",
                fail_after_mutation_close,
            )
        elif cleanup_boundary == "controller_connection":
            original = transaction._ControllerConnectionScope.close_after_commit

            def fail_after_connection_close(scope: object, **kwargs: object) -> bool:
                original(scope, **kwargs)
                raise RuntimeError("private connection close fault")

            fault.setattr(
                transaction._ControllerConnectionScope,
                "close_after_commit",
                fail_after_connection_close,
            )
        else:
            original = writer_module._WriterSessionOperationLease._close
            fired = False

            def fail_after_operation_close(lease: object) -> None:
                nonlocal fired
                original(lease)
                if not fired:
                    fired = True
                    raise RuntimeError("private operation-lease close fault")

            fault.setattr(
                writer_module._WriterSessionOperationLease,
                "_close",
                fail_after_operation_close,
            )

        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
        assert caught.value.error_class == "commit_outcome_unknown"
        assert caught.value.args == ("commit_outcome_unknown",)

    harness.close()
    writer = _fresh_writer(harness)
    try:
        recovered = writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
    finally:
        writer.close()


def _insert_with_foreign_keys_disabled(
    database_path: Path,
    sql: str,
    values: tuple[object, ...],
) -> None:
    connection = sqlite3.connect(database_path)
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (0,)
        connection.execute(sql, values)
        connection.commit()
    finally:
        connection.close()


def _recover_evidence_after_failed_apply(
    harness: object,
    selector: object,
) -> RW0C1RecoveryResultV1:
    harness.close()
    writer = _fresh_writer(harness)
    try:
        recovered = writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert type(recovered) is RW0C1RecoveryResultV1
        return recovered
    finally:
        writer.close()


def test_reaudit_result_publication_fault_after_real_commit_is_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="reaudit-result-publication")
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=8801,
    )
    selector = _evidence_selector(command)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    original = (
        transaction._CoordinatorMutationTransactionController
        ._commit_fresh_rw0_c1_plan
    )

    def fail_after_committed_result(self: object, plan: object) -> object:
        committed = original(self, plan)
        assert type(committed) is RW0C1AdmitEvidenceResultV1
        assert committed.disposition == "fresh_committed"
        raise RuntimeError("private committed-result publication fault")

    with monkeypatch.context() as fault:
        fault.setattr(
            transaction._CoordinatorMutationTransactionController,
            "_commit_fresh_rw0_c1_plan",
            fail_after_committed_result,
        )
        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
    assert caught.value.error_class == "commit_outcome_unknown"
    assert caught.value.args == ("commit_outcome_unknown",)

    recovered = _recover_evidence_after_failed_apply(harness, selector)
    assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
    connection = sqlite3.connect(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        assert connection.execute(
            "SELECT count(*) FROM rw0_evidence_memberships "
            "WHERE membership_ref = ?",
            (command.preassigned_membership_ref,),
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT count(*) FROM rw0_c1_mutation_receipts "
            "WHERE mutation_ref = ?",
            (command.mutation_ref,),
        ).fetchone() == (1,)
    finally:
        connection.close()


def test_reaudit_payload_digest_alias_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = make_c1_harness(tmp_path, suffix="reaudit-payload-source")
    target = make_c1_harness(tmp_path, suffix="reaudit-payload-target")
    value = _mechanics_values(source)[5]
    source_command = admission_command(
        source,
        rank=5,
        value=value,
        sequence=8802,
    )
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    source.writer._admit_rw0_evidence(source_command)
    source_connection = sqlite3.connect(
        source.bundle["author_fixture"].location.database_path
    )
    try:
        columns = tuple(
            row[1]
            for row in source_connection.execute(
                "PRAGMA table_info(rw0_remote_host_readiness_observations)"
            )
        )
        raw_row = source_connection.execute(
            "SELECT "
            + ",".join(columns)
            + " FROM rw0_remote_host_readiness_observations"
        ).fetchone()
        assert raw_row is not None
        source_mapping = dict(zip(columns, raw_row, strict=True))
    finally:
        source_connection.close()

    target_command = admission_command(
        target,
        rank=5,
        value=value,
        sequence=8803,
    )
    selector = _evidence_selector(target_command)
    source_mapping.pop("payload_row_digest")
    source_mapping["value_ref"] = "readiness.reaudit.digest-alias"
    alias_row = build_row(
        "rw0_remote_host_readiness_observations",
        source_mapping,
    )
    _insert_with_foreign_keys_disabled(
        target.bundle["author_fixture"].location.database_path,
        "INSERT INTO rw0_remote_host_readiness_observations VALUES ("
        + ",".join("?" for _ in alias_row.as_tuple())
        + ")",
        alias_row.as_tuple(),
    )
    try:
        recovered = target.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        source.close()
        target.close()


def test_reaudit_recovery_mutation_lease_close_fault_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="reaudit-recovery-mutation-close")
    probe = _phase_probe(harness)
    original = writer_module._WriterSessionMutationLease._close
    fired = False

    def fail_after_real_close(lease: object) -> None:
        nonlocal fired
        original(lease)
        if not fired:
            fired = True
            raise SQLiteMutationStoreError(
                SQLiteMutationStoreErrorCode.MUTATION_FAILED
            )

    monkeypatch.setattr(
        writer_module._WriterSessionMutationLease,
        "_close",
        fail_after_real_close,
    )
    try:
        recovered = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
            probe
        )
        assert type(recovered) is RW0C1RecoveryResultV1
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


def _assert_single_evidence_commit(harness: object, command: object) -> None:
    connection = sqlite3.connect(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        assert connection.execute(
            "SELECT count(*) FROM rw0_evidence_memberships "
            "WHERE membership_ref = ?",
            (command.preassigned_membership_ref,),
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT count(*) FROM rw0_c1_mutation_receipts "
            "WHERE mutation_ref = ?",
            (command.mutation_ref,),
        ).fetchone() == (1,)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "boundary",
    (
        "controller_return",
        "module_delegate_return",
        "controller_connection_cleanup",
        "mutation_slot_close",
        "operation_lease_close",
        "process_stabilization",
        "writer_post_operation_cleanup",
    ),
)
def test_reaudit_cross_layer_postcommit_fault_matrix_is_unknown_and_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    sequence = {
        "controller_return": 8810,
        "module_delegate_return": 8811,
        "controller_connection_cleanup": 8812,
        "mutation_slot_close": 8813,
        "operation_lease_close": 8814,
        "process_stabilization": 8815,
        "writer_post_operation_cleanup": 8816,
    }[boundary]
    harness = make_c1_harness(tmp_path, suffix=f"reaudit-{boundary.replace('_', '-')}")
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=sequence,
    )
    selector = _evidence_selector(command)
    original_commit = transaction._commit_transaction
    commit_calls: list[sqlite3.Connection] = []

    def counted_commit(connection: sqlite3.Connection) -> object:
        commit_calls.append(connection)
        return original_commit(connection)

    monkeypatch.setattr(transaction, "_commit_transaction", counted_commit)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    with monkeypatch.context() as fault:
        if boundary == "controller_return":
            original = (
                transaction._CoordinatorMutationTransactionController
                .run_atomic_rw0_c1_evidence_admission
            )

            def fail_after_controller_return(
                controller: object,
                *,
                command: object,
            ) -> object:
                committed = original(controller, command=command)
                assert type(committed) is RW0C1AdmitEvidenceResultV1
                raise RuntimeError("private controller-return fault")

            fault.setattr(
                transaction._CoordinatorMutationTransactionController,
                "run_atomic_rw0_c1_evidence_admission",
                fail_after_controller_return,
            )
        elif boundary == "module_delegate_return":
            original_delegate = transaction._run_atomic_rw0_c1_evidence_admission

            def fail_after_module_delegate(**kwargs: object) -> object:
                committed = original_delegate(**kwargs)
                assert type(committed) is RW0C1AdmitEvidenceResultV1
                raise RuntimeError("private module-delegate-return fault")

            fault.setattr(
                transaction,
                "_run_atomic_rw0_c1_evidence_admission",
                fail_after_module_delegate,
            )
        elif boundary == "controller_connection_cleanup":
            original_close = (
                transaction._ControllerConnectionScope.close_after_commit
            )

            def fail_after_controller_connection_close(
                scope: object,
                **kwargs: object,
            ) -> bool:
                original_close(scope, **kwargs)
                raise RuntimeError("private controller-connection cleanup fault")

            fault.setattr(
                transaction._ControllerConnectionScope,
                "close_after_commit",
                fail_after_controller_connection_close,
            )
        elif boundary == "mutation_slot_close":
            original_mutation_close = writer_module._WriterSessionMutationLease._close
            fired = False

            def fail_after_mutation_slot_close(lease: object) -> None:
                nonlocal fired
                original_mutation_close(lease)
                if not fired:
                    fired = True
                    raise RuntimeError("private mutation-slot cleanup fault")

            fault.setattr(
                writer_module._WriterSessionMutationLease,
                "_close",
                fail_after_mutation_slot_close,
            )
        elif boundary == "operation_lease_close":
            original_operation_close = writer_module._WriterSessionOperationLease._close
            fired = False

            def fail_after_operation_lease_close(lease: object) -> None:
                nonlocal fired
                original_operation_close(lease)
                if not fired:
                    fired = True
                    raise RuntimeError("private operation-lease cleanup fault")

            fault.setattr(
                writer_module._WriterSessionOperationLease,
                "_close",
                fail_after_operation_lease_close,
            )
        elif boundary == "process_stabilization":
            fault.setattr(
                writer_module,
                "_stabilize_rw0_c1_outer_operation_close",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("private process-stabilization fault")
                ),
            )
        else:
            fault.setattr(
                writer_module,
                "_complete_rw0_c1_writer_post_operation",
                lambda **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("private writer post-operation cleanup fault")
                ),
            )

        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
        assert caught.value.error_class == "commit_outcome_unknown"
        assert caught.value.args == ("commit_outcome_unknown",)
        assert len(commit_calls) == 1

    recovered = _recover_evidence_after_failed_apply(harness, selector)
    assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
    _assert_single_evidence_commit(harness, command)


@pytest.mark.parametrize(
    "safe_code",
    (
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE,
        SQLiteMutationStoreErrorCode.MUTATION_FAILED,
    ),
)
def test_reaudit_safe_operation_retirement_after_commit_is_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    safe_code: SQLiteMutationStoreErrorCode,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"reaudit-safe-retirement-{safe_code.value.replace('_', '-')}",
    )
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=8820 + int(
            safe_code is SQLiteMutationStoreErrorCode.MUTATION_FAILED
        ),
    )
    selector = _evidence_selector(command)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    original = writer_module._WriterSessionOperationLease._close
    fired = False

    def fail_after_real_close(lease: object) -> None:
        nonlocal fired
        original(lease)
        if not fired:
            fired = True
            raise SQLiteMutationStoreError(safe_code)

    with monkeypatch.context() as fault:
        fault.setattr(
            writer_module._WriterSessionOperationLease,
            "_close",
            fail_after_real_close,
        )
        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
    assert caught.value.error_class == "commit_outcome_unknown"
    recovered = _recover_evidence_after_failed_apply(harness, selector)
    assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
    _assert_single_evidence_commit(harness, command)


def test_reaudit_payload_ref_alias_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = make_c1_harness(tmp_path, suffix="reaudit-ref-alias-source")
    target = make_c1_harness(tmp_path, suffix="reaudit-ref-alias-target")
    value = _mechanics_values(source)[5]
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    source.writer._admit_rw0_evidence(
        admission_command(source, rank=5, value=value, sequence=8830)
    )
    source_connection = sqlite3.connect(
        source.bundle["author_fixture"].location.database_path
    )
    try:
        columns = tuple(
            row[1]
            for row in source_connection.execute(
                "PRAGMA table_info(rw0_remote_host_readiness_observations)"
            )
        )
        raw_row = source_connection.execute(
            "SELECT "
            + ",".join(columns)
            + " FROM rw0_remote_host_readiness_observations"
        ).fetchone()
        assert raw_row is not None
        mapping = dict(zip(columns, raw_row, strict=True))
    finally:
        source_connection.close()
    command = admission_command(target, rank=5, value=value, sequence=8831)
    selector = _evidence_selector(command)
    mapping.pop("payload_row_digest")
    mapping["value_digest"] = (
        "0" * 64 if selector.value_digest != "0" * 64 else "1" * 64
    )
    alias_row = build_row("rw0_remote_host_readiness_observations", mapping)
    _insert_with_foreign_keys_disabled(
        target.bundle["author_fixture"].location.database_path,
        "INSERT INTO rw0_remote_host_readiness_observations VALUES ("
        + ",".join("?" for _ in alias_row.as_tuple())
        + ")",
        alias_row.as_tuple(),
    )
    try:
        recovered = target.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        source.close()
        target.close()


@pytest.mark.parametrize(
    ("rank", "identity_route"),
    ((1, "ref"), (1, "digest"), (12, "ref"), (12, "digest")),
)
def test_reaudit_child_only_identity_routes_are_unresolved(
    tmp_path: Path,
    rank: int,
    identity_route: str,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"reaudit-rank{rank}-child-{identity_route}",
    )
    value = (
        valid_rank1_value(harness)
        if rank == 1
        else worker_observation(
            "worker_started",
            f"observation.c1.reaudit-child-{identity_route}.0001",
        )
    )
    command = admission_command(
        harness,
        rank=rank,
        value=value,
        sequence=8840 + rank + int(identity_route == "digest"),
    )
    selector = _evidence_selector(command)
    child_ref = (
        selector.value_ref
        if identity_route == "ref"
        else f"value.reaudit.rank{rank}.child-alias"
    )
    child_digest = (
        selector.value_digest
        if identity_route == "digest"
        else ("0" * 64 if selector.value_digest != "0" * 64 else "1" * 64)
    )
    if rank == 1:
        child = build_row(
            "rw0_authority_observation_effect_classes",
            {
                "schema_id": (
                    "governed-execution.nwp-rw0-c1-"
                    "authority-effect-class-row.v1"
                ),
                "kind_rank": 1,
                "value_ref": child_ref,
                "value_digest": child_digest,
                "ordinal": 0,
                "effect_class": value.allowed_effect_classes[0],
            },
        )
    else:
        child = build_row(
            "rw0_c2a_worker_observation_evidence_refs",
            {
                "schema_id": (
                    "governed-execution.nwp-rw0-c1-"
                    "worker-observation-evidence-ref-row.v1"
                ),
                "kind_rank": 12,
                "value_ref": child_ref,
                "value_digest": child_digest,
                "ordinal": 0,
                "evidence_ref": "evidence.reaudit.child-only.0001",
            },
        )
    _insert_with_foreign_keys_disabled(
        harness.bundle["author_fixture"].location.database_path,
        f"INSERT INTO {child.table_name} VALUES ("
        + ",".join("?" for _ in child.as_tuple())
        + ")",
        child.as_tuple(),
    )
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


@pytest.mark.parametrize("fragment", ("binding", "operand"))
def test_reaudit_relation_identity_is_global_across_phases(
    tmp_path: Path,
    fragment: str,
) -> None:
    harness = make_c1_harness(tmp_path, suffix=f"reaudit-global-{fragment}")
    command = admission_command(
        harness,
        rank=1,
        value=valid_rank1_value(harness),
        sequence=8850 + int(fragment == "operand"),
    )
    selector = _evidence_selector(command)
    relation_ref = relation_reference(
        phase_basis_ref=command.phase_basis_ref,
        phase_basis_digest=command.phase_basis_digest,
        subject_type="evidence_membership",
        subject_membership_ref=command.preassigned_membership_ref,
        relation_rank=0,
    )
    if fragment == "binding":
        row = build_row(
            "rw0_relation_bindings",
            {
                "schema_id": (
                    "governed-execution.nwp-rw0-c1-relation-binding.v1"
                ),
                "phase_basis_ref": "phase.reaudit.foreign",
                "phase_basis_digest": command.phase_basis_digest,
                "relation_ref": relation_ref,
                "relation_digest": "3" * 64,
                "subject_type": "evidence_membership",
                "subject_membership_ref": command.preassigned_membership_ref,
                "subject_membership_digest": "4" * 64,
                "subject_kind_rank": command.kind_rank,
                "subject_value_ref": selector.value_ref,
                "subject_value_digest": selector.value_digest,
                "subject_value_schema_id": selector.value_schema_id,
                "relation_rank": 0,
                "relation_schema_id": (
                    "governed-execution.nwp-rw0-c1-"
                    "authority-verification-observation-relation.v1"
                ),
                "relation_version": 1,
                "proof_mode": "relation_recomputable",
                "profile_ref": None,
                "profile_digest": None,
                "evaluated_at": "2029-01-01T00:00:00Z",
                "operand_count": 1,
                "operand_set_digest": "5" * 64,
            },
        )
    else:
        row = build_row(
            "rw0_relation_operands",
            {
                "schema_id": (
                    "governed-execution.nwp-rw0-c1-relation-operand.v1"
                ),
                "phase_basis_ref": "phase.reaudit.foreign",
                "relation_ref": relation_ref,
                "relation_digest": "3" * 64,
                "operand_ordinal": 0,
                "operand_role": "attempt_fence",
                "operand_source": "existing_owner_row",
                "source_membership_ref": None,
                "source_membership_digest": None,
                "source_kind_rank": None,
                "owner_role": "development_attempt_fence",
                "owner_locator_ref": "attempt.fence.reaudit-orphan",
                "owner_locator_revision": None,
                "owner_locator_subrole": None,
                "owner_locator_ordinal": None,
                "transient_binding_kind": None,
                "transient_error_reason": None,
                "snapshot_binding_kind": None,
                "operand_schema_id": "governed-execution.nwp-attempt-fence.v1",
                "operand_ref": "attempt.fence.reaudit-orphan",
                "operand_digest": "4" * 64,
                "operand_scope_digest": None,
            },
        )
    _insert_with_foreign_keys_disabled(
        harness.bundle["author_fixture"].location.database_path,
        f"INSERT INTO {row.table_name} VALUES ("
        + ",".join("?" for _ in row.as_tuple())
        + ")",
        row.as_tuple(),
    )
    try:
        recovered = harness.writer._resolve_rw0_c1_evidence_admission_commit_outcome(
            selector
        )
        assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    finally:
        harness.close()


@pytest.mark.parametrize(
    "boundary",
    ("operation_lease_close", "outer_writer_cleanup"),
)
def test_reaudit_recovery_outer_cleanup_faults_are_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"reaudit-recovery-{boundary.replace('_', '-')}",
    )
    probe = _phase_probe(harness)
    with monkeypatch.context() as fault:
        if boundary == "operation_lease_close":
            original = writer_module._WriterSessionOperationLease._close
            fired = False

            def fail_after_real_close(lease: object) -> None:
                nonlocal fired
                original(lease)
                if not fired:
                    fired = True
                    raise RuntimeError("private recovery operation-close fault")

            fault.setattr(
                writer_module._WriterSessionOperationLease,
                "_close",
                fail_after_real_close,
            )
        else:
            fault.setattr(
                writer_module,
                "_complete_rw0_c1_writer_post_operation",
                lambda **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("private recovery outer-writer cleanup fault")
                ),
            )
        recovered = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
            probe
        )
    assert type(recovered) is RW0C1RecoveryResultV1
    assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    harness.close()


def test_final_handoff_fault_after_committed_apply_is_unknown_and_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="final-handoff-committed-apply")
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=8901,
    )
    selector = _evidence_selector(command)
    original_commit = transaction._commit_transaction
    commit_calls: list[sqlite3.Connection] = []

    def counted_commit(connection: sqlite3.Connection) -> object:
        commit_calls.append(connection)
        return original_commit(connection)

    monkeypatch.setattr(transaction, "_commit_transaction", counted_commit)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    original_complete = writer_module._complete_rw0_c1_writer_post_operation

    def fail_after_close_proof(**kwargs: object) -> None:
        original_complete(**kwargs)
        witness = kwargs["commit_close_witness"]
        assert witness.state == "close_proof_complete"
        raise RuntimeError("private final apply handoff fault")

    with monkeypatch.context() as fault:
        fault.setattr(
            writer_module,
            "_complete_rw0_c1_writer_post_operation",
            fail_after_close_proof,
        )
        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
    assert caught.value.error_class == "commit_outcome_unknown"
    assert caught.value.args == ("commit_outcome_unknown",)
    assert len(commit_calls) == 1

    recovered = _recover_evidence_after_failed_apply(harness, selector)
    assert recovered.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT
    _assert_single_evidence_commit(harness, command)


def test_final_handoff_fault_after_computed_recovery_is_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="final-handoff-recovery")
    probe = _phase_probe(harness)
    original_complete = writer_module._complete_rw0_c1_writer_post_operation

    def fail_after_close_proof(**kwargs: object) -> None:
        original_complete(**kwargs)
        witness = kwargs["recovery_close_witness"]
        assert witness.result_computed is True
        raise RuntimeError("private final recovery handoff fault")

    with monkeypatch.context() as fault:
        fault.setattr(
            writer_module,
            "_complete_rw0_c1_writer_post_operation",
            fail_after_close_proof,
        )
        recovered = harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
            probe
        )
    assert type(recovered) is RW0C1RecoveryResultV1
    assert recovered.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    harness.close()


def test_invalid_recovery_primary_safe_error_survives_operation_cleanup_fault(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="primary-safe-cleanup")
    original_close = writer_module._WriterSessionOperationLease._close
    fired = False

    def fail_after_real_close(lease: object) -> None:
        nonlocal fired
        original_close(lease)
        if not fired:
            fired = True
            raise RuntimeError("private secondary operation cleanup fault")

    monkeypatch.setattr(
        writer_module._WriterSessionOperationLease,
        "_close",
        fail_after_real_close,
    )
    try:
        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._resolve_rw0_c1_phase_establishment_commit_outcome(
                object()
            )
        assert caught.value.error_class == "mutation_failed"
        assert caught.value.args == ("mutation_failed",)
        assert caught.value.internal_detail is None
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None
    finally:
        harness.close()


def test_exact_replay_operation_cleanup_fault_is_mutation_failed_without_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="replay-cleanup")
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=8902,
    )
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: "2029-01-01T00:00:00Z",
    )
    committed = harness.writer._admit_rw0_evidence(command)
    assert type(committed) is RW0C1AdmitEvidenceResultV1
    assert committed.disposition == "fresh_committed"
    original_commit = transaction._commit_transaction
    commit_calls: list[sqlite3.Connection] = []

    def counted_commit(connection: sqlite3.Connection) -> object:
        commit_calls.append(connection)
        return original_commit(connection)

    original_close = writer_module._WriterSessionOperationLease._close
    fired = False

    def fail_after_real_close(lease: object) -> None:
        nonlocal fired
        original_close(lease)
        if not fired:
            fired = True
            raise RuntimeError("private replay operation cleanup fault")

    monkeypatch.setattr(transaction, "_commit_transaction", counted_commit)
    monkeypatch.setattr(
        writer_module._WriterSessionOperationLease,
        "_close",
        fail_after_real_close,
    )
    try:
        with pytest.raises(SQLiteMutationStoreError) as caught:
            harness.writer._admit_rw0_evidence(command)
        assert caught.value.error_class == "mutation_failed"
        assert caught.value.args == ("mutation_failed",)
        assert caught.value.error_class != "commit_outcome_unknown"
        assert commit_calls == []
        _assert_single_evidence_commit(harness, command)
    finally:
        harness.close()
