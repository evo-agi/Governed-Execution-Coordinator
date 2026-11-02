"""S01 historical-binding and A03 witness grammar controls; synthetic state only."""
from __future__ import annotations

from dataclasses import replace
import json
import sqlite3

import pytest

from ge_nwp_coordinator import _cognitive_proposal_row_values as cognitive
from ge_nwp_coordinator import _cognitive_proposal_semantic_values as cognitive_values
from ge_nwp_coordinator import _development_effect_row_values as effects
from ge_nwp_coordinator import _development_program_row_values as programs
from ge_nwp_coordinator import _rw0_terminal_outcome_plan as plan
from ge_nwp_coordinator import _sqlite_rw0_terminal_outcome as terminal_runtime
from ge_nwp_coordinator import sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator import sqlite_writer_session as writer_session_module
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator._rw0_terminal_head_witness import (
    TerminalHeadWitness, WITNESS_BYTE_CEILING, WITNESS_SCHEMA,
    witness_from_bytes, witness_from_typed,
)
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import (
    CONTEXT_SCHEMA, GRAPH_PROFILE, HEAD_ROLES, RecordRW0TerminalOutcomeCommandV1,
    TerminalConflictV1, _canonical, _digest,
)
from ge_nwp_coordinator._rw0_terminal_outcome_rows import (
    COLUMNS, CONTEXT, OUTCOME, RECEIPT, RESULT, TABLES, checked_row, seal_row,
)
from ge_nwp_coordinator._rw0_terminal_anchor_rows import (
    COLUMNS as ANCHOR_COLUMNS, SCHEMA as ANCHOR_SCHEMA,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_terminal_connected import _terminal_selector, prepared_normal_case


_TABLES = (
    "development_program_heads", "development_work_item_heads",
    "development_pre_execution_selection_heads", "development_effect_heads",
    "development_delivery_heads",
)
_COLUMNS = (
    programs._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
    programs._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
    cognitive._TABLE_COLUMNS[_TABLES[2]],
    effects._DEVELOPMENT_EFFECT_HEAD_COLUMNS,
    effects._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
)
_DOMAINS = (
    programs._DEVELOPMENT_PROGRAM_HEAD_DOMAIN,
    programs._DEVELOPMENT_WORK_ITEM_HEAD_DOMAIN,
    cognitive._DOMAINS[_TABLES[2]],
    effects._EFFECT_HEAD_DOMAIN,
    effects._DELIVERY_HEAD_DOMAIN,
)


def _actual_witness(db: sqlite3.Connection):
    images = []
    for table, columns in zip(_TABLES, _COLUMNS, strict=True):
        row = db.execute("SELECT " + ", ".join(columns) + " FROM " + table).fetchone()
        assert row is not None
        images.append(dict(zip(columns, row, strict=True)))
    return witness_from_bytes(_canonical({
        "schema_id": WITNESS_SCHEMA,
        "heads": [{"role": role, "postimage": image}
                  for role, image in zip(HEAD_ROLES, images, strict=True)],
    }))


def _observe_complete_terminal_sql(patch, *, historical: bool,
                                   deny_managed_stop: bool = False):
    """Test-only authorizer on the real acquisition and controller openers."""
    events = []
    phases = {}
    next_connection = 0
    original_acquisition = writer_session_module._open_bound_existing_sqlite_connection
    original_controller = transaction_module._open_bound_existing_sqlite_connection
    original_managed = transaction_module._validate_managed_connection_for_mutation
    original_fence = transaction_module._read_writer_ownership_for_fencing

    def attach(connection, kind):
        nonlocal next_connection
        next_connection += 1
        identity = next_connection
        phase = {"name": "acquisition" if kind == "acquisition" else "opened"}
        phases[id(connection)] = phase

        def authorize(action, table, column, database, trigger):
            if action != sqlite3.SQLITE_READ:
                return sqlite3.SQLITE_OK
            denied = (kind == "operation" and (
                (historical and table in _TABLES)
                or (table == "global_stop_current" and (
                    (deny_managed_stop and phase["name"] == "managed")
                    or (historical and phase["name"] != "managed")))
            ))
            events.append((identity, kind, phase["name"], table, column, denied))
            return sqlite3.SQLITE_DENY if denied else sqlite3.SQLITE_OK

        connection.set_authorizer(authorize)
        if kind == "operation":
            phase["name"] = "calibration"
            connection.execute("SELECT name FROM sqlite_schema LIMIT 1").fetchone()
            try:
                connection.execute(
                    "SELECT head_revision FROM development_program_heads LIMIT 1"
                ).fetchone()
            except sqlite3.DatabaseError:
                assert historical
            else:
                assert not historical
            phase["name"] = "opened"
        return connection

    def acquisition_open(*args, **kwargs):
        return attach(original_acquisition(*args, **kwargs), "acquisition")

    def controller_open(*args, **kwargs):
        return attach(original_controller(*args, **kwargs), "operation")

    def managed(connection):
        phase = phases[id(connection)]
        phase["name"] = "managed"
        try:
            return original_managed(connection)
        finally:
            phase["name"] = "after_managed"

    def fence(connection):
        phase = phases[id(connection)]
        phase["name"] = "fencing"
        result = original_fence(connection)
        phase["name"] = "terminal"
        return result

    patch.setattr(writer_session_module, "_open_bound_existing_sqlite_connection",
                  acquisition_open)
    patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection",
                  controller_open)
    patch.setattr(transaction_module, "_validate_managed_connection_for_mutation",
                  managed)
    patch.setattr(transaction_module, "_read_writer_ownership_for_fencing", fence)
    return events


