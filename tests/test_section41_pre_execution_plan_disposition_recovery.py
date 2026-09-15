from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

import ge_nwp_coordinator.sqlite_transition_transaction as transaction
import ge_nwp_coordinator._cognitive_proposal_row_values as rows
import ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts as contracts
import ge_nwp_coordinator._sqlite_development_pre_execution_plan_disposition as runtime
from ge_nwp_coordinator._cognitive_proposal_value_support import (
    _domain_separated_digest,
)
from ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts import (
    PreExecutionPlanDispositionRecoveryClassificationV1,
    PreExecutionPlanDispositionRecoveryProbeV1,
    _L34_FIELDS,
    _RECOVERY_PROBE_IDENTITY_SHAPES,
)
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from test_section41_private_atomic_pre_execution_plan_disposition import (
    DECISION_TIME,
    _build_bundle,
    _install_dangling_successor_above_unadvanced_head,
    make_section41_fixture,
)
from test_remote_worker_pre_execution_planning_contract import (
    _build_repaired_physical_family,
)


_EXPECTED_RECOVERY_IDENTITY_SHAPES = _RECOVERY_PROBE_IDENTITY_SHAPES
assert len(_EXPECTED_RECOVERY_IDENTITY_SHAPES) == 30


def _clock_forbidden() -> str:
    raise AssertionError("recovery called the transaction clock")


def _commit_forbidden(connection: object) -> object:
    raise AssertionError("recovery attempted COMMIT")


def _insert_row(
    database_path: Path,
    table: str,
    mapping: dict[str, object],
) -> None:
    columns = tuple(mapping)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _column in columns)})",
            tuple(mapping.values()),
        )
        connection.commit()
    finally:
        connection.close()


def _lineage_inventory(
    maximum_revision: int,
) -> tuple[object, object, object, tuple[object, ...]]:
    physical = _build_repaired_physical_family(False)["physical_rows"]
    by_role = {member["role"]: member for member in physical}
    root_member = by_role["coordinator_disposition"]
    head_member = by_role["selection_head_postimage"]
    receipt_member = by_role["receipt"]
    root = rows._row_value_from_mapping(root_member["table"], root_member["values"])
    head = rows._row_value_from_mapping(head_member["table"], head_member["values"])
    receipt = rows._row_value_from_mapping(
        receipt_member["table"], receipt_member["values"]
    )
    inventory = [root]
    predecessor = root
    for revision in range(1, maximum_revision + 1):
        disposition_mapping = root.to_mapping()
        disposition_mapping.update(
            {
                "disposition_ref": f"planning-disposition-boundary-{revision}",
                "proposal_ref": f"model-proposal-boundary-{revision}",
                "supersedes_disposition_ref": predecessor.disposition_ref,
                "expected_selection_head_revision": revision - 1,
                "expected_selection_head_digest": head.head_digest,
                "prior_selection_head_revision": revision - 1,
                "prior_selection_head_digest": head.head_digest,
                "resulting_selection_head_revision": revision,
            }
        )
        head_mapping = head_member["values"].copy()
        head_mapping.update(
            {
                "current_proposal_ref": disposition_mapping["proposal_ref"],
                "current_disposition_ref": disposition_mapping["disposition_ref"],
                "head_revision": revision,
            }
        )
        head_mapping = runtime._seal_row_mapping(rows._TABLE_ORDER[7], head_mapping)
        head = rows._row_value_from_mapping(rows._TABLE_ORDER[7], head_mapping)
        disposition_mapping["selection_head_postimage_digest"] = head.head_digest
        disposition_mapping = runtime._seal_row_mapping(
            rows._TABLE_ORDER[6], disposition_mapping
        )
        predecessor = rows._row_value_from_mapping(
            rows._TABLE_ORDER[6], disposition_mapping
        )
        inventory.append(predecessor)
    return receipt, root, head, tuple(inventory)


def _observe_successor_exclusion(
    monkeypatch: pytest.MonkeyPatch,
    expected_head: object,
) -> list[object]:
    observed: list[object] = []

    def no_dangling_successor(capability: object, head: object) -> None:
        assert head is expected_head
        observed.append(capability)

    monkeypatch.setattr(
        runtime,
        "_require_no_dangling_successor",
        no_dangling_successor,
    )
    return observed


def _shared_tuple_dag(depth: int) -> tuple[object, ...]:
    node: tuple[object, ...] = ("bounded-leaf",)
    for _index in range(depth):
        node = (node, node)
    return node


def _rewrite_redigested_rows(
    database_path: Path,
    replacements: tuple[
        tuple[str, tuple[tuple[str, object], ...], dict[str, object]], ...
    ],
) -> tuple[tuple[object, ...], ...]:
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (0,)
        target_tables = tuple(
            dict.fromkeys(table for table, _locator, _row in replacements)
        )
        trigger_rows = connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type='trigger' "
            "AND tbl_name IN ("
            + ",".join("?" for _table in target_tables)
            + ") ORDER BY name",
            target_tables,
        ).fetchall()
        assert all(
            type(name) is str and type(sql) is str for name, sql in trigger_rows
        )
        for name, _sql in trigger_rows:
            connection.execute(f'DROP TRIGGER "{name}"')
        connection.commit()

        for table, locator, mapping in replacements:
            columns = tuple(mapping)
            cursor = connection.execute(
                f'UPDATE "{table}" SET '
                + ",".join(f'"{column}"=?' for column in columns)
                + " WHERE "
                + " AND ".join(f'"{name}"=?' for name, _value in locator),
                (*mapping.values(), *(value for _name, value in locator)),
            )
            assert cursor.rowcount == 1, (table, locator)
            cursor.close()
        for _name, sql in trigger_rows:
            connection.execute(sql)
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        return tuple(connection.execute("PRAGMA foreign_key_check").fetchall())
    finally:
        connection.close()


def _alternate_lineage_value(field: str, value: object) -> object:
    if type(value) is int:
        return value + 1
    assert type(value) is str
    if field.endswith("_digest"):
        return ("f" if value[0] != "f" else "e") + value[1:]
    candidate = value + ".x"
    if len(candidate.encode("utf-8")) <= 96:
        return candidate
    return value[:-1] + ("x" if value[-1] != "x" else "y")


