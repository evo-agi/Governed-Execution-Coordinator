from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator._sqlite_rw0_c1 as runtime
import ge_nwp_coordinator._sqlite_rw0_c1_readers as readers
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
)
from test_rw0_c1_private_atomic_persistence import (
    _mechanics_values,
    _install_rank15_owner_family,
    admit,
    make_c1_harness,
    member_locator,
)
from test_remote_worker_pre_execution_planning_contract import (
    _build_repaired_common_phase_rows,
    _insert_exact_repaired_values,
)


class _TestsOnlyEpoch:
    """Structural test seam only; never production transaction authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.generation = 0
        self.active = False

    def start(self) -> "_TestsOnlyCapability":
        self.generation += 1
        self.active = True
        return _TestsOnlyCapability(self, self.generation)

    def end(self) -> None:
        self.active = False


class _TestsOnlyCapability:
    def __init__(self, epoch: _TestsOnlyEpoch, generation: int) -> None:
        self.epoch = epoch
        self.generation = generation
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        self.borrow_count += 1
        if not self.epoch.active or self.generation != self.epoch.generation:
            raise _MutationReadCapabilityError(
                _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED
            )
        return self.epoch.connection


def _open_capability(path: Path) -> tuple[sqlite3.Connection, _TestsOnlyEpoch, _TestsOnlyCapability]:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    epoch = _TestsOnlyEpoch(connection)
    return connection, epoch, epoch.start()


def test_capability_lifecycle_and_point_reader_are_guarded(tmp_path: Path) -> None:
    harness = make_c1_harness(tmp_path, suffix="reader-capability")
    connection, epoch, capability = _open_capability(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        phase = readers._read_phase_by_ref(
            capability, harness.phase_result.phase_basis_ref
        )
        assert phase is not None
        assert phase.value("phase_basis_digest") == harness.phase_result.phase_basis_digest
        assert capability.borrow_count == 1
        epoch.end()
        with pytest.raises(_MutationReadCapabilityError) as captured:
            readers._read_phase_by_ref(
                capability, harness.phase_result.phase_basis_ref
            )
        assert captured.value.reason is _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED
    finally:
        connection.close()
        harness.close()


@pytest.mark.parametrize("rows", [[], [("wrong-shape",)], [("a",), ("b",)]])
def test_point_reader_rejects_malformed_or_multiple_rows_without_disclosure(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[tuple[object, ...]],
) -> None:
    monkeypatch.setattr(
        readers,
        "_execute_select_fetch_bounded",
        lambda **_kwargs: rows,
    )
    if rows == []:
        assert readers._read_phase_by_ref(object(), "phase.reader.none") is None
        return
    with pytest.raises(SQLiteMutationStoreError) as captured:
        readers._read_phase_by_ref(object(), "phase.reader.bad")
    assert captured.value.error_class == "database_integrity_failure"
    assert captured.value.args == ("database_integrity_failure",)


def test_same_phase_dependency_family_relation_set_and_page_are_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="reader-family")
    monkeypatch.setattr(runtime, "_validate_rank_relation", lambda *_args, **_kwargs: False)
    values = _mechanics_values(harness)
    try:
        declaration = admit(harness, rank=7, value=values[7], sequence=1)
        observation = admit(
            harness,
            rank=8,
            value=values[8],
            sequence=2,
            dependencies=(member_locator(declaration, "capability_declaration"),),
        )
        connection, epoch, capability = _open_capability(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            family = readers._read_membership_family(
                capability,
                phase_basis_ref=harness.phase_result.phase_basis_ref,
                membership_ref=observation.membership_ref,
            )
            assert family is not None
            assert family.membership.value("kind_rank") == 8
            assert len(family.relation_set.relations) == 1
            operand = family.relation_set.relations[0].operands[0]
            assert operand.value("operand_source") == "c1_evidence"
            assert operand.value("source_membership_ref") == declaration.membership_ref
            assert operand.value("phase_basis_ref") == harness.phase_result.phase_basis_ref
            assert readers._read_membership_family(
                capability,
                phase_basis_ref="phase.reader.foreign.0001",
                membership_ref=observation.membership_ref,
            ) is None

            page_one = readers._read_membership_page(
                capability,
                phase_basis_ref=harness.phase_result.phase_basis_ref,
                after_kind_rank=0,
                after_membership_ref="cursor.start",
                maximum=1,
            )
            assert page_one.entries == (
                (7, declaration.membership_ref, declaration.membership_digest),
            )
            assert page_one.next_cursor == (7, declaration.membership_ref)
            page_two = readers._read_membership_page(
                capability,
                phase_basis_ref=harness.phase_result.phase_basis_ref,
                after_kind_rank=7,
                after_membership_ref=declaration.membership_ref,
                maximum=256,
            )
            assert page_two.entries == (
                (8, observation.membership_ref, observation.membership_digest),
            )
            assert page_two.next_cursor is None
            epoch.end()
        finally:
            connection.close()
    finally:
        harness.close()


def test_relation_and_operand_overflow_sentinels_are_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relation_columns = readers.RELATIONS_FOR_MEMBERSHIP.columns
    operand_columns = readers.OPERANDS_FOR_RELATION.columns
    relation_rows = [tuple(None for _ in relation_columns) for _ in range(3)]
    operand_rows = [tuple(None for _ in operand_columns) for _ in range(15)]

    monkeypatch.setattr(
        readers,
        "_execute_select_fetch_bounded",
        lambda **kwargs: (
            relation_rows if kwargs["limit"] == 3 else operand_rows
        ),
    )
    with pytest.raises(SQLiteMutationStoreError) as relation_error:
        readers._read_relation_set(
            object(),
            phase_basis_ref="phase.reader.overflow",
            membership_ref="membership.reader.overflow",
        )
    assert relation_error.value.error_class == "database_integrity_failure"

    with pytest.raises(SQLiteMutationStoreError) as operand_error:
        readers._read_relation_operands(
            object(),
            relation_ref="relation.reader.overflow",
        )
    assert operand_error.value.error_class == "database_integrity_failure"


@pytest.mark.parametrize("evidence_binding_count", (0, 9))
def test_section41_post_execution_family_reader_accepts_exact_zero_or_nine(
    tmp_path: Path,
    evidence_binding_count: int,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"reader-section41-{evidence_binding_count}",
    )
    try:
        _owners, wrapped = _install_rank15_owner_family(
            harness,
            evidence_binding_count=evidence_binding_count,
        )
        connection, epoch, capability = _open_capability(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            family = readers._read_section41_post_execution_evidence_family(
                capability,
                proposal_ref=wrapped.proposal_ref,
            )
            assert len(family.rows) == evidence_binding_count
            assert tuple(
                row.value("evidence_role") for row in family.rows
            ) == tuple(
                item[0] for item in readers._POST_EXECUTION_EVIDENCE
            )[:evidence_binding_count]
            epoch.end()
        finally:
            connection.close()
    finally:
        harness.close()


def test_section41_post_execution_family_reader_rejects_incomplete_set(
    tmp_path: Path,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="reader-section41-incomplete")
    physical = _build_repaired_common_phase_rows(
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        post_evidence_count=1,
    )
    connection = sqlite3.connect(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        for member in physical:
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
        connection.commit()
    finally:
        connection.close()
    connection, epoch, capability = _open_capability(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        with pytest.raises(SQLiteMutationStoreError) as captured:
            readers._read_section41_post_execution_evidence_family(
                capability,
                proposal_ref=physical[2]["values"]["proposal_ref"],
            )
        assert captured.value.error_class == "database_integrity_failure"
        epoch.end()
    finally:
        connection.close()
        harness.close()