def _assert_historical_authorizer_events(events, *, operations: int,
                                         reached_terminal: bool):
    operation_ids = {identity for identity, kind, *_ in events if kind == "operation"}
    assert len(operation_ids) == operations
    assert any(kind == "acquisition" and table == "global_stop_current"
               for _, kind, _, table, _, _ in events)
    for identity in operation_ids:
        own = [event for event in events if event[0] == identity]
        assert any(phase == "calibration" and table == "sqlite_master" and not denied
                   for _, _, phase, table, _, denied in own)
        assert any(phase == "calibration" and table == _TABLES[0] and denied
                   for _, _, phase, table, _, denied in own)
        assert any(phase == "managed" and table == "global_stop_current"
                   for _, _, phase, table, _, _ in own)
        assert all(table not in _TABLES or denied
                   for _, _, _, table, _, denied in own)
        assert all(table != "global_stop_current" or phase == "managed" or denied
                   for _, _, phase, table, _, denied in own)
        if reached_terminal:
            assert any(phase == "terminal" and table == RECEIPT and not denied
                       for _, _, phase, table, _, denied in own)
        else:
            assert all(phase != "terminal" for _, _, phase, _, _, _ in own)


def test_witness_ceiling_covers_closed_owner_column_inventory():
    assert tuple(map(len, _COLUMNS)) == (8, 9, 41, 9, 8)
    empty = _canonical({"schema_id": WITNESS_SCHEMA, "heads": [
        {"role": role, "postimage": {}} for role in HEAD_ROLES]})
    # Conservative per-scalar 256-byte allowance exceeds each owner's
    # closed ref/digest/time/schema/enum/integer/null budget, including quotes.
    upper = len(empty) + sum(len(name.encode()) + 4 + 256
                             for columns in _COLUMNS for name in columns)
    assert upper < WITNESS_BYTE_CEILING


def _cognitive_row(db: sqlite3.Connection, table: str, key: str, ref: str):
    columns = cognitive._TABLE_COLUMNS[table]
    found = db.execute("SELECT " + ", ".join(columns) + " FROM " + table
                       + " WHERE " + key + "=?", (ref,)).fetchone()
    assert found is not None
    return dict(zip(columns, found, strict=True))


def _reseal_cognitive(table: str, original: dict[str, object], **changes: object):
    columns = cognitive._TABLE_COLUMNS[table]
    digest_field = cognitive._DIGEST_FIELDS[table]
    changed = {**original, **changes}
    digest_input = {column: changed[column] for column in columns
                    if column != digest_field}
    if table == "development_pre_execution_plan_projections":
        digest_input["allowed_effect_classes"] = (
            cognitive._require_canonical_effect_class_json(
                digest_input["allowed_effect_classes"]))
    changed[digest_field] = cognitive._domain_separated_digest(
        cognitive._DOMAINS[table], digest_input,
    )
    assert cognitive._row_value_from_mapping(table, changed).to_mapping() == changed
    return changed


def _insert_cognitive(db: sqlite3.Connection, table: str, row: dict[str, object]):
    columns = cognitive._TABLE_COLUMNS[table]
    db.execute("INSERT INTO " + table + " (" + ", ".join(columns)
               + ") VALUES (" + ", ".join("?" for _ in columns) + ")",
               tuple(row[column] for column in columns))


def _advance_selection_head(db: sqlite3.Connection, suffix: str):
    """Test-only coherent later selection, with its distinct immutable owners."""
    head_table = _TABLES[2]
    head_columns = _COLUMNS[2]
    original = dict(zip(head_columns, db.execute(
        "SELECT " + ", ".join(head_columns) + " FROM " + head_table
    ).fetchone(), strict=True))
    proposal_table = "development_model_proposals"
    artifact_table = "development_private_proposal_artifact_bindings"
    source_table = "development_model_source_invocations"
    projection_table = "development_pre_execution_plan_projections"
    evidence_table = "development_model_proposal_evidence_bindings"
    disposition_table = "development_pre_execution_dispositions"
    old_proposal = _cognitive_row(db, proposal_table, "proposal_ref",
                                  original["current_proposal_ref"])
    old_artifact = _cognitive_row(db, artifact_table, "artifact_ref",
                                  old_proposal["artifact_ref"])
    old_source = _cognitive_row(db, source_table, "source_invocation_ref",
                                old_proposal["source_invocation_ref"])
    old_projection = _cognitive_row(db, projection_table, "proposal_ref",
                                    old_proposal["proposal_ref"])
    old_disposition = _cognitive_row(db, disposition_table, "disposition_ref",
                                     original["current_disposition_ref"])
    prefix = "s01selection." + suffix
    artifact_ref = prefix + ".artifact"
    source_ref = prefix + ".source"
    proposal_ref = prefix + ".proposal"
    evidence_ref = prefix + ".evidence"
    disposition_ref = prefix + ".disposition"
    artifact = _reseal_cognitive(artifact_table, old_artifact,
                                 artifact_ref=artifact_ref)
    source = _reseal_cognitive(source_table, old_source,
                               source_invocation_ref=source_ref,
                               artifact_ref=artifact_ref)
    projection = _reseal_cognitive(projection_table, old_projection,
                                   proposal_ref=proposal_ref, artifact_ref=artifact_ref)
    old_evidence = db.execute(
        "SELECT " + ", ".join(cognitive._TABLE_COLUMNS[evidence_table])
        + " FROM " + evidence_table + " WHERE proposal_ref=? ORDER BY role_rank",
        (old_proposal["proposal_ref"],),
    ).fetchall()
    assert len(old_evidence) in (14, 15)
    evidence = tuple(_reseal_cognitive(
        evidence_table,
        dict(zip(cognitive._TABLE_COLUMNS[evidence_table], row, strict=True)),
        proposal_ref=proposal_ref, evidence_set_ref=evidence_ref,
    ) for row in old_evidence)
    evidence_digest = cognitive._domain_separated_digest(
        cognitive_values._EVIDENCE_SET_DOMAIN,
        {"evidence_set_ref": evidence_ref, "proposal_ref": proposal_ref,
         "proposal_phase": old_proposal["proposal_phase"],
         "entries": tuple({name: row[name] for name in (
             "evidence_role", "role_rank", "ordinal", "evidence_ref",
             "evidence_digest", "evidence_binding_digest")}
             for row in evidence)},
    )
    proposal = _reseal_cognitive(
        proposal_table, old_proposal, proposal_ref=proposal_ref,
        source_invocation_ref=source_ref,
        source_invocation_digest=source["source_invocation_digest"],
        artifact_ref=artifact_ref,
        safe_projection_digest=projection["safe_projection_digest"],
        evidence_set_ref=evidence_ref, evidence_set_digest=evidence_digest,
    )
    moved = _reseal_cognitive(
        head_table, original, current_proposal_ref=proposal_ref,
        current_disposition_ref=disposition_ref,
        head_revision=original["head_revision"] + 1,
        updated_at="2098-01-01T00:00:00Z",
    )
    disposition = _reseal_cognitive(
        disposition_table, old_disposition, disposition_ref=disposition_ref,
        proposal_ref=proposal_ref, proposal_digest=proposal["proposal_digest"],
        evidence_set_ref=evidence_ref, evidence_set_digest=evidence_digest,
        supersedes_disposition_ref=old_disposition["disposition_ref"],
        expected_selection_head_revision=original["head_revision"],
        expected_selection_head_digest=original["head_digest"],
        prior_selection_head_revision=original["head_revision"],
        prior_selection_head_digest=original["head_digest"],
        resulting_selection_head_revision=moved["head_revision"],
        selection_head_postimage_digest=moved["head_digest"],
        coordinator_disposition_decided_at="2098-01-01T00:00:00Z",
    )
    for table, row in ((artifact_table, artifact), (source_table, source),
                       (proposal_table, proposal), (projection_table, projection)):
        _insert_cognitive(db, table, row)
    for row in evidence:
        _insert_cognitive(db, evidence_table, row)
    _insert_cognitive(db, disposition_table, disposition)
    db.execute("UPDATE " + head_table
               + " SET current_proposal_ref=?, current_disposition_ref=?, "
               "head_revision=?, updated_at=?, head_digest=?",
               (proposal_ref, disposition_ref, moved["head_revision"],
                moved["updated_at"], moved["head_digest"]))
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert _actual_witness(db).postimages[2] == moved
    return original