def _redigested_plan_dependents(
    plan: object,
    disposition_mapping: dict[str, object],
    head_mapping: dict[str, object],
) -> tuple[
    dict[str, object],
    tuple[tuple[str, tuple[tuple[str, object], ...], dict[str, object]], ...],
]:
    original_disposition = next(
        member.values
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[6]
    )
    original_head = next(
        member.values
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )
    original_receipt = next(
        member.values
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[8]
    )
    disposition_mapping["selection_head_postimage_digest"] = head_mapping[
        "head_digest"
    ]
    disposition_mapping = runtime._seal_row_mapping(
        rows._TABLE_ORDER[6], disposition_mapping
    )

    replacement_members = []
    for member in plan.rows:
        if member.table == rows._TABLE_ORDER[8]:
            continue
        if member.table == rows._TABLE_ORDER[6]:
            replacement_members.append(
                runtime._physical_row(
                    table=member.table,
                    role=member.role,
                    rank=member.rank,
                    values=disposition_mapping,
                )
            )
        elif member.table == rows._TABLE_ORDER[7]:
            replacement_members.append(
                runtime._physical_row(
                    table=member.table,
                    role=member.role,
                    rank=member.rank,
                    values=head_mapping,
                )
            )
        else:
            replacement_members.append(member)
    graph = runtime._graph_from_members(
        plan.command.mutation_ref,
        plan.command.mutation_command_digest,
        tuple(replacement_members),
    )

    receipt_mapping = original_receipt.to_mapping()
    receipt_mapping.update(
        {
            "program_ref": disposition_mapping["program_ref"],
            "proposal_ref": disposition_mapping["proposal_ref"],
            "disposition_ref": disposition_mapping["disposition_ref"],
            "disposition_digest": disposition_mapping["disposition_digest"],
            "authority_selection_observation_ref": disposition_mapping[
                "authority_selection_observation_ref"
            ],
            "authority_selection_observation_digest": disposition_mapping[
                "authority_selection_observation_digest"
            ],
            "effect_intent_ref": disposition_mapping["effect_intent_ref"],
            "selection_head_revision": disposition_mapping[
                "resulting_selection_head_revision"
            ],
            "selection_head_digest": disposition_mapping[
                "selection_head_postimage_digest"
            ],
            "mutation_graph_digest": graph.mutation_graph_digest,
            "committed_at": disposition_mapping[
                "coordinator_disposition_decided_at"
            ],
        }
    )
    result_fields = {
        "schema_id": runtime._RESULT_SCHEMA,
        "mutation_ref": receipt_mapping["mutation_ref"],
        "command_digest": receipt_mapping["command_digest"],
        "proposal_ref": receipt_mapping["proposal_ref"],
        "disposition_ref": receipt_mapping["disposition_ref"],
        "disposition_digest": receipt_mapping["disposition_digest"],
        "disposition": disposition_mapping["disposition"],
        "program_ref": receipt_mapping["program_ref"],
        "semantic_attempt_ref": disposition_mapping["semantic_attempt_ref"],
        "candidate_ref": disposition_mapping["candidate_ref"],
        "effect_intent_ref": receipt_mapping["effect_intent_ref"],
        "selection_head_revision": receipt_mapping["selection_head_revision"],
        "selection_head_digest": receipt_mapping["selection_head_digest"],
        "authority_selection_observation_ref": receipt_mapping[
            "authority_selection_observation_ref"
        ],
        "authority_selection_observation_digest": receipt_mapping[
            "authority_selection_observation_digest"
        ],
        "mutation_graph_digest": receipt_mapping["mutation_graph_digest"],
        "recorded_at": receipt_mapping["committed_at"],
    }
    receipt_mapping["result_projection_digest"] = _domain_separated_digest(
        runtime._RESULT_DOMAIN, result_fields
    )
    receipt_mapping = runtime._seal_row_mapping(
        rows._TABLE_ORDER[8], receipt_mapping
    )
    replacements = (
        (
            rows._TABLE_ORDER[6],
            (("disposition_ref", original_disposition.disposition_ref),),
            disposition_mapping,
        ),
        (
            rows._TABLE_ORDER[7],
            tuple(
                (name, object.__getattribute__(original_head, name))
                for name in runtime._K8_FIELDS
            ),
            head_mapping,
        ),
        (
            rows._TABLE_ORDER[8],
            (("mutation_ref", original_receipt.mutation_ref),),
            receipt_mapping,
        ),
    )
    return receipt_mapping, replacements


def _planned_root_family(fixture: object, probe: object) -> object:
    return runtime._build_write_plan(
        runtime._FreshPreExecutionPlanDisposition(
            fixture.command,
            fixture.bundle,
            None,
            probe,
        ),
        DECISION_TIME,
    )


def _record_depth_one_successor(
    fixture: object,
    root_result: object,
    root_plan: object,
) -> object:
    bundle = _build_bundle(
        fixture.author,
        marker="latest-relation-successor",
        readiness_present=True,
    )
    identity: dict[str, object] = {
        "preassigned_disposition_ref": "planning-disposition-latest-successor",
        "expected_current_selection_revision": root_result.selection_head_revision,
        "expected_current_selection_head_digest": root_result.selection_head_digest,
        "disposition": "selected_for_dispatch_gates",
        "disposition_reason_code": "selection.policy_bounds_satisfied",
        "supersedes_disposition_ref": root_result.disposition_ref,
    }
    fields = fixture.command.to_mapping()
    fields.pop("mutation_command_digest")
    fields.update(
        {
            "mutation_ref": "cognitive-mutation-latest-successor",
            "proposal_ref": bundle.model_proposal.proposal_ref,
            "proposal_digest": bundle.model_proposal.proposal_digest,
            "source_invocation_ref": bundle.source_invocation.source_invocation_ref,
            "source_invocation_digest": bundle.source_invocation.source_invocation_digest,
            "artifact_ref": bundle.private_artifact_binding.artifact_ref,
            "artifact_digest": bundle.private_artifact_binding.artifact_digest,
            "artifact_binding_digest": (
                bundle.private_artifact_binding.artifact_binding_digest
            ),
            "planning_context_ref": bundle.planning_context.planning_context_ref,
            "planning_context_digest": bundle.planning_context.planning_context_digest,
            "safe_projection_digest": bundle.safe_projection.safe_projection_digest,
            "evidence_set_ref": bundle.evidence_set.evidence_set_ref,
            "evidence_set_digest": bundle.evidence_set.evidence_set_digest,
            **identity,
        }
    )
    digest = _domain_separated_digest(
        runtime._COMMAND_SCHEMA + ".identity", fields
    )
    probe = fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
        fields["mutation_ref"], digest, bundle, identity
    )
    root_head = next(
        member.values
        for member in root_plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )
    plan = runtime._build_write_plan(
        runtime._FreshPreExecutionPlanDisposition(
            probe.command,
            bundle,
            root_head,
            probe,
        ),
        DECISION_TIME,
    )
    successor = fixture.author.writer._record_pre_execution_plan_disposition(
        fields["mutation_ref"], digest, bundle, identity, probe
    )
    assert successor.selection_head_revision == 1
    return plan