def _move_head(db: sqlite3.Connection, role: str, *, suffix: str = "later"):
    if role == "selection":
        return _advance_selection_head(db, suffix)
    index = HEAD_ROLES.index(role)
    table, columns, domain = _TABLES[index], _COLUMNS[index], _DOMAINS[index]
    row = dict(zip(columns, db.execute(
        "SELECT " + ", ".join(columns) + " FROM " + table
    ).fetchone(), strict=True))
    moved = {**row, "head_revision": row["head_revision"] + 1,
             "updated_at": "2098-01-01T00:00:00Z"}
    moved["head_digest"] = _domain_separated_digest(
        domain, {key: moved[key] for key in columns if key != "head_digest"})
    db.execute("UPDATE " + table + " SET head_revision=?, updated_at=?, head_digest=?",
               (moved["head_revision"], moved["updated_at"], moved["head_digest"]))
    assert _actual_witness(db).postimages[index] == moved
    return row


def _restore_head(db: sqlite3.Connection, role: str, row: dict[str, object]):
    table = _TABLES[HEAD_ROLES.index(role)]
    if role == "selection":
        db.execute("UPDATE " + table + " SET current_proposal_ref=?, "
                   "current_disposition_ref=?, current_disposition=?, "
                   "head_revision=?, updated_at=?, head_digest=?",
                   (row["current_proposal_ref"], row["current_disposition_ref"],
                    row["current_disposition"], row["head_revision"],
                    row["updated_at"], row["head_digest"]))
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        return
    db.execute("UPDATE " + table + " SET head_revision=?, updated_at=?, head_digest=?",
               (row["head_revision"], row["updated_at"], row["head_digest"]))


def _selector_for_witness(original, witness):
    safe = original.to_mapping()
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref=safe["mutation_ref"], p1_command=original.p1_command,
        section41_command=original.section41_command, c1_rank15=original.c1_rank15,
        heads=witness.coordinates, stop=safe["stop"],
        prior_decision_digest=safe["reached_owners"][15]["digest"],
        prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
        prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
        expected_branch=safe["expected_branch"], expected_outcome=safe["expected_outcome"],
    )


def _selector_with_mutation(original, mutation_ref: str):
    safe = original.to_mapping()
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref=mutation_ref, p1_command=original.p1_command,
        section41_command=original.section41_command, c1_rank15=original.c1_rank15,
        heads=tuple(safe["heads"]), stop=safe["stop"],
        prior_decision_digest=safe["reached_owners"][15]["digest"],
        prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
        prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
        expected_branch=safe["expected_branch"],
        expected_outcome=safe["expected_outcome"],
    )


def _family(db: sqlite3.Connection):
    return {table: dict(zip(COLUMNS[table], db.execute(
        "SELECT " + ", ".join(COLUMNS[table]) + " FROM " + table
    ).fetchone(), strict=True)) for table in TABLES}