def _record_planned_successor(
    fixture: object,
    predecessor_result: object,
    predecessor_head: object,
    *,
    marker: str,
) -> tuple[object, object]:
    bundle = _build_bundle(
        fixture.author,
        marker=marker,
        readiness_present=True,
    )
    identity: dict[str, object] = {
        "preassigned_disposition_ref": f"planning-disposition-{marker}",
        "expected_current_selection_revision": (
            predecessor_result.selection_head_revision
        ),
        "expected_current_selection_head_digest": (
            predecessor_result.selection_head_digest
        ),
        "disposition": "selected_for_dispatch_gates",
        "disposition_reason_code": "selection.policy_bounds_satisfied",
        "supersedes_disposition_ref": predecessor_result.disposition_ref,
    }
    fields = fixture.command.to_mapping()
    fields.pop("mutation_command_digest")
    fields.update(
        {
            "mutation_ref": f"cognitive-mutation-{marker}",
            "proposal_ref": bundle.model_proposal.proposal_ref,
            "proposal_digest": bundle.model_proposal.proposal_digest,
            "source_invocation_ref": bundle.source_invocation.source_invocation_ref,
            "source_invocation_digest": (
                bundle.source_invocation.source_invocation_digest
            ),
            "artifact_ref": bundle.private_artifact_binding.artifact_ref,
            "artifact_digest": bundle.private_artifact_binding.artifact_digest,
            "artifact_binding_digest": (
                bundle.private_artifact_binding.artifact_binding_digest
            ),
            "planning_context_ref": bundle.planning_context.planning_context_ref,
            "planning_context_digest": bundle.planning_context.planning_context_digest,
            "safe_projection_digest": bundle.safe_projection.safe_projection_digest,
            "evidence_set_ref": bundle.evidence_set.evidence_set_ref,
            "evidence_set_digest": bundle.evidence_set.evidence_set_digest,
            **identity,
        }
    )
    digest = _domain_separated_digest(runtime._COMMAND_SCHEMA + ".identity", fields)
    probe = fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
        fields["mutation_ref"], digest, bundle, identity
    )
    plan = runtime._build_write_plan(
        runtime._FreshPreExecutionPlanDisposition(
            probe.command,
            bundle,
            predecessor_head,
            probe,
        ),
        DECISION_TIME,
    )
    result = fixture.author.writer._record_pre_execution_plan_disposition(
        fields["mutation_ref"], digest, bundle, identity, probe
    )
    assert result.selection_head_revision == (
        predecessor_result.selection_head_revision + 1
    )
    return result, plan


def _assert_replay_and_recovery_disclose_no_result(
    fixture: object,
    retained_probe: object,
    monkeypatch: pytest.MonkeyPatch,
    *,
    label: str,
) -> None:
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    with pytest.raises(SQLiteMutationStoreError) as replay_failure:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            retained_probe,
        )
    assert replay_failure.value.error_class == (
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    ), label
    fixture.author.writer.close()

    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        retained_probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED
    ), label
    assert recovered.committed_result is None, label
    recovery_writer.close()


def _inject_l34_disposition_and_head_corruption(
    fixture: object,
    retained_probe: object,
    field: str,
) -> tuple[tuple[object, ...], ...]:
    plan = _planned_root_family(fixture, retained_probe)
    disposition = next(
        member.values.to_mapping()
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[6]
    )
    head = next(
        member.values.to_mapping()
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )
    replacement = _alternate_lineage_value(field, disposition[field])
    disposition[field] = replacement
    head[field] = replacement
    head = runtime._seal_row_mapping(rows._TABLE_ORDER[7], head)
    _receipt, replacements = _redigested_plan_dependents(plan, disposition, head)
    return _rewrite_redigested_rows(
        fixture.author.location.database_path, replacements
    )


def test_fk_valid_redigested_program_version_family_exposes_no_replay_or_recovery_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="l34-program-version-exploit")
    retained_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        retained_probe,
    )

    foreign_key_failures = _inject_l34_disposition_and_head_corruption(
        fixture, retained_probe, "program_version_number"
    )
    assert foreign_key_failures == ()
    _assert_replay_and_recovery_disclose_no_result(
        fixture,
        retained_probe,
        monkeypatch,
        label="program_version_number",
    )


def test_every_l34_coordinate_is_bound_across_context_disposition_head_and_probe_routes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    foreign_key_classification: dict[str, bool] = {}
    for index, field in enumerate(_L34_FIELDS):
        monkeypatch.setattr(
            transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
        )
        fixture = make_section41_fixture(
            tmp_path / f"coordinate-{index:02d}",
            suffix=f"l34-{index:02d}",
        )
        retained_probe = fixture.recovery_probe
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            retained_probe,
        )
        foreign_key_failures = _inject_l34_disposition_and_head_corruption(
            fixture, retained_probe, field
        )
        foreign_key_classification[field] = bool(foreign_key_failures)
        _assert_replay_and_recovery_disclose_no_result(
            fixture,
            retained_probe,
            monkeypatch,
            label=field,
        )
    assert tuple(foreign_key_classification) == _L34_FIELDS
    assert foreign_key_classification["program_version_number"] is False


def test_depth_one_current_head_is_exact_latest_disposition_postimage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacements = {
        "current_proposal_ref": "model-proposal-contradictory-latest",
        "current_disposition": "deferred",
        "updated_at": "2098-01-01T00:00:09Z",
    }
    for index, (field, replacement) in enumerate(replacements.items()):
        monkeypatch.setattr(
            transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
        )
        fixture = make_section41_fixture(
            tmp_path / f"latest-{index}", suffix=f"latest-relation-{index}"
        )
        retained_probe = fixture.recovery_probe
        root_plan = _planned_root_family(fixture, retained_probe)
        root_result = fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            retained_probe,
        )
        successor_plan = _record_depth_one_successor(
            fixture, root_result, root_plan
        )
        connection = sqlite3.connect(fixture.author.location.database_path)
        try:
            root_receipt_before = connection.execute(
                f'SELECT * FROM "{rows._TABLE_ORDER[8]}" WHERE mutation_ref=?',
                (fixture.mutation_ref,),
            ).fetchone()
        finally:
            connection.close()
        disposition = next(
            member.values.to_mapping()
            for member in successor_plan.rows
            if member.table == rows._TABLE_ORDER[6]
        )
        head = next(
            member.values.to_mapping()
            for member in successor_plan.rows
            if member.table == rows._TABLE_ORDER[7]
        )
        head[field] = replacement
        head = runtime._seal_row_mapping(rows._TABLE_ORDER[7], head)
        _receipt, changed_rows = _redigested_plan_dependents(
            successor_plan, disposition, head
        )
        foreign_key_failures = _rewrite_redigested_rows(
            fixture.author.location.database_path, changed_rows
        )
        connection = sqlite3.connect(fixture.author.location.database_path)
        try:
            root_receipt_after = connection.execute(
                f'SELECT * FROM "{rows._TABLE_ORDER[8]}" WHERE mutation_ref=?',
                (fixture.mutation_ref,),
            ).fetchone()
        finally:
            connection.close()
        assert root_receipt_after == root_receipt_before, field
        if field == "updated_at":
            assert foreign_key_failures == ()
        else:
            assert foreign_key_failures
        _assert_replay_and_recovery_disclose_no_result(
            fixture,
            retained_probe,
            monkeypatch,
            label=field,
        )


def test_depth_two_intermediate_postimage_is_recomputed_before_replay_or_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="depth-two-intermediate")
    retained_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    root_plan = _planned_root_family(fixture, retained_probe)
    root_result = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        retained_probe,
    )
    root_head = next(
        member.values
        for member in root_plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )
    intermediate_result, intermediate_plan = _record_planned_successor(
        fixture,
        root_result,
        root_head,
        marker="depth-two-intermediate-one",
    )
    intermediate_head = next(
        member.values
        for member in intermediate_plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )
    final_result, _final_plan = _record_planned_successor(
        fixture,
        intermediate_result,
        intermediate_head,
        marker="depth-two-intermediate-two",
    )
    assert final_result.selection_head_revision == 2

    disposition_mapping = next(
        member.values.to_mapping()
        for member in intermediate_plan.rows
        if member.table == rows._TABLE_ORDER[6]
    )
    historical_head_mapping = intermediate_head.to_mapping()
    stale_postimage_digest = disposition_mapping["selection_head_postimage_digest"]
    disposition_mapping["disposition"] = "deferred"
    disposition_mapping["coordinator_disposition_decided_at"] = (
        "2098-01-01T00:00:09Z"
    )
    _receipt_mapping, redigested = _redigested_plan_dependents(
        intermediate_plan,
        disposition_mapping,
        historical_head_mapping,
    )
    assert disposition_mapping["selection_head_postimage_digest"] == (
        stale_postimage_digest
    )
    replacements = tuple(
        replacement
        for replacement in redigested
        if replacement[0] != rows._TABLE_ORDER[7]
    )
    assert _rewrite_redigested_rows(
        fixture.author.location.database_path,
        replacements,
    ) == ()
    _assert_replay_and_recovery_disclose_no_result(
        fixture,
        retained_probe,
        monkeypatch,
        label="depth-two-intermediate-postimage",
    )


def test_fresh_writer_recovers_committed_exact_without_clock_or_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recover-committed")
    probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    committed = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        probe,
    )
    fixture.author.writer.close()

    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    monkeypatch.setattr(transaction, "_commit_transaction", _commit_forbidden)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.COMMITTED_EXACT
    )
    assert recovered.observed_depth == 0
    assert recovered.committed_result.to_mapping() == committed.to_mapping()
    recovery_writer.close()


def test_fresh_writer_proves_definitely_not_committed_from_exact_preimage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recover-absent")
    probe = fixture.recovery_probe
    fixture.author.writer.close()
    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    monkeypatch.setattr(transaction, "_commit_transaction", _commit_forbidden)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.DEFINITELY_NOT_COMMITTED
    )
    assert recovered.observed_depth == 0
    assert recovered.committed_result is None
    recovery_writer.close()


def test_recovery_rejects_a_structurally_valid_but_foreign_locator_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recover-foreign")
    exact_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        exact_probe,
    )
    fixture.author.writer.close()

    locators = list(exact_probe.identity_locators)
    table, locator = locators[0]
    locators[0] = (table, ((locator[0][0], "source-invocation-foreign"),))
    foreign_probe = fixture.recovery_probe
    object.__setattr__(foreign_probe, "identity_locators", tuple(locators))
    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    monkeypatch.setattr(transaction, "_commit_transaction", _commit_forbidden)
    with pytest.raises(SQLiteMutationStoreError):
        recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
            foreign_probe
        )
    recovery_writer.close()


def test_original_receipt_recovery_proves_one_exact_descendant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recover-descendant")
    original_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    original = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        original_probe,
    )
    bundle = _build_bundle(
        fixture.author,
        marker="recover-descendant-second",
        readiness_present=True,
    )
    identity: dict[str, object] = {
        "preassigned_disposition_ref": "planning-disposition-descendant-second",
        "expected_current_selection_revision": original.selection_head_revision,
        "expected_current_selection_head_digest": original.selection_head_digest,
        "disposition": "selected_for_dispatch_gates",
        "disposition_reason_code": "selection.policy_bounds_satisfied",
        "supersedes_disposition_ref": original.disposition_ref,
    }
    fields = fixture.command.to_mapping()
    fields.pop("mutation_command_digest")
    fields.update(
        {
            "mutation_ref": "cognitive-mutation-descendant-second",
            "proposal_ref": bundle.model_proposal.proposal_ref,
            "proposal_digest": bundle.model_proposal.proposal_digest,
            "source_invocation_ref": bundle.source_invocation.source_invocation_ref,
            "source_invocation_digest": bundle.source_invocation.source_invocation_digest,
            "artifact_ref": bundle.private_artifact_binding.artifact_ref,
            "artifact_digest": bundle.private_artifact_binding.artifact_digest,
            "artifact_binding_digest": (
                bundle.private_artifact_binding.artifact_binding_digest
            ),
            "planning_context_ref": bundle.planning_context.planning_context_ref,
            "planning_context_digest": bundle.planning_context.planning_context_digest,
            "safe_projection_digest": bundle.safe_projection.safe_projection_digest,
            "evidence_set_ref": bundle.evidence_set.evidence_set_ref,
            "evidence_set_digest": bundle.evidence_set.evidence_set_digest,
            **identity,
        }
    )
    digest = _domain_separated_digest(
        "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1.identity",
        fields,
    )
    successor_probe = (
        fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
            fields["mutation_ref"], digest, bundle, identity
        )
    )
    successor = fixture.author.writer._record_pre_execution_plan_disposition(
        fields["mutation_ref"], digest, bundle, identity, successor_probe
    )
    assert successor.selection_head_revision == 1
    fixture.author.writer.close()

    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    monkeypatch.setattr(transaction, "_commit_transaction", _commit_forbidden)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        original_probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.COMMITTED_EXACT
    )
    assert recovered.observed_depth == 1
    assert recovered.committed_result.to_mapping() == original.to_mapping()
    recovery_writer.close()


def test_recovery_classifies_verified_257_transition_sentinel_as_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recover-overflow")
    oracle = _build_repaired_physical_family(False)["physical_rows"]
    by_role = {member["role"]: member for member in oracle}
    receipt_member = by_role["receipt"]
    head_member = by_role["selection_head_postimage"]
    receipt = rows._row_value_from_mapping(
        receipt_member["table"], receipt_member["values"]
    )
    head = rows._row_value_from_mapping(head_member["table"], head_member["values"])
    monkeypatch.setattr(runtime, "_read_receipt", lambda capability, ref: receipt)

    def overflow(**kwargs: object) -> object:
        raise runtime._LineageProofOverflow(head, 257)

    monkeypatch.setattr(runtime, "_read_and_verify_persisted_family", overflow)
    result = runtime._recover_pre_execution_plan_disposition_after_fencing(
        capability=object(),
        probe=fixture.recovery_probe,
    )
    assert (
        result.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED
    )
    assert result.observed_depth == 257
    assert result.committed_result is None
    fixture.author.writer.close()