def _reseal(original, command, witness, *, outcome_coordinates=None):
    safe = command.to_mapping()
    context = seal_row(CONTEXT, {
        **original[CONTEXT], "context_ref": safe["context_ref"],
        "mutation_ref": safe["mutation_ref"], "command_safe_bytes": command.safe_bytes,
        "closure_heads_bytes": witness.canonical_bytes, "context_digest": "",
    })
    c = context.mapping
    outcome = seal_row(OUTCOME, {
        **original[OUTCOME], "outcome_value_ref": safe["outcome_value_ref"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "closure_heads_bytes": _canonical({"heads": list(
            witness.coordinates if outcome_coordinates is None else outcome_coordinates
        )}),
        "outcome_value_digest": "",
    })
    o = outcome.mapping
    result = seal_row(RESULT, {
        **original[RESULT], "result_ref": safe["result_ref"],
        "outcome_value_ref": o["outcome_value_ref"],
        "outcome_value_digest": o["outcome_value_digest"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "result_digest": "",
    })
    r = result.mapping
    members = list(safe["reached_owners"])
    members.extend((
        {"role": "terminal_context", "ref": c["context_ref"], "digest": c["context_digest"]},
        {"role": "terminal_outcome", "ref": o["outcome_value_ref"], "digest": o["outcome_value_digest"]},
        {"role": "terminal_result", "ref": r["result_ref"], "digest": r["result_digest"]},
    ))
    if c["acceptance_fact_ref"] is not None:
        members.append({"role": "acceptance_fact", "ref": c["acceptance_fact_ref"],
                        "digest": c["acceptance_fact_digest"]})
    graph = _digest(GRAPH_PROFILE + ".identity", members)
    committed_digest = _digest(plan._COMMITTED_RESULT_DOMAIN, {
        "command_digest": command.command_digest,
        "context_digest": c["context_digest"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_digest": r["result_digest"], "graph_digest": graph,
        "recorded_at": r["recorded_at"],
    })
    receipt = seal_row(RECEIPT, {
        **original[RECEIPT], "receipt_ref": safe["receipt_ref"],
        "mutation_ref": safe["mutation_ref"],
        "command_digest": command.command_digest,
        "family_route": safe["family_route"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "outcome_value_ref": o["outcome_value_ref"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_ref": r["result_ref"], "result_digest": r["result_digest"],
        "graph_digest": graph, "committed_result_digest": committed_digest,
        "receipt_digest": "",
    })
    return context, outcome, result, receipt


def _replace_family(db: sqlite3.Connection, rows):
    # Test-only synthetic corruption. Restore exact trigger definitions before
    # allowing a production writer to inspect this disposable database.
    db.commit()
    db.execute("PRAGMA foreign_keys=OFF")
    triggers = db.execute(
        "SELECT name, sql FROM sqlite_schema WHERE type='trigger' "
        "AND tbl_name IN ('rw0_terminal_contexts','rw0_terminal_outcomes',"
        "'rw0_terminal_results','rw0_terminal_receipts',"
        "'rw0_terminal_anchors') ORDER BY name"
    ).fetchall()
    assert len(triggers) == 12
    db.execute("BEGIN IMMEDIATE")
    for name, _ in triggers:
        db.execute("DROP TRIGGER " + name)
    db.execute("DELETE FROM rw0_terminal_anchors")
    for table in reversed(TABLES):
        db.execute("DELETE FROM " + table)
    for row in rows:
        db.execute("INSERT INTO " + row.table + " (" + ", ".join(COLUMNS[row.table])
                   + ") VALUES (" + ", ".join("?" for _ in row.values) + ")", row.values)
    c, o, result, r = (row.mapping for row in rows)
    anchor = (
        ANCHOR_SCHEMA, r["phase_basis_ref"], r["phase_basis_digest"], r["profile"],
        r["family_route"], r["mutation_ref"], r["command_digest"], c["program_ref"],
        r["p1_decision_ref"], r["context_ref"], r["context_digest"],
        r["outcome_value_ref"], r["outcome_value_digest"], r["result_ref"],
        r["result_digest"], r["receipt_ref"], r["receipt_digest"],
        r["graph_profile"], r["graph_digest"], r["committed_result_digest"],
        r["recorded_at"],
    )
    db.execute("INSERT INTO rw0_terminal_anchors (" + ", ".join(ANCHOR_COLUMNS)
               + ") VALUES (" + ", ".join("?" for _ in anchor) + ")", anchor)
    for _, sql in triggers:
        db.execute(sql)
    db.commit()
    db.execute("PRAGMA foreign_keys=ON")
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert all(checked_row(table, db.execute(
        "SELECT " + ", ".join(COLUMNS[table]) + " FROM " + table
    ).fetchone()).table == table for table in TABLES)


@pytest.mark.parametrize("role", HEAD_ROLES)
def test_s01_each_actual_head_drift_and_synthetic_historical_misbinding(monkeypatch, role):
    def fresh_drift(location, command, source, p1, *, restore):
        with sqlite3.connect(location.database_path) as db:
            baseline = _actual_witness(db)
            original_row = _move_head(db, role, suffix="fresh")
            changed = _terminal_selector(db, command.p1_command,
                                         command.section41_command, command.c1_rank15, p1)
            assert changed.to_mapping()["heads"] != command.to_mapping()["heads"]
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(changed, source) == TerminalConflictV1("stale_currentness")
        with sqlite3.connect(location.database_path) as db:
            assert all(db.execute("SELECT count(*) FROM " + table).fetchone()[0] == 0
                       for table in TABLES)
            if restore:
                _restore_head(db, role, original_row)
                assert _actual_witness(db) == baseline
        return baseline

    # A selection successor has a unique prior-revision disposition. Use a
    # separate disposable family for fresh refusal and synthetic history.
    if role == "selection":
        with prepared_normal_case(monkeypatch) as (location, command, source, p1):
            fresh_drift(location, command, source, p1, restore=False)
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        if role == "selection":
            with sqlite3.connect(location.database_path) as db:
                baseline = _actual_witness(db)
        else:
            baseline = fresh_drift(location, command, source, p1, restore=True)
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
            assert writer._read_terminal_outcome(command, source) == committed
        with sqlite3.connect(location.database_path) as db:
            original_family = _family(db)
            # Same synthetic re-sealer yields a valid positive family first.
            if role == "program":
                _replace_family(db, _reseal(original_family, command, baseline))
        if role == "program":
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._read_terminal_outcome(command, source) == committed
                assert writer._record_terminal_outcome(command, source) == committed
                assert writer._recover_terminal_outcome(command, source).classification == "committed_exact"
        with sqlite3.connect(location.database_path) as db:
            _move_head(db, role, suffix="historical")
            wrong = _terminal_selector(db, command.p1_command,
                                       command.section41_command, command.c1_rank15, p1)
            witness = _actual_witness(db)
            assert witness.postimages[HEAD_ROLES.index(role)] != baseline.postimages[HEAD_ROLES.index(role)]
            assert witness.coordinates == tuple(wrong.to_mapping()["heads"])
            _replace_family(db, _reseal(original_family, wrong, witness))
        # The family is internally self-consistent and every own-row digest is
        # valid. Only the independent immutable P1/phase relationship rejects.
        with acquire_sqlite_writer_session(location) as writer:
            for operation in (writer._read_terminal_outcome, writer._record_terminal_outcome):
                with pytest.raises(SQLiteMutationStoreError) as error:
                    operation(wrong, source)
                assert error.value.error_class == "database_integrity_failure"
            assert writer._recover_terminal_outcome(wrong, source).classification == "unresolved"


def test_s01_witness_grammar_and_each_own_digest(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            raw = db.execute("SELECT closure_heads_bytes FROM " + CONTEXT).fetchone()[0]
            context = dict(zip(COLUMNS[CONTEXT], db.execute(
                "SELECT " + ", ".join(COLUMNS[CONTEXT]) + " FROM " + CONTEXT
            ).fetchone(), strict=True))
        good = witness_from_bytes(raw)
        assert len(raw) <= WITNESS_BYTE_CEILING
        for role in HEAD_ROLES:
            parsed = {"schema_id": WITNESS_SCHEMA,
                      "heads": [{"role": r, "postimage": dict(image)}
                                for r, image in zip(HEAD_ROLES, good.postimages, strict=True)]}
            parsed["heads"][HEAD_ROLES.index(role)]["postimage"]["updated_at"] = "2098-01-01T00:00:00Z"
            with pytest.raises(ValueError):
                witness_from_bytes(_canonical(parsed))
            for mutation in ("missing", "extra", "schema", "revision", "time",
                             "state", "null"):
                images = [dict(image) for image in good.postimages]
                selected = images[HEAD_ROLES.index(role)]
                if mutation == "missing":
                    selected.pop("updated_at")
                elif mutation == "extra":
                    selected["unknown_field"] = "extension"
                elif mutation == "schema":
                    selected["schema_id"] = "governed-execution.wrong-head.v1"
                elif mutation == "revision":
                    selected["head_revision"] = True
                elif mutation == "state":
                    state_field = {
                        "program": "program_state",
                        "work": "work_state",
                        "selection": "current_disposition",
                        "effect": "effect_state",
                        "delivery": "delivery_state",
                    }[role]
                    selected[state_field] = "unsupported_terminal_state"
                elif mutation == "null":
                    selected["updated_at"] = None
                else:
                    selected["updated_at"] = "2020-02-30T00:00:00Z"
                payload = {"schema_id": WITNESS_SCHEMA, "heads": [
                    {"role": r, "postimage": image}
                    for r, image in zip(HEAD_ROLES, images, strict=True)]}
                with pytest.raises(ValueError):
                    witness_from_bytes(_canonical(payload))
        parsed = {"schema_id": WITNESS_SCHEMA,
                  "heads": [{"role": r, "postimage": image}
                            for r, image in zip(HEAD_ROLES, good.postimages, strict=True)]}
        malformed = [
            {"heads": list(good.coordinates)},  # blocked compact v1 projection
            {**parsed, "schema_id": "governed-execution.nwp-rw0-terminal-closure-head-witness-set.v0"},
            {**parsed, "extra": 1},
            {**parsed, "heads": parsed["heads"][:-1]},
            {**parsed, "heads": list(reversed(parsed["heads"]))},
            {**parsed, "heads": [{**parsed["heads"][0], "extra": 1}, *parsed["heads"][1:]]},
            {**parsed, "heads": [{"role": "delivery", "postimage": good.postimages[0]}, *parsed["heads"][1:]]},
            {**parsed, "heads": [parsed["heads"][0], parsed["heads"][0], *parsed["heads"][2:]]},
        ]
        for payload in malformed:
            with pytest.raises(ValueError):
                witness_from_bytes(_canonical(payload))
        nested_duplicate = raw.replace(b'"role":"program"',
                                       b'"role":"program","role":"program"', 1)
        assert nested_duplicate != raw
        for payload in (raw + b" ", b'{"heads":{},"heads":{}}',
                        nested_duplicate, b"x" * (WITNESS_BYTE_CEILING + 1)):
            with pytest.raises(ValueError):
                witness_from_bytes(payload)
        with pytest.raises(ValueError):
            checked_row(CONTEXT, tuple(
                "governed-execution.nwp-rw0-terminal-context.v1" if name == "schema_id" else context[name]
                for name in COLUMNS[CONTEXT]))
        assert context["schema_id"] == CONTEXT_SCHEMA


def test_s01_resealed_outcome_projection_disagrees_with_full_witness(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            original = _family(db)
            witness = _actual_witness(db)
        wrong_coordinates = [dict(item) for item in witness.coordinates]
        wrong_coordinates[0]["digest"] = "0" * 64
        assert wrong_coordinates[0] != witness.coordinates[0]
        with sqlite3.connect(location.database_path) as db:
            _replace_family(db, _reseal(
                original, command, witness, outcome_coordinates=wrong_coordinates))
        with acquire_sqlite_writer_session(location) as writer:
            for operation in (writer._read_terminal_outcome, writer._record_terminal_outcome):
                with pytest.raises(SQLiteMutationStoreError) as error:
                    operation(command, source)
                assert error.value.error_class == "database_integrity_failure"
            assert writer._recover_terminal_outcome(command, source).classification == "unresolved"


def test_s01_resealed_cross_owner_linkage_mismatches_are_historical_integrity(monkeypatch):
    variations = (
        ("program", "current_program_version_ref", "synthetic.version.other"),
        ("work", "program_ref", "synthetic.program.other"),
        ("selection", "program_ref", "synthetic.program.other"),
        ("selection", "work_item_ref", "synthetic.work.other"),
        ("selection", "effect_intent_ref", "synthetic.effect.other"),
        ("effect", "program_ref", "synthetic.program.other"),
        ("effect", "current_effect_fence_ref", "synthetic.fence.other"),
        ("delivery", "program_ref", "synthetic.program.other"),
        ("delivery", "current_delivery_attempt_ref", "synthetic.delivery.other"),
    )
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            original = _family(db)
            baseline = _actual_witness(db)
        for role, field, value in variations:
            index = HEAD_ROLES.index(role)
            images = [dict(image) for image in baseline.postimages]
            image = images[index]
            image[field] = value
            image["head_digest"] = _domain_separated_digest(
                _DOMAINS[index], {key: image[key] for key in _COLUMNS[index]
                                  if key != "head_digest"})
            witness = witness_from_bytes(_canonical({
                "schema_id": WITNESS_SCHEMA,
                "heads": [{"role": r, "postimage": item}
                          for r, item in zip(HEAD_ROLES, images, strict=True)],
            }))
            wrong = _selector_for_witness(command, witness)
            with sqlite3.connect(location.database_path) as db:
                _replace_family(db, _reseal(original, wrong, witness))
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._read_terminal_outcome(wrong, source)
                assert error.value.error_class == "database_integrity_failure", (role, field)
                assert writer._recover_terminal_outcome(wrong, source).classification == "unresolved"


def test_historical_replay_keeps_saved_rows_after_later_valid_heads_and_stop(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            saved = db.execute("SELECT closure_heads_bytes, closure_stop_bytes FROM " + CONTEXT).fetchone()

        def forbidden_current(*args, **kwargs):
            raise AssertionError("historical path consulted a current head or stop")

        with monkeypatch.context() as patch:
            patch.setattr(terminal_runtime, "_current", forbidden_current)
            patch.setattr(terminal_runtime, "_read_global_stop_current", forbidden_current)
            patch.setattr(terminal_runtime, "_read_exact_row", forbidden_current)
            for role in HEAD_ROLES:
                with sqlite3.connect(location.database_path) as db:
                    _move_head(db, role)
                    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
                with acquire_sqlite_writer_session(location) as writer:
                    assert writer._read_terminal_outcome(command, source) == committed
                    assert writer._record_terminal_outcome(command, source) == committed
                    recovered = writer._recover_terminal_outcome(command, source)
                    assert recovered.classification == "committed_exact"
                    assert recovered.committed == committed
                with sqlite3.connect(location.database_path) as db:
                    assert db.execute("SELECT closure_heads_bytes, closure_stop_bytes FROM " + CONTEXT).fetchone() == saved
            with sqlite3.connect(location.database_path) as db:
                db.execute("UPDATE global_stop_current SET version=version+1, updated_at='2098-01-01T00:00:00Z'")
                assert db.execute("PRAGMA foreign_key_check").fetchall() == []
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._read_terminal_outcome(command, source) == committed
                assert writer._record_terminal_outcome(command, source) == committed
                assert writer._recover_terminal_outcome(command, source).classification == "committed_exact"
            with sqlite3.connect(location.database_path) as db:
                assert db.execute("SELECT closure_heads_bytes, closure_stop_bytes FROM " + CONTEXT).fetchone() == saved


@pytest.mark.parametrize("branch", ("candidate_acceptance", "attempt_selecting_replan"))
def test_direct_witness_constructor_matches_checked_factories_and_detaches_mappings(
    monkeypatch, branch,
):
    with prepared_normal_case(monkeypatch, branch) as (location, command, source, prior):
        with sqlite3.connect(location.database_path) as db:
            checked = _actual_witness(db)
        images = tuple(dict(image) for image in checked.postimages)
        coordinates = tuple(dict(head) for head in checked.coordinates)
        direct = TerminalHeadWitness(checked.canonical_bytes, images, coordinates)
        assert direct == checked == witness_from_bytes(checked.canonical_bytes)
        assert direct.canonical_bytes == checked.canonical_bytes
        assert tuple(map(len, direct.postimages)) == (8, 9, 41, 9, 8)
        assert all(type(image) is dict for image in direct.postimages)
        assert all(type(head) is dict for head in direct.coordinates)
        if branch == "attempt_selecting_replan":
            assert direct.postimages[3]["cancellation_effect_intent_ref"] is None
        typed = (
            programs.development_program_head_row_value_from_row_tuple(
                tuple(images[0][name] for name in _COLUMNS[0])),
            programs.development_work_item_head_row_value_from_row_tuple(
                tuple(images[1][name] for name in _COLUMNS[1])),
            cognitive._row_value_from_mapping(_TABLES[2], images[2]),
            effects.development_effect_head_row_value_from_row_tuple(
                tuple(images[3][name] for name in _COLUMNS[3])),
            effects.development_delivery_head_row_value_from_row_tuple(
                tuple(images[4][name] for name in _COLUMNS[4])),
        )
        assert witness_from_typed(typed) == direct
        image_before = direct.postimages
        coordinates_before = direct.coordinates
        images[0]["updated_at"] = "0000-00-00T00:00:00Z"
        coordinates[0]["digest"] = "0" * 64
        returned_images = direct.postimages
        returned_coordinates = direct.coordinates
        returned_images[0]["head_digest"] = "0" * 64
        returned_coordinates[0]["owner_ref"] = "detached.example"
        assert direct.postimages == image_before
        assert direct.coordinates == coordinates_before
        assert witness_from_bytes(direct.canonical_bytes) == direct


def test_direct_witness_constructor_closed_components_before_hostile_equality(monkeypatch):
    class BytesSubclass(bytes):
        pass

    class TupleSubclass(tuple):
        pass

    class DictSubclass(dict):
        pass

    class StringSubclass(str):
        pass

    class IntegerSubclass(int):
        pass

    calls = []

    class EqualitySpy:
        def __eq__(self, other):
            calls.append(type(other).__name__)
            return False

    spy = EqualitySpy()
    assert spy != "calibration"
    assert calls
    calls.clear()

    with prepared_normal_case(monkeypatch) as (location, command, source, prior):
        with sqlite3.connect(location.database_path) as db:
            good = _actual_witness(db)
            _move_head(db, "program", suffix="different-valid")
            different = _actual_witness(db)
        images = good.postimages
        coordinates = good.coordinates

        def invalid(raw, supplied_images, supplied_coordinates):
            with pytest.raises(ValueError):
                TerminalHeadWitness(raw, supplied_images, supplied_coordinates)
            assert calls == []

        invalid("not bytes", [], {})
        invalid(b"{}", (), ())
        invalid(BytesSubclass(good.canonical_bytes), images, coordinates)
        invalid(good.canonical_bytes + b" ", images, coordinates)
        invalid(b"x" * (WITNESS_BYTE_CEILING + 1), images, coordinates)
        invalid(good.canonical_bytes, list(images), coordinates)
        invalid(good.canonical_bytes, TupleSubclass(images), coordinates)
        invalid(good.canonical_bytes, images, list(coordinates))
        invalid(good.canonical_bytes, images, TupleSubclass(coordinates))
        invalid(good.canonical_bytes, images[:-1], coordinates)
        invalid(good.canonical_bytes, images, coordinates[:-1])
        invalid(good.canonical_bytes, different.postimages, coordinates)
        invalid(good.canonical_bytes, images, different.coordinates)
        invalid(good.canonical_bytes, tuple(reversed(images)), coordinates)
        invalid(good.canonical_bytes, images, tuple(reversed(coordinates)))

        for value in (
            DictSubclass(images[0]),
            {key: item for key, item in images[0].items()
             if key != "updated_at"},
            {**images[0], "unknown": "x"},
            {**images[0], "schema_id": "wrong"},
            {**images[0], "head_digest": "0" * 64},
            {**images[0], "head_revision": True},
            {**images[0], "head_revision": IntegerSubclass(0)},
            {**images[0], "updated_at": StringSubclass(images[0]["updated_at"])},
            {**images[0], "updated_at": spy},
            {**{key: item for key, item in images[0].items()
                if key != "updated_at"}, StringSubclass("updated_at"): spy},
        ):
            changed = (value, *images[1:])
            invalid(good.canonical_bytes, changed, coordinates)
        for value in (
            DictSubclass(coordinates[0]),
            {key: item for key, item in coordinates[0].items() if key != "role"},
            {**coordinates[0], "extra": "x"},
            {**coordinates[0], "role": StringSubclass("program")},
            {**coordinates[0], "revision": True},
            {**coordinates[0], "revision": IntegerSubclass(0)},
            {**coordinates[0], "digest": spy},
            {**{key: item for key, item in coordinates[0].items()
                if key != "digest"}, StringSubclass("digest"): spy},
        ):
            invalid(good.canonical_bytes, images, (value, *coordinates[1:]))
        parsed = json.loads(good.canonical_bytes)
        for changed in (
            {**parsed, "schema_id": "wrong"},
            {**parsed, "extra": "x"},
            {**parsed, "heads": list(reversed(parsed["heads"]))},
            {**parsed, "heads": [{**parsed["heads"][0], "postimage":
                                  {**parsed["heads"][0]["postimage"],
                                   "head_digest": "0" * 64}},
                                 *parsed["heads"][1:]]},
        ):
            invalid(_canonical(changed), images, coordinates)


def _set_synthetic_later_stop(db: sqlite3.Connection, *, active: bool):
    """Explicit test fixture, not a claim of a product stop transition."""
    if active:
        from ge_nwp_coordinator.global_stop import GlobalStopOperatorDecision
        from ge_nwp_coordinator.persistence_contracts import (
            global_stop_operator_decision_canonical_digest,
            global_stop_operator_decision_canonical_json,
        )
        decision = GlobalStopOperatorDecision(
            decision_ref="later-terminal-witness-stop-decision", authorized=True,
            reason="accepted")
        db.execute(
            "INSERT INTO global_stop_operator_decision_receipts "
            "(decision_ref, authorized, reason, schema_id, canonical_json, "
            "canonical_digest, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (decision.decision_ref, 1, decision.reason, decision.schema_id,
             global_stop_operator_decision_canonical_json(decision),
             global_stop_operator_decision_canonical_digest(decision),
             "2098-01-01T00:00:00Z"),
        )
        db.execute(
            "UPDATE global_stop_current SET version=version+1, active=1, "
            "stop_id='later-terminal-witness-stop', reason_class='operator_stop', "
            "issuer_ref='synthetic-operator-policy', issued_at='2098-01-01T00:00:00Z', "
            "operator_decision_ref=?, updated_at='2098-01-01T00:00:00Z'",
            (decision.decision_ref,),
        )
    else:
        db.execute(
            "UPDATE global_stop_current SET version=version+1, active=0, "
            "stop_id=NULL, reason_class=NULL, issuer_ref=NULL, issued_at=NULL, "
            "operator_decision_ref=NULL, updated_at='2098-01-02T00:00:00Z'"
        )
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []


@pytest.mark.parametrize("branch", ("candidate_acceptance", "attempt_selecting_replan"))
def test_whole_operation_historical_admission_and_later_stop_are_separate(
    monkeypatch, request, branch,
):
    with prepared_normal_case(monkeypatch, branch) as (location, command, source, prior):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            saved = {table: db.execute("SELECT * FROM " + table).fetchall()
                     for table in TABLES}
            acceptance = db.execute(
                "SELECT * FROM rw0_c2_bootstrap_acceptance_facts"
            ).fetchall()
            for role in HEAD_ROLES:
                _move_head(db, role, suffix="complete-operation")
            _set_synthetic_later_stop(db, active=True)

        with monkeypatch.context() as patch:
            events = _observe_complete_terminal_sql(patch, historical=True)
            with acquire_sqlite_writer_session(location) as writer:
                for active in (True, False):
                    if not active:
                        with sqlite3.connect(location.database_path) as db:
                            _set_synthetic_later_stop(db, active=False)
                    assert writer._read_terminal_outcome(command, source) == committed
                    assert writer._record_terminal_outcome(command, source) == committed
                    recovered = writer._recover_terminal_outcome(command, source)
                    assert recovered.classification == "committed_exact"
                    assert recovered.committed == committed
            _assert_historical_authorizer_events(
                events, operations=6, reached_terminal=True)
        with sqlite3.connect(location.database_path) as db:
            assert {table: db.execute("SELECT * FROM " + table).fetchall()
                    for table in TABLES} == saved
            assert db.execute(
                "SELECT * FROM rw0_c2_bootstrap_acceptance_facts"
            ).fetchall() == acceptance
        request.node.user_properties.append((
            "historical_read_phase_map",
            json.dumps([list(event) for event in events if event[1] == "operation"],
                       separators=(",", ":"), sort_keys=False),
        ))


def test_whole_operation_managed_stop_denial_prevents_terminal_disclosure(
    monkeypatch,
):
    with prepared_normal_case(monkeypatch) as (location, command, source, prior):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            before = {table: db.execute("SELECT * FROM " + table).fetchall()
                      for table in TABLES}
        with monkeypatch.context() as patch:
            events = _observe_complete_terminal_sql(
                patch, historical=True, deny_managed_stop=True)
            with acquire_sqlite_writer_session(location) as writer:
                for method in (writer._read_terminal_outcome,
                               writer._record_terminal_outcome):
                    with pytest.raises(SQLiteMutationStoreError) as error:
                        method(command, source)
                    assert error.value.error_class == "mutation_failed"
                assert writer._recover_terminal_outcome(
                    command, source).classification == "unresolved"
            _assert_historical_authorizer_events(
                events, operations=3, reached_terminal=False)
            assert any(phase == "managed" and table == "global_stop_current"
                       and denied for _, kind, phase, table, _, denied in events
                       if kind == "operation")
        with sqlite3.connect(location.database_path) as db:
            assert {table: db.execute("SELECT * FROM " + table).fetchall()
                    for table in TABLES} == before
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._read_terminal_outcome(command, source) == committed
            assert writer._record_terminal_outcome(command, source) == committed
            assert writer._recover_terminal_outcome(
                command, source).classification == "committed_exact"


def test_whole_operation_malformed_stop_row_fails_real_managed_validation(
    monkeypatch,
):
    with prepared_normal_case(monkeypatch) as (location, command, source, prior):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as db:
            family_before = {table: db.execute("SELECT * FROM " + table).fetchall()
                             for table in TABLES}
        with acquire_sqlite_writer_session(location) as writer:
            with sqlite3.connect(location.database_path) as db:
                stop_before = db.execute(
                    "SELECT updated_at FROM global_stop_current"
                ).fetchone()[0]
                # SQL permits this length; the unchanged managed validator rejects
                # the impossible calendar value returned by its real SELECT.
                db.execute(
                    "UPDATE global_stop_current SET updated_at='2098-99-99T00:00:00Z'"
                )
            with monkeypatch.context() as patch:
                events = _observe_complete_terminal_sql(patch, historical=True)
                for method in (writer._read_terminal_outcome,
                               writer._record_terminal_outcome):
                    with pytest.raises(SQLiteMutationStoreError) as error:
                        method(command, source)
                    assert error.value.error_class == "database_integrity_failure"
                assert writer._recover_terminal_outcome(
                    command, source).classification == "unresolved"
                # The session predates this test-only row fault, so no acquisition
                # callback is expected inside this observer interval.
                assert any(kind == "operation" and phase == "managed"
                           and table == "global_stop_current" and not denied
                           for _, kind, phase, table, _, denied in events)
                assert all(phase != "terminal" for _, kind, phase, *_ in events
                           if kind == "operation")
            with sqlite3.connect(location.database_path) as db:
                assert {table: db.execute("SELECT * FROM " + table).fetchall()
                        for table in TABLES} == family_before
            with sqlite3.connect(location.database_path) as db:
                db.execute("UPDATE global_stop_current SET updated_at=?", (stop_before,))
            assert writer._read_terminal_outcome(command, source) == committed
            assert writer._record_terminal_outcome(command, source) == committed
            assert writer._recover_terminal_outcome(
                command, source).classification == "committed_exact"


def test_historical_absence_compatible_and_incompatible_winner_use_same_policy(
    monkeypatch,
):
    with prepared_normal_case(monkeypatch) as (location, command, source, prior):
        with monkeypatch.context() as patch:
            absent_events = _observe_complete_terminal_sql(patch, historical=True)
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._recover_terminal_outcome(
                    command, source).classification == "definitely_not_committed"
                assert writer._recover_terminal_outcome(
                    command, replace(source, old_execution_excluded=False)
                ).classification == "unresolved"
            _assert_historical_authorizer_events(
                absent_events, operations=2, reached_terminal=True)
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
        competitor = _selector_with_mutation(command, "terminal.competing.historical")
        with monkeypatch.context() as patch:
            compatible_events = _observe_complete_terminal_sql(patch, historical=True)
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._recover_terminal_outcome(
                    competitor, source).classification == "definitely_not_committed"
            _assert_historical_authorizer_events(
                compatible_events, operations=1, reached_terminal=True)
        with sqlite3.connect(location.database_path) as db:
            original = _family(db)
            baseline = _actual_witness(db)
            images = [dict(image) for image in baseline.postimages]
            work = images[1]
            work["program_ref"] = "synthetic.program.other"
            work["head_digest"] = _domain_separated_digest(
                _DOMAINS[1], {key: work[key] for key in _COLUMNS[1]
                              if key != "head_digest"})
            inconsistent = witness_from_bytes(_canonical({
                "schema_id": WITNESS_SCHEMA,
                "heads": [{"role": role, "postimage": image}
                          for role, image in zip(HEAD_ROLES, images, strict=True)],
            }))
            wrong_selector = _selector_for_witness(command, inconsistent)
            _replace_family(db, _reseal(original, wrong_selector, inconsistent))
        with monkeypatch.context() as patch:
            incompatible_events = _observe_complete_terminal_sql(patch, historical=True)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._read_terminal_outcome(wrong_selector, source)
                assert error.value.error_class == "database_integrity_failure"
                assert writer._recover_terminal_outcome(
                    competitor, source).classification == "unresolved"
            _assert_historical_authorizer_events(
                incompatible_events, operations=2, reached_terminal=True)


def test_fresh_receipt_miss_still_reads_current_heads_and_stop(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, prior):
        with sqlite3.connect(location.database_path) as db:
            _set_synthetic_later_stop(db, active=True)
            changed = _terminal_selector(
                db, command.p1_command, command.section41_command,
                command.c1_rank15, prior)
        assert changed.to_mapping()["stop"] != command.to_mapping()["stop"]
        with monkeypatch.context() as patch:
            events = _observe_complete_terminal_sql(patch, historical=False)
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._record_terminal_outcome(
                    command, source) == TerminalConflictV1("stale_currentness")
                assert writer._record_terminal_outcome(changed, source).outcome == "accept"
            operation_ids = {identity for identity, kind, *_ in events
                             if kind == "operation"}
            assert len(operation_ids) == 2
            for identity in operation_ids:
                terminal_reads = {table for observed, kind, phase, table, _, denied
                                  in events if observed == identity and kind == "operation"
                                  and phase == "terminal" and not denied}
                assert set(_TABLES) <= terminal_reads
                assert "global_stop_current" in terminal_reads
                assert RECEIPT in terminal_reads