def test_lineage_proof_accepts_exact_maximum_depth_256(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt, root, head, inventory = _lineage_inventory(256)
    monkeypatch.setattr(runtime, "_read_selection_head", lambda *args: head)
    monkeypatch.setattr(
        runtime,
        "_read_disposition_inventory",
        lambda *args: tuple(reversed(inventory)),
    )
    successor_checks = _observe_successor_exclusion(monkeypatch, head)
    observed_head, depth = runtime._prove_current_head_descends_from_receipt(
        object(), receipt, root
    )
    assert observed_head is head
    assert depth == 256
    assert len(successor_checks) == 1


def test_lineage_proof_marks_transition_257_as_overflow_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt, root, head, inventory = _lineage_inventory(257)
    monkeypatch.setattr(runtime, "_read_selection_head", lambda *args: head)
    monkeypatch.setattr(
        runtime,
        "_read_disposition_inventory",
        lambda *args: tuple(reversed(inventory)),
    )
    successor_checks = _observe_successor_exclusion(monkeypatch, head)
    with pytest.raises(runtime._LineageProofOverflow) as caught:
        runtime._prove_current_head_descends_from_receipt(object(), receipt, root)
    assert caught.value.head is head
    assert caught.value.observed_depth == 257
    assert len(successor_checks) == 1


@pytest.mark.parametrize(
    ("case_name", "receipt_depth"),
    (
        ("current", 0),
        ("predecessor", 1),
        ("accepted", 256),
        ("overflow", 257),
    ),
    ids=(
        "current-depth-0",
        "predecessor-depth-1",
        "accepted-depth-256",
        "overflow-depth-257",
    ),
)
def test_late_history_uses_receipt_relative_observed_depth(
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    receipt_depth: int,
) -> None:
    receipt, _root, head, inventory = _lineage_inventory(257)
    target = inventory[head.head_revision - receipt_depth]
    receipt_view = object.__new__(type(receipt))
    for name in receipt._COLUMNS:
        object.__setattr__(receipt_view, name, object.__getattribute__(receipt, name))
    object.__setattr__(receipt_view, "disposition_ref", target.disposition_ref)
    object.__setattr__(receipt_view, "disposition_digest", target.disposition_digest)
    object.__setattr__(
        receipt_view,
        "selection_head_revision",
        target.resulting_selection_head_revision,
    )
    object.__setattr__(
        receipt_view,
        "selection_head_digest",
        target.selection_head_postimage_digest,
    )
    monkeypatch.setattr(runtime, "_read_selection_head", lambda *args: head)

    def receipt_relative_inventory(*args: object) -> tuple[object, ...]:
        if len(args) == 2:
            # Opening behavior asks for the lifetime inventory and therefore
            # misclassifies a late current receipt as depth 257 overflow.
            return inventory
        assert len(args) == 3
        assert args[1] is target and args[2] is head
        return tuple(
            reversed(inventory[target.resulting_selection_head_revision :])
        )

    monkeypatch.setattr(
        runtime,
        "_read_disposition_inventory",
        receipt_relative_inventory,
    )
    successor_checks = _observe_successor_exclusion(monkeypatch, head)
    if receipt_depth == 257:
        with pytest.raises(runtime._LineageProofOverflow) as caught:
            runtime._prove_current_head_descends_from_receipt(
                object(), receipt_view, target
            )
        assert caught.value.head is head
        assert caught.value.observed_depth == 257
        assert len(successor_checks) == 1
        return
    observed_head, observed_depth = runtime._prove_current_head_descends_from_receipt(
        object(), receipt_view, target
    )
    assert case_name in ("current", "predecessor", "accepted")
    assert observed_head is head
    assert observed_depth == receipt_depth
    assert len(successor_checks) == 1


def test_disposition_inventory_uses_k8_and_rejects_different_l34(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    physical = _build_repaired_physical_family(False)["physical_rows"]
    member = next(
        item for item in physical if item["role"] == "coordinator_disposition"
    )
    root = rows._row_value_from_mapping(member["table"], member["values"])
    head_member = next(
        item for item in physical if item["role"] == "selection_head_postimage"
    )
    head = rows._row_value_from_mapping(head_member["table"], head_member["values"])
    contradictory = root.to_mapping()
    contradictory["program_version_number"] = 2
    contradictory = runtime._seal_row_mapping(rows._TABLE_ORDER[6], contradictory)
    observed: dict[str, object] = {}

    def read_rows(capability: object, **kwargs: object) -> list[object]:
        observed["capability"] = capability
        observed.update(kwargs)
        return [(*tuple(contradictory.values()), 1)]

    monkeypatch.setattr(runtime, "_read_rows", read_rows)
    with pytest.raises(SQLiteMutationStoreError):
        runtime._read_disposition_inventory(object(), root, head)
    assert observed["where"] == (
        runtime._K8_WHERE
        + " AND resulting_selection_head_revision BETWEEN ? AND ? "
        + "ORDER BY resulting_selection_head_revision DESC, disposition_ref ASC"
    )
    assert observed["parameters"] == tuple(
        object.__getattribute__(root, name) for name in runtime._K8_FIELDS
    ) + (0, 0)
    assert observed["columns"] == (
        *rows._TABLE_COLUMNS[rows._TABLE_ORDER[6]],
        "COUNT(*) OVER ()",
    )
    assert observed["limit"] == 258

    successor_observed: dict[str, object] = {}

    def read_no_successor(capability: object, **kwargs: object) -> list[object]:
        successor_observed["capability"] = capability
        successor_observed.update(kwargs)
        return []

    monkeypatch.setattr(runtime, "_read_rows", read_no_successor)
    runtime._require_no_dangling_successor(object(), head)
    assert successor_observed["table"] == rows._TABLE_ORDER[6]
    assert successor_observed["columns"] == rows._TABLE_COLUMNS[rows._TABLE_ORDER[6]]
    assert successor_observed["where"] == (
        runtime._L34_WHERE
        + " AND prior_selection_head_revision = ?"
        + " AND supersedes_disposition_ref = ?"
    )
    assert successor_observed["parameters"] == tuple(
        object.__getattribute__(head, name) for name in runtime._L34_FIELDS
    ) + (head.head_revision, head.current_disposition_ref)
    assert successor_observed["limit"] == 2


def test_evidence_read_uses_complete_repaired_canonical_order() -> None:
    assert runtime._EVIDENCE_SELECT.endswith(
        "ORDER BY role_rank, ordinal, evidence_role, evidence_set_ref, "
        "evidence_ref, evidence_digest, evidence_binding_digest, proposal_phase, "
        "schema_id, required_for_selection, evidence_bound_at LIMIT 16"
    )


@pytest.mark.parametrize("readiness_present", (False, True))
def test_total_absence_recovery_probes_every_evidence_member_and_rejects_lone_nonfirst_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    readiness_present: bool,
) -> None:
    fixture = make_section41_fixture(
        tmp_path,
        suffix=f"lone-risk-{int(readiness_present)}",
        readiness_present=readiness_present,
    )
    probe = fixture.recovery_probe
    assert len(probe.evidence_member_locators) == (15 if readiness_present else 14)
    risk_lane = fixture.bundle.evidence_bindings[1]
    _insert_row(
        fixture.author.location.database_path,
        rows._TABLE_ORDER[5],
        risk_lane.to_mapping(),
    )
    fixture.author.writer.close()
    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    monkeypatch.setattr(transaction, "_commit_transaction", _commit_forbidden)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED
    )
    assert recovered.committed_result is None
    recovery_writer.close()


def test_total_absence_recovery_rejects_alternate_selection_head_unique_route_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="alternate-head-route")
    probe = fixture.recovery_probe
    fresh = runtime._FreshPreExecutionPlanDisposition(
        fixture.command,
        fixture.bundle,
        None,
        probe,
    )
    plan = runtime._build_write_plan(fresh, DECISION_TIME)
    head = next(
        member.values
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )
    alternate = head.to_mapping()
    alternate["semantic_attempt_ref"] = "semantic-attempt-alternate-head"
    alternate = runtime._seal_row_mapping(rows._TABLE_ORDER[7], alternate)
    _insert_row(
        fixture.author.location.database_path,
        rows._TABLE_ORDER[7],
        alternate,
    )
    fixture.author.writer.close()
    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", _clock_forbidden)
    monkeypatch.setattr(transaction, "_commit_transaction", _commit_forbidden)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED
    )
    assert recovered.committed_result is None
    recovery_writer.close()


def test_recovery_preflight_rejects_shared_dag_before_operation_guard_or_sql(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recovery-shared-dag")
    probe = fixture.recovery_probe
    shared = _shared_tuple_dag(10)
    object.__setattr__(
        probe,
        "identity_locators",
        tuple((shared, shared) for _index in range(30)),
    )
    monkeypatch.setattr(
        contracts,
        "_MAX_EXACT_CONTRACT_RECONSTRUCTION_WORK",
        5_000,
        raising=False,
    )
    calls = {"operation": 0, "connection": 0, "query": 0}

    def forbidden(name: str):
        def invoke(*args: object, **kwargs: object) -> object:
            calls[name] += 1
            raise AssertionError(f"{name} reached")

        return invoke

    monkeypatch.setattr(
        type(fixture.author.writer),
        "_run_pre_execution_plan_disposition_operation",
        forbidden("operation"),
    )
    monkeypatch.setattr(
        transaction, "_open_controller_connection", forbidden("connection")
    )
    monkeypatch.setattr(runtime, "_read_receipt", forbidden("query"))
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._resolve_pre_execution_plan_disposition_commit_outcome(
            probe
        )
    assert caught.value.error_class == (
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    )
    assert calls == {"operation": 0, "connection": 0, "query": 0}
    fixture.author.writer.close()


@pytest.mark.parametrize(
    "mutation",
    ("source-locator", "evidence-locator", "head-locator", "nested-context", "hostile"),
)
def test_mutated_or_forged_recovery_probe_fails_before_operation_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix=f"forged-{mutation}")
    probe = fixture.recovery_probe
    callbacks = 0

    class HostileString(str):
        def __eq__(self, other: object) -> bool:
            nonlocal callbacks
            callbacks += 1
            raise KeyboardInterrupt()

        def __hash__(self) -> int:
            nonlocal callbacks
            callbacks += 1
            raise SystemExit()

    if mutation in ("source-locator", "head-locator"):
        index = 0 if mutation == "source-locator" else 22
        locators = list(probe.identity_locators)
        table, locator = locators[index]
        changed = list(locator)
        name, _value = changed[0]
        changed[0] = (name, "forged-locator-value")
        locators[index] = (table, tuple(changed))
        object.__setattr__(probe, "identity_locators", tuple(locators))
    elif mutation == "evidence-locator":
        members = list(probe.evidence_member_locators)
        primary, alternate = members[1]
        changed = list(primary)
        changed[1] = ("evidence_role", "standing_policy")
        members[1] = (tuple(changed), alternate)
        object.__setattr__(probe, "evidence_member_locators", tuple(members))
    elif mutation == "nested-context":
        object.__setattr__(
            probe.planning_context,
            "risk_lane_ref",
            "risk-lane-post-mutated",
        )
    else:
        object.__setattr__(
            probe.planning_context,
            "risk_lane_ref",
            HostileString("risk-lane-hostile"),
        )

    operation_calls = 0

    def operation(*args: object, **kwargs: object) -> object:
        nonlocal operation_calls
        operation_calls += 1
        return object()

    monkeypatch.setattr(
        type(fixture.author.writer),
        "_run_pre_execution_plan_disposition_operation",
        operation,
    )
    with pytest.raises(SQLiteMutationStoreError):
        fixture.author.writer._resolve_pre_execution_plan_disposition_commit_outcome(
            probe
        )
    assert operation_calls == 0
    assert callbacks == 0
    fixture.author.writer.close()


def _recovery_semantic_metaclass_spoof(
    trusted_value: object,
    process_control: BaseException | None,
) -> tuple[object, dict[str, int]]:
    trusted_type = type(trusted_value)
    callbacks = {"hash": 0, "equality": 0, "mapping": 0, "construction": 0}

    class CollisionMeta(type):
        def __hash__(cls) -> int:
            callbacks["hash"] += 1
            if process_control is not None:
                raise process_control
            return type.__hash__(trusted_type)

        def __eq__(cls, other: object) -> bool:
            callbacks["equality"] += 1
            if process_control is not None:
                raise process_control
            return other is trusted_type

        def __call__(cls, *args: object, **kwargs: object) -> object:
            callbacks["construction"] += 1
            if process_control is not None:
                raise process_control
            return trusted_type(*args, **kwargs)

    field_order = trusted_type._FIELD_ORDER  # type: ignore[attr-defined]

    def to_mapping(self: object) -> dict[str, object]:
        callbacks["mapping"] += 1
        if process_control is not None:
            raise process_control
        return {
            name: object.__getattribute__(self, name) for name in field_order
        }

    spoof_type = CollisionMeta(
        trusted_type.__name__,
        (),
        {
            "__module__": trusted_type.__module__,
            "_FIELD_ORDER": field_order,
            "to_mapping": to_mapping,
        },
    )
    spoof = object.__new__(spoof_type)
    spoof.__dict__.update(
        {
            name: object.__getattribute__(trusted_value, name)
            for name in field_order
        }
    )
    callbacks.update(hash=0, equality=0, mapping=0, construction=0)
    return spoof, callbacks


def _exact_container_contains(value: object, target: str) -> bool:
    kind = type(value)
    if kind is str:
        return value == target
    if kind is tuple or kind is list or kind is set or kind is frozenset:
        return any(_exact_container_contains(member, target) for member in value)
    if kind is dict:
        return any(
            _exact_container_contains(member, target)
            for pair in value.items()
            for member in pair
        )
    return False


@pytest.mark.parametrize(
    "mutation",
    (
        "equal-hash-spoof",
        "raising-metaclass",
        "post-mutated-exact-probe",
        "post-mutated-probe-digest",
    ),
)
def test_recovery_hostile_class_and_mutation_fail_before_every_operation_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix=f"recovery-{mutation}")
    probe = fixture.recovery_probe
    raw_sentinel = "recovery-hostile-process-control-sentinel"
    process_control = (
        GeneratorExit(raw_sentinel) if mutation == "raising-metaclass" else None
    )
    callbacks = {"hash": 0, "equality": 0, "mapping": 0, "construction": 0}
    if mutation == "post-mutated-exact-probe":
        object.__setattr__(
            probe.planning_context,
            "risk_lane_ref",
            "risk-lane-post-mutated-exact-probe",
        )
    elif mutation == "post-mutated-probe-digest":
        replacement = (
            "f" * 64 if probe.recovery_probe_digest != "f" * 64 else "e" * 64
        )
        object.__setattr__(probe, "recovery_probe_digest", replacement)
    else:
        spoof, callbacks = _recovery_semantic_metaclass_spoof(
            probe.planning_context,
            process_control,
        )
        object.__setattr__(probe, "planning_context", spoof)

    calls = {
        "operation": 0,
        "connection": 0,
        "query": 0,
        "clock": 0,
        "write": 0,
        "rollback": 0,
        "commit": 0,
    }

    def forbidden(name: str):
        def invoke(*args: object, **kwargs: object) -> object:
            calls[name] += 1
            raise AssertionError(f"{name} reached")

        return invoke

    monkeypatch.setattr(
        type(fixture.author.writer),
        "_run_pre_execution_plan_disposition_operation",
        forbidden("operation"),
    )
    monkeypatch.setattr(transaction, "_open_controller_connection", forbidden("connection"))
    monkeypatch.setattr(runtime, "_read_receipt", forbidden("query"))
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", forbidden("clock"))
    monkeypatch.setattr(
        transaction, "_execute_pre_execution_plan_disposition_writes", forbidden("write")
    )
    monkeypatch.setattr(transaction, "_rollback_transaction", forbidden("rollback"))
    monkeypatch.setattr(transaction, "_commit_transaction", forbidden("commit"))

    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._resolve_pre_execution_plan_disposition_commit_outcome(
            probe
        )
    assert caught.value.error_class == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    assert callbacks == {"hash": 0, "equality": 0, "mapping": 0, "construction": 0}
    assert calls == {
        "operation": 0,
        "connection": 0,
        "query": 0,
        "clock": 0,
        "write": 0,
        "rollback": 0,
        "commit": 0,
    }
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert not hasattr(caught.value, "__notes__")
    assert not _exact_container_contains(caught.value.args, raw_sentinel)
    assert not _exact_container_contains(caught.value.__dict__, raw_sentinel)
    traceback = caught.value.__traceback__
    while traceback is not None:
        if "/src/ge_nwp_coordinator/" in traceback.tb_frame.f_code.co_filename:
            assert not any(
                _exact_container_contains(value, raw_sentinel)
                for value in traceback.tb_frame.f_locals.values()
            )
        traceback = traceback.tb_next
    fixture.author.writer.close()


@pytest.mark.parametrize("entry", ("replay", "recovery"))
def test_exact_disclosure_executes_all_thirty_identity_routes_and_every_evidence_member_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix=f"coverage-{entry}")
    probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    committed = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        probe,
    )
    original = runtime._verified_row_for_locator
    observed: list[tuple[str, tuple[tuple[str, object], ...]]] = []

    def capture(
        capability: object,
        table: str,
        locator: tuple[tuple[str, object], ...],
    ) -> object:
        observed.append((table, locator))
        return original(capability, table, locator)

    monkeypatch.setattr(runtime, "_verified_row_for_locator", capture)
    if entry == "replay":
        disclosed = fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            probe,
        )
    else:
        fixture.author.writer.close()
        recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
        recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
            probe
        )
        assert (
            recovered.classification
            is PreExecutionPlanDispositionRecoveryClassificationV1.COMMITTED_EXACT
        )
        disclosed = recovered.committed_result
        recovery_writer.close()
    assert disclosed.to_mapping() == committed.to_mapping()
    assert len(observed) == 30 + 2 * len(probe.evidence_member_locators)
    assert tuple(
        (table, tuple(name for name, _value in locator))
        for table, locator in observed[:30]
    ) == _EXPECTED_RECOVERY_IDENTITY_SHAPES
    fixture.author.writer.close()


def _member_with_redigested_route_divergence(
    member: rows.CanonicalCognitivePhysicalRow,
    locator: tuple[tuple[str, object], ...],
) -> rows.CanonicalCognitivePhysicalRow:
    for field, value in reversed(locator):
        mapping = member.values.to_mapping()
        if type(value) is int:
            replacement: object = value + 1
        elif field == "disposition":
            replacement = "deferred" if value != "deferred" else "blocked"
        elif type(value) is str and field.endswith("_digest"):
            replacement = ("f" if value[0] != "f" else "e") + value[1:]
        elif type(value) is str and field != "proposal_phase":
            replacement = value + ".x"
            if len(replacement.encode("utf-8")) > 96:
                replacement = value[:-1] + ("x" if value[-1] != "x" else "y")
        else:
            continue
        mapping[field] = replacement
        try:
            sealed = runtime._seal_row_mapping(member.table, mapping)
            changed = runtime._physical_row(
                table=member.table,
                role=member.role,
                rank=member.rank,
                values=sealed,
            )
        except SQLiteMutationStoreError:
            continue
        if changed.values.to_mapping() != member.values.to_mapping():
            return changed
    raise AssertionError((member.table, locator))


def test_redigested_actual_rows_must_equal_all_retained_probe_route_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="actual-route-equality")
    retained_probe = fixture.recovery_probe
    plan = _planned_root_family(fixture, retained_probe)
    head = next(
        member.values
        for member in plan.rows
        if member.table == rows._TABLE_ORDER[7]
    )

    def query_forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("route query reached before actual/probe equality")

    monkeypatch.setattr(runtime, "_verified_row_for_locator", query_forbidden)
    assert len(retained_probe.identity_locators) == 30
    for route_index, (table, locator) in enumerate(
        retained_probe.identity_locators
    ):
        members = list(plan.rows)
        member_index = next(
            index for index, member in enumerate(members) if member.table == table
        )
        members[member_index] = _member_with_redigested_route_divergence(
            members[member_index], locator
        )
        actual = runtime._identity_locators_for_rows(tuple(members))
        assert actual[route_index] != retained_probe.identity_locators[route_index]
        with pytest.raises(SQLiteMutationStoreError) as caught:
            runtime._verify_all_persisted_identity_routes(
                capability=object(),
                members=tuple(members),
                current_head=head,
                historical_head=head,
                observed_depth=0,
                persisted_probe=retained_probe,
            )
        assert caught.value.error_class == (
            SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
        ), route_index

    evidence_indexes = tuple(
        index
        for index, member in enumerate(plan.rows)
        if member.table == rows._TABLE_ORDER[5]
    )
    assert len(evidence_indexes) == len(retained_probe.evidence_member_locators)
    for member_index, expected_routes in zip(
        evidence_indexes,
        retained_probe.evidence_member_locators,
        strict=True,
    ):
        for route_index, route in enumerate(expected_routes):
            members = list(plan.rows)
            members[member_index] = _member_with_redigested_route_divergence(
                members[member_index], route
            )
            actual_routes = runtime._evidence_member_locators_for_rows(
                tuple(members)
            )
            assert actual_routes[evidence_indexes.index(member_index)][route_index] != (
                expected_routes[route_index]
            )
            with pytest.raises(SQLiteMutationStoreError) as caught:
                runtime._verify_all_persisted_identity_routes(
                    capability=object(),
                    members=tuple(members),
                    current_head=head,
                    historical_head=head,
                    observed_depth=0,
                    persisted_probe=retained_probe,
                )
            assert caught.value.error_class == (
                SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
            ), (member_index, route_index)
    fixture.author.writer.close()


_ALTERNATE_ROUTE_INDEX = {
    rows._TABLE_ORDER[0]: 1,
    rows._TABLE_ORDER[1]: 3,
    rows._TABLE_ORDER[2]: 5,
    rows._TABLE_ORDER[3]: 9,
    rows._TABLE_ORDER[4]: 11,
    rows._TABLE_ORDER[5]: 13,
    rows._TABLE_ORDER[6]: 15,
    rows._TABLE_ORDER[7]: 25,
    rows._TABLE_ORDER[8]: 28,
}


def _alternate_valid_row(
    row: rows._CognitiveRowValue,
) -> rows._CognitiveRowValue:
    table = row._TABLE
    mapping = row.to_mapping()
    if table == rows._TABLE_ORDER[0]:
        mapping["model_contract_ref"] = "model-contract-alternate"
    elif table == rows._TABLE_ORDER[1]:
        mapping["risk_lane_ref"] = "risk-lane-alternate"
    elif table == rows._TABLE_ORDER[2]:
        mapping["safe_projection_digest"] = "e" * 64
    elif table == rows._TABLE_ORDER[3]:
        mapping["model_contract_ref"] = "model-contract-alternate"
    elif table == rows._TABLE_ORDER[4]:
        mapping["reason_code"] = "plan.alternate"
    elif table == rows._TABLE_ORDER[5]:
        mapping["evidence_ref"] = "evidence-alternate"
    elif table == rows._TABLE_ORDER[6]:
        mapping["reason_code"] = "selection.alternate"
    elif table == rows._TABLE_ORDER[7]:
        mapping["current_disposition_ref"] = "disposition-alternate"
    else:
        mapping["result_projection_digest"] = "e" * 64
    sealed = runtime._seal_row_mapping(table, mapping)
    return rows._row_value_from_mapping(table, sealed)


@pytest.mark.parametrize("table", rows._TABLE_ORDER)
def test_exact_replay_with_alternate_collision_in_each_identity_family_exposes_no_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    table: str,
) -> None:
    fixture = make_section41_fixture(
        tmp_path, suffix=f"replay-collision-{rows._TABLE_ORDER.index(table)}"
    )
    probe = fixture.recovery_probe
    fresh = runtime._FreshPreExecutionPlanDisposition(
        fixture.command, fixture.bundle, None, probe
    )
    plan = runtime._build_write_plan(fresh, DECISION_TIME)
    expected = next(member.values for member in plan.rows if member.table == table)
    alternate = _alternate_valid_row(expected)
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        probe,
    )
    target_index = _ALTERNATE_ROUTE_INDEX[table]
    target_shape = _EXPECTED_RECOVERY_IDENTITY_SHAPES[target_index][1]
    original = runtime._verified_row_for_locator
    collisions = 0

    def collide(
        capability: object,
        observed_table: str,
        locator: tuple[tuple[str, object], ...],
    ) -> object:
        nonlocal collisions
        if (
            observed_table == table
            and tuple(name for name, _value in locator) == target_shape
        ):
            collisions += 1
            return alternate
        return original(capability, observed_table, locator)

    monkeypatch.setattr(runtime, "_verified_row_for_locator", collide)
    with pytest.raises(SQLiteMutationStoreError):
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            probe,
        )
    assert collisions == 1
    fixture.author.writer.close()


@pytest.mark.parametrize("table", rows._TABLE_ORDER)
def test_committed_recovery_with_alternate_collision_in_each_identity_family_exposes_no_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    table: str,
) -> None:
    fixture = make_section41_fixture(
        tmp_path, suffix=f"recovery-collision-{rows._TABLE_ORDER.index(table)}"
    )
    probe = fixture.recovery_probe
    fresh = runtime._FreshPreExecutionPlanDisposition(
        fixture.command, fixture.bundle, None, probe
    )
    plan = runtime._build_write_plan(fresh, DECISION_TIME)
    expected = next(member.values for member in plan.rows if member.table == table)
    alternate = _alternate_valid_row(expected)
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        probe,
    )
    fixture.author.writer.close()
    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    original = runtime._verified_row_for_locator
    target_index = _ALTERNATE_ROUTE_INDEX[table]
    target_shape = _EXPECTED_RECOVERY_IDENTITY_SHAPES[target_index][1]
    collisions = 0

    def collide(
        capability: object,
        observed_table: str,
        locator: tuple[tuple[str, object], ...],
    ) -> object:
        nonlocal collisions
        if observed_table == table and tuple(name for name, _value in locator) == target_shape:
            collisions += 1
            return alternate
        return original(capability, observed_table, locator)

    monkeypatch.setattr(runtime, "_verified_row_for_locator", collide)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED
    )
    assert recovered.committed_result is None
    assert collisions == 1
    recovery_writer.close()


def test_preconstructed_probe_survives_late_commit_uncertainty_for_fresh_writer_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="late-commit-uncertainty")
    retained_probe = fixture.recovery_probe
    original_commit = transaction._ControllerConnectionScope.commit
    commit_calls = 0

    def late_uncertainty(scope: object) -> object:
        nonlocal commit_calls
        commit_calls += 1
        original_commit(scope)
        raise sqlite3.OperationalError("injected lost commit acknowledgement")

    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    monkeypatch.setattr(
        transaction._ControllerConnectionScope, "commit", late_uncertainty
    )
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            retained_probe,
        )
    assert caught.value.error_class == "commit_outcome_unknown"
    assert commit_calls == 1

    reads = 0
    original_read_receipt = runtime._read_receipt

    def count_read(*args: object, **kwargs: object) -> object:
        nonlocal reads
        reads += 1
        return original_read_receipt(*args, **kwargs)

    monkeypatch.setattr(runtime, "_read_receipt", count_read)
    with pytest.raises(Exception):
        fixture.author.writer._resolve_pre_execution_plan_disposition_commit_outcome(
            retained_probe
        )
    assert reads == 0
    fixture.author.writer.close()

    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    recovered = recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
        retained_probe
    )
    assert (
        recovered.classification
        is PreExecutionPlanDispositionRecoveryClassificationV1.COMMITTED_EXACT
    )
    assert recovered.committed_result is not None
    assert recovered.committed_result.mutation_ref == fixture.mutation_ref
    recovery_writer.close()


def test_recovery_classifies_dangling_successor_above_unadvanced_head_unresolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="dangling-successor-recovery")
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: DECISION_TIME,
    )
    try:
        _root_result, retained_probe, evidence = (
            _install_dangling_successor_above_unadvanced_head(
                fixture,
                marker="dangling-successor-recovery-next",
            )
        )
        assert evidence == {
            "foreign_key_failures": (),
            "integrity_check": ("ok",),
            "disposition_count": (2,),
            "receipt_count": (2,),
            "head_revision": (0,),
            "dangling_count": (1,),
        }
    finally:
        fixture.author.writer.close()

    recovery_writer = acquire_sqlite_writer_session(fixture.author.location)
    successor_exclusion_checks = 0
    result_constructions = 0
    downstream = {"clock": 0, "result": 0, "dml": 0, "commit": 0}
    original_exclusion = runtime._require_no_dangling_successor

    def count_exclusion(capability: object, head: object) -> None:
        nonlocal successor_exclusion_checks
        successor_exclusion_checks += 1
        original_exclusion(capability, head)  # type: ignore[arg-type]

    def forbidden(name: str) -> object:
        downstream[name] += 1
        raise AssertionError(f"dangling-successor recovery reached {name}")

    def result_forbidden(*args: object, **kwargs: object) -> object:
        nonlocal result_constructions
        result_constructions += 1
        return forbidden("result")

    monkeypatch.setattr(runtime, "_require_no_dangling_successor", count_exclusion)
    monkeypatch.setattr(
        runtime,
        "PreExecutionPlanDispositionResultProjectionV1",
        result_forbidden,
    )
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: forbidden("clock"),
    )
    monkeypatch.setattr(
        transaction,
        "_execute_pre_execution_plan_disposition_writes",
        lambda *args, **kwargs: forbidden("dml"),
    )
    monkeypatch.setattr(
        transaction,
        "_commit_transaction",
        lambda *args, **kwargs: forbidden("commit"),
    )
    try:
        recovered = (
            recovery_writer._resolve_pre_execution_plan_disposition_commit_outcome(
                retained_probe
            )
        )
        assert (
            recovered.classification
            is PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED
        )
        assert recovered.observed_depth == 0
        assert recovered.committed_result is None
        assert successor_exclusion_checks == 1
        assert result_constructions == 0
        assert downstream == {"clock": 0, "result": 0, "dml": 0, "commit": 0}
    finally:
        recovery_writer.close()
