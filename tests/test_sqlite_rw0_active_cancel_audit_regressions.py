"""Connected counterexamples for the active-cancel audit repair."""
from __future__ import annotations

import sqlite3

import pytest

from ge_nwp_coordinator import _development_decision_row_values as decisions
from ge_nwp_coordinator import _development_effect_row_values as effects
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator._worker_execution_semantic_values import EffectFenceV1, DeliveryEnvelopeV1
from ge_nwp_coordinator import sqlite_transition_transaction as transaction
from ge_nwp_coordinator import sqlite_writer_session as writer_session_module
from ge_nwp_coordinator import _sqlite_rw0_cancel_decision as decision_runtime
from ge_nwp_coordinator import _sqlite_rw0_cancel_pre_effect_terminal as terminal_runtime
from ge_nwp_coordinator._rw0_cancel_decision_plan import build_cancel_decision_plan
from ge_nwp_coordinator._rw0_cancel_decision_rows import BINDING as DECISION_BINDING, COLUMNS as DECISION_COLUMNS
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_plan import build_cancel_terminal_plan
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_rows import COLUMNS as TERMINAL_COLUMNS
from ge_nwp_coordinator import _rw0_cancel_pre_effect_terminal_contracts as terminal_contracts
from ge_nwp_coordinator import _rw0_c1_row_values as c1_rows
from ge_nwp_coordinator import _rw0_cancel_pre_effect_terminal_plan as terminal_plan
from ge_nwp_coordinator._sqlite_rw0_cancel_currentness import CancelCurrentnessV1
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import _canonical
from ge_nwp_coordinator._sqlite_rw0_terminal_anchor_migration_invariants_0010 import verify_terminal_anchor_families_0010
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_active_cancel_connected import prepared_cancel_case, _row
from test_sqlite_rw0_active_cancel_decision import _variation as decision_variation
from test_sqlite_rw0_active_cancel_terminal import _ready
from test_sqlite_rw0_active_cancel_verification import _reprepare
from rw0_active_cancel_audit_repair_fixtures import seed_selected_second_attempt_author_target
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_contracts import RecordRW0CancelPreEffectTerminalCommandV1


def _stage_command(db: sqlite3.Connection, command, stage: str):
    intent = _row(db, "development_effect_intents", "effect_class=?", (stage,))
    fence = _row(db, "development_effect_fences", "effect_intent_ref=?",
                 (intent["effect_intent_ref"],))
    effect_head = _row(db, "development_effect_heads", "effect_intent_ref=?",
                       (intent["effect_intent_ref"],))
    delivery_head = _row(db, "development_delivery_heads", "effect_intent_ref=?",
                         (intent["effect_intent_ref"],))
    m = command.to_mapping()
    target = m["target"]
    target.update(effect_intent_ref=intent["effect_intent_ref"],
                  effect_class=stage, effect_fence_ref=fence["effect_fence_ref"],
                  effect_fence_digest=fence["effect_fence_digest"],
                  effect_head=effect_head,
                  delivery_attempt_ref=delivery_head["current_delivery_attempt_ref"],
                  delivery_head=delivery_head,
                  capsule_manifest_ref="capsule-manifest.d1",
                  capsule_digest=intent["portable_capsule_digest"])
    evidence = m["evidence"]
    evidence[0].update(ref=intent["effect_intent_ref"], digest=effect_head["head_digest"])
    evidence[1].update(ref=fence["effect_fence_ref"], digest=fence["effect_fence_digest"])
    evidence.append({"role": "cancel_target_capsule", "ref": "capsule-manifest.d1",
                     "digest": intent["portable_capsule_digest"]})
    return _reprepare(command, target=target, evidence=evidence)


@pytest.mark.parametrize("stage", ("validate_candidate", "review_candidate"))
def test_ac01_legitimate_later_stage_target_retains_own_lineage(monkeypatch, stage):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with sqlite3.connect(location.database_path) as db:
            stage_command = _stage_command(db, command, stage)
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_active_cancel_decision(stage_command)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._verify_active_cancel_currentness(stage_command).classification == (
                "locally_current_source_unverified")
            assert writer._record_active_cancel_decision(stage_command) == committed


def test_ac07_artificial_source_flag_has_no_effect_authority(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_active_cancel_decision(command)
        with acquire_sqlite_writer_session(location) as writer:
            default = writer._verify_active_cancel_currentness(command)
            explicit_true = writer._verify_active_cancel_currentness(command, True)
            explicit_false = writer._verify_active_cancel_currentness(command, False)
        assert default.classification == explicit_true.classification == "locally_current_source_unverified"
        assert explicit_false.classification == "external_source_unresolved"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_pre_effect_receipts").fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM rw0_wire_cancellation_request_observations").fetchone() == (0,)


def _insert_row(db: sqlite3.Connection, table: str, columns: tuple[str, ...], value: dict[str, object]) -> None:
    db.execute(f"INSERT INTO {table} ({', '.join(columns)}) "
               f"VALUES ({', '.join('?' for _ in columns)})",
               tuple(value[name] for name in columns))


def _other_version_target(db: sqlite3.Connection, command):
    base = command.to_mapping()
    version = base["program"]["program_version_ref"]
    intent = _row(db, "development_effect_intents", "effect_class=?", ("validate_candidate",))
    fence = _row(db, "development_effect_fences", "effect_intent_ref=?", (intent["effect_intent_ref"],))
    delivery = _row(db, "development_delivery_attempts", "effect_intent_ref=?", (intent["effect_intent_ref"],))
    effect_head = _row(db, "development_effect_heads", "effect_intent_ref=?", (intent["effect_intent_ref"],))
    delivery_head = _row(db, "development_delivery_heads", "effect_intent_ref=?", (intent["effect_intent_ref"],))
    assert intent["program_version_ref"] != version
    ref = "effect.audit.other-version"
    fence_ref = "fence.audit.other-version"
    delivery_ref = "delivery.audit.other-version"
    intent.update(effect_intent_ref=ref, program_version_ref=version)
    icols = effects._DEVELOPMENT_EFFECT_INTENT_COLUMNS
    intent["effect_intent_digest"] = _domain_separated_digest(
        effects._EFFECT_INTENT_DOMAIN,
        {key: intent[key] for key in icols if key != "effect_intent_digest"})
    effects.development_effect_intent_row_value_from_row_tuple(tuple(intent[key] for key in icols))
    _insert_row(db, "development_effect_intents", icols, intent)

    fence.update(effect_fence_ref=fence_ref, effect_intent_ref=ref, program_version_ref=version)
    fcols = effects._DEVELOPMENT_EFFECT_FENCE_COLUMNS
    parsed_fence = effects.development_effect_fence_row_value_from_row_tuple(
        tuple(_row(db, "development_effect_fences", "effect_class=?", ("validate_candidate",))[key]
              for key in fcols)).effect_fence
    fence_value = parsed_fence.to_mapping()
    fence_value.update(effect_fence_ref=fence_ref, effect_intent_ref=ref,
                       program_version_ref=version)
    fence["effect_fence_digest"] = _domain_separated_digest(
        EffectFenceV1._DOMAIN,
        {key: value for key, value in fence_value.items() if key != "effect_fence_digest"})
    EffectFenceV1.from_mapping({**fence_value, "effect_fence_digest": fence["effect_fence_digest"]})
    effects.development_effect_fence_row_value_from_row_tuple(tuple(fence[key] for key in fcols))
    _insert_row(db, "development_effect_fences", fcols, fence)

    effect_head.update(effect_intent_ref=ref, current_effect_fence_ref=fence_ref)
    ehcols = effects._DEVELOPMENT_EFFECT_HEAD_COLUMNS
    effect_head["head_digest"] = _domain_separated_digest(
        effects._EFFECT_HEAD_DOMAIN,
        {key: effect_head[key] for key in ehcols if key != "head_digest"})
    effects.development_effect_head_row_value_from_row_tuple(tuple(effect_head[key] for key in ehcols))
    _insert_row(db, "development_effect_heads", ehcols, effect_head)

    delivery.update(delivery_attempt_ref=delivery_ref, program_version_ref=version,
                    effect_intent_ref=ref, effect_fence_ref=fence_ref,
                    effect_fence_digest=fence["effect_fence_digest"])
    dcols = effects._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS
    envelope = {key: delivery[key] for key in DeliveryEnvelopeV1._FIELDS
                if key != "delivery_envelope_digest"}
    delivery["delivery_envelope_digest"] = _domain_separated_digest(
        DeliveryEnvelopeV1._DOMAIN, envelope)
    DeliveryEnvelopeV1.from_mapping({**envelope,
        "delivery_envelope_digest": delivery["delivery_envelope_digest"]})
    delivery["delivery_attempt_digest"] = _domain_separated_digest(
        effects._DELIVERY_ATTEMPT_DOMAIN,
        {key: delivery[key] for key in ("delivery_envelope_digest", "delivery_kind",
           "delivery_number", "predecessor_delivery_attempt_ref", "basis_decision_ref", "recorded_at")}
        | {"schema_id": effects._DELIVERY_ATTEMPT_WRAPPER_SCHEMA})
    effects.development_delivery_attempt_row_value_from_row_tuple(tuple(delivery[key] for key in dcols))
    _insert_row(db, "development_delivery_attempts", dcols, delivery)

    delivery_head.update(effect_intent_ref=ref, current_delivery_attempt_ref=delivery_ref)
    dhcols = effects._DEVELOPMENT_DELIVERY_HEAD_COLUMNS
    delivery_head["head_digest"] = _domain_separated_digest(
        effects._DELIVERY_HEAD_DOMAIN,
        {key: delivery_head[key] for key in dhcols if key != "head_digest"})
    effects.development_delivery_head_row_value_from_row_tuple(tuple(delivery_head[key] for key in dhcols))
    _insert_row(db, "development_delivery_heads", dhcols, delivery_head)
    return intent, fence, delivery, effect_head, delivery_head


def _cross_version_command(db: sqlite3.Connection, command):
    intent, fence, delivery, effect_head, delivery_head = _other_version_target(db, command)
    m = command.to_mapping()
    target = m["target"]
    target.update(effect_intent_ref=intent["effect_intent_ref"],
                  effect_class=intent["effect_class"], effect_fence_ref=fence["effect_fence_ref"],
                  effect_fence_digest=fence["effect_fence_digest"], effect_head=effect_head,
                  delivery_attempt_ref=delivery["delivery_attempt_ref"],
                  delivery_head=delivery_head,
                  capsule_manifest_ref="capsule-manifest.d1",
                  capsule_digest=intent["portable_capsule_digest"])
    evidence = m["evidence"]
    evidence[0].update(ref=intent["effect_intent_ref"], digest=effect_head["head_digest"])
    evidence[1].update(ref=fence["effect_fence_ref"], digest=fence["effect_fence_digest"])
    evidence.append({"role": "cancel_target_capsule", "ref": "capsule-manifest.d1",
                     "digest": intent["portable_capsule_digest"]})
    return _reprepare(command, target=target, evidence=evidence)


def test_ac01_other_valid_version_target_cannot_be_bound_to_old_phase(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with sqlite3.connect(location.database_path) as db:
            wrong = _cross_version_command(db, command)
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as raised:
                writer._record_active_cancel_decision(wrong)
            assert raised.value.error_class == "database_integrity_failure"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (0,)


def test_ac01_selected_second_attempt_target_cannot_close_first_phase(monkeypatch):
    with prepared_cancel_case(monkeypatch, branch="candidate_repair") as (location, command):
        with sqlite3.connect(location.database_path) as db:
            attempt, attempt_fence, intent, fence, author, delivery, head, delivery_head = (
                seed_selected_second_attempt_author_target(db, command))
            phase = _row(db, "rw0_phase_instances")
            assert intent["program_ref"] == phase["program_ref"]
            assert attempt["semantic_attempt_ref"] != phase["semantic_attempt_ref"]
            assert attempt["program_version_ref"] != phase["program_version_ref"]
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        m = command.to_mapping()
        target = m["target"]
        target.update(effect_intent_ref=intent["effect_intent_ref"],
                      effect_fence_ref=fence["effect_fence_ref"],
                      effect_fence_digest=fence["effect_fence_digest"],
                      effect_head=head, delivery_attempt_ref=delivery["delivery_attempt_ref"],
                      delivery_head=delivery_head,
                      originating_command_ref=author["command_ref"],
                      originating_command_digest=author["command_digest"])
        evidence = m["evidence"]
        evidence[0].update(ref=intent["effect_intent_ref"], digest=head["head_digest"])
        evidence[1].update(ref=fence["effect_fence_ref"], digest=fence["effect_fence_digest"])
        wrong = _reprepare(command, target=target, evidence=evidence)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as raised:
                writer._record_active_cancel_decision(wrong)
            assert raised.value.error_class == "database_integrity_failure"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (0,)


def test_ac01_persisted_cross_version_witness_cannot_verify_or_close(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with sqlite3.connect(location.database_path) as db:
            wrong = _cross_version_command(db, command)
            plan = build_cancel_decision_plan(wrong, "2020-01-01T00:00:00Z")
            decision = plan.decision.identity_mapping()
            decision["decision_digest"] = plan.decision.decision_digest
            _insert_row(db, "development_decisions", decisions._DEVELOPMENT_DECISION_COLUMNS,
                        decision)
            for binding in plan.bindings:
                _insert_row(db, binding.table, DECISION_COLUMNS[binding.table], binding.mapping)
            _insert_row(db, plan.receipt.table, DECISION_COLUMNS[plan.receipt.table],
                        plan.receipt.mapping)
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._verify_active_cancel_currentness(wrong).classification == "integrity_failure"
        diagnostic = CancelCurrentnessV1(
            "proven_coordinator_mismatch", "effect_head",
            wrong.to_mapping()["target"]["effect_intent_ref"], "1" * 64,
            _canonical({"heads": {}}),
            _canonical({"stop": wrong.to_mapping()["stop"]}),
            _canonical({"classification": "proven_coordinator_mismatch",
                        "mismatch_class": "effect_head",
                        "mismatch_ref": wrong.to_mapping()["target"]["effect_intent_ref"],
                        "mismatch_digest": "1" * 64}),
        )
        terminal = RecordRW0CancelPreEffectTerminalCommandV1.prepare(
            mutation_ref="mutation.audit.cross-version.block", decision_command=wrong,
            committed=plan.committed, verification=diagnostic)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as raised:
                writer._record_cancel_pre_effect_block(terminal)
            assert raised.value.error_class == "database_integrity_failure"
            assert writer._recover_cancel_pre_effect_block(terminal).status == "unresolved"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_pre_effect_receipts").fetchone() == (0,)


@pytest.mark.parametrize("family", ("decision", "terminal"))
def test_ac02_success_replay_and_recovery_make_one_actual_commit(monkeypatch, family):
    with prepared_cancel_case(monkeypatch) as (location, command):
        terminal = _ready(location, command)[2] if family == "terminal" else None
        original_commit = transaction._ControllerConnectionScope.commit
        commits: list[int] = []

        def counted_commit(self):
            commits.append(1)
            return original_commit(self)

        with monkeypatch.context() as patch:
            patch.setattr(transaction._ControllerConnectionScope, "commit", counted_commit)
            with acquire_sqlite_writer_session(location) as writer:
                fresh = (writer._record_active_cancel_decision(command) if family == "decision"
                         else writer._record_cancel_pre_effect_block(terminal))
            with acquire_sqlite_writer_session(location) as writer:
                replay = (writer._record_active_cancel_decision(command) if family == "decision"
                          else writer._record_cancel_pre_effect_block(terminal))
                recovered = (writer._recover_active_cancel_decision(command) if family == "decision"
                             else writer._recover_cancel_pre_effect_block(terminal))
        assert commits == [1]
        assert replay == fresh
        assert recovered.status == "committed_exact"
        assert recovered.committed == fresh
        with sqlite3.connect(location.database_path) as db:
            table = ("rw0_cancel_decision_receipts" if family == "decision"
                     else "rw0_cancel_pre_effect_receipts")
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (1,)


@pytest.mark.parametrize("family", ("decision", "terminal"))
def test_ac02_real_commit_without_close_proof_is_uncertain(monkeypatch, family):
    with prepared_cancel_case(monkeypatch) as (location, command):
        terminal = None
        if family == "terminal":
            _, _, terminal, _ = _ready(location, command)
        commits: list[int] = []
        original_commit = transaction._ControllerConnectionScope.commit
        original_close = transaction._ControllerConnectionScope.close_after_commit

        def counted_commit(self):
            commits.append(1)
            return original_commit(self)

        def unproved_close(self, *, commit_succeeded, force_cleanup):
            result = original_close(self, commit_succeeded=commit_succeeded,
                                    force_cleanup=force_cleanup)
            assert result is True
            self._close_proved = False
            return False

        with monkeypatch.context() as patch:
            patch.setattr(transaction._ControllerConnectionScope, "commit", counted_commit)
            patch.setattr(transaction._ControllerConnectionScope, "close_after_commit", unproved_close)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as raised:
                    if family == "decision":
                        writer._record_active_cancel_decision(command)
                    else:
                        writer._record_cancel_pre_effect_block(terminal)
                assert raised.value.error_class == "commit_outcome_unknown"
        assert commits == [1]
        with sqlite3.connect(location.database_path) as db:
            table = ("rw0_cancel_decision_receipts" if family == "decision"
                     else "rw0_cancel_pre_effect_receipts")
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (1,)
        with acquire_sqlite_writer_session(location) as writer:
            recovered = (writer._recover_active_cancel_decision(command) if family == "decision"
                         else writer._recover_cancel_pre_effect_block(terminal))
        assert recovered.status == "committed_exact"


@pytest.mark.parametrize("family", ("decision", "terminal"))
def test_ac02_precommit_failure_rolls_back_without_commit(monkeypatch, family):
    with prepared_cancel_case(monkeypatch) as (location, command):
        terminal = _ready(location, command)[2] if family == "terminal" else None
        module = decision_runtime if family == "decision" else terminal_runtime
        original_commit = transaction._ControllerConnectionScope.commit
        commits: list[int] = []

        def counted_commit(self):
            commits.append(1)
            return original_commit(self)

        def fail_before_write(*_args):
            raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)

        with monkeypatch.context() as patch:
            patch.setattr(transaction._ControllerConnectionScope, "commit", counted_commit)
            patch.setattr(module, "write_after_fencing", fail_before_write)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as raised:
                    (writer._record_active_cancel_decision(command) if family == "decision"
                     else writer._record_cancel_pre_effect_block(terminal))
                assert raised.value.error_class == "mutation_failed"
        assert commits == []
        with acquire_sqlite_writer_session(location) as writer:
            recovery = (writer._recover_active_cancel_decision(command) if family == "decision"
                        else writer._recover_cancel_pre_effect_block(terminal))
        assert recovery.status == "definitely_not_committed"


@pytest.mark.parametrize("family", ("decision", "terminal"))
@pytest.mark.parametrize("failure_site", ("commit_response", "outer_cleanup"))
def test_ac02_post_commit_fault_is_uncertain_until_exact_recovery(
    monkeypatch, family, failure_site,
):
    with prepared_cancel_case(monkeypatch) as (location, command):
        terminal = _ready(location, command)[2] if family == "terminal" else None
        original_commit = transaction._ControllerConnectionScope.commit
        original_cleanup = writer_session_module._stabilize_rw0_c1_outer_operation_close
        commits: list[int] = []

        def lost_commit_response(self):
            commits.append(1)
            original_commit(self)
            raise sqlite3.OperationalError("test-only lost commit response")

        def failed_outer_cleanup(resource, correlation):
            original_cleanup(resource, correlation)
            raise RuntimeError("test-only outer cleanup failure")

        with monkeypatch.context() as patch:
            if failure_site == "commit_response":
                patch.setattr(transaction._ControllerConnectionScope, "commit", lost_commit_response)
            else:
                def counted_commit(self):
                    commits.append(1)
                    return original_commit(self)
                patch.setattr(transaction._ControllerConnectionScope, "commit", counted_commit)
                patch.setattr(writer_session_module,
                              "_stabilize_rw0_c1_outer_operation_close", failed_outer_cleanup)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as raised:
                    (writer._record_active_cancel_decision(command) if family == "decision"
                     else writer._record_cancel_pre_effect_block(terminal))
                assert raised.value.error_class == "commit_outcome_unknown"
        assert commits == [1]
        with acquire_sqlite_writer_session(location) as writer:
            recovery = (writer._recover_active_cancel_decision(command) if family == "decision"
                        else writer._recover_cancel_pre_effect_block(terminal))
        assert recovery.status == "committed_exact"
        with sqlite3.connect(location.database_path) as db:
            table = ("rw0_cancel_decision_receipts" if family == "decision"
                     else "rw0_cancel_pre_effect_receipts")
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (1,)


def test_ac03_differently_named_orphan_phase_binding_blocks_record_and_recovery(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        other = decision_variation(command, mutation_ref="mutation.orphan.phase.offline")
        plan = build_cancel_decision_plan(other, "2020-01-01T00:00:00Z")
        decision = plan.decision.identity_mapping()
        decision["decision_digest"] = plan.decision.decision_digest
        columns = decisions._DEVELOPMENT_DECISION_COLUMNS
        with sqlite3.connect(location.database_path) as db:
            db.execute(f"INSERT INTO development_decisions ({', '.join(columns)}) "
                       f"VALUES ({', '.join('?' for _ in columns)})",
                       tuple(decision[name] for name in columns))
            binding = plan.bindings[0]
            bcols = DECISION_COLUMNS[DECISION_BINDING]
            db.execute(f"INSERT INTO {DECISION_BINDING} ({', '.join(bcols)}) "
                       f"VALUES ({', '.join('?' for _ in bcols)})", binding.values)
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as raised:
                writer._record_active_cancel_decision(command)
            assert raised.value.error_class == "database_integrity_failure"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (0,)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._recover_active_cancel_decision(command).status == "unresolved"


def test_ac06_populated_verifier_checks_original_decision_command(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        _, _, original, _ = _ready(location, command)
        mapping = original.to_mapping()
        mapping["decision_command_digest"] = "9" * 64
        stable = {key: value for key, value in mapping.items()
                  if key not in terminal_contracts._DERIVED + ("command_digest",)}
        for name in terminal_contracts._DERIVED:
            mapping[name] = terminal_contracts._digest(
                terminal_contracts.COMMAND_SCHEMA + "." + name + ".v1", stable)
        mapping["command_digest"] = terminal_contracts._digest(
            terminal_contracts.COMMAND_SCHEMA + ".identity",
            {key: value for key, value in mapping.items() if key != "command_digest"})
        contradictory = RecordRW0CancelPreEffectTerminalCommandV1(
            terminal_contracts._canonical(mapping))
        plan = build_cancel_terminal_plan(contradictory, "2020-01-01T00:00:00Z")
        with sqlite3.connect(location.database_path) as db:
            for row in plan.rows:
                columns = TERMINAL_COLUMNS[row.table]
                db.execute(f"INSERT INTO {row.table} ({', '.join(columns)}) "
                           f"VALUES ({', '.join('?' for _ in columns)})", row.values)
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
            with pytest.raises(ValueError):
                verify_terminal_anchor_families_0010(db)


def test_ac06_valid_populated_verifier_and_historical_replay(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        decision, _, terminal, _ = _ready(location, command)
        with acquire_sqlite_writer_session(location) as writer:
            terminal_committed = writer._record_cancel_pre_effect_block(terminal)
        with sqlite3.connect(location.database_path) as db:
            verify_terminal_anchor_families_0010(db)
            db.execute("UPDATE global_stop_current SET updated_at=?",
                       ("2098-01-01T00:00:00Z",))
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_active_cancel_decision(command) == decision
            assert writer._record_cancel_pre_effect_block(terminal) == terminal_committed
        with sqlite3.connect(location.database_path) as db:
            verify_terminal_anchor_families_0010(db)


def test_ac04_normal_winner_does_not_mask_other_phase_orphan_alias(monkeypatch):
    with prepared_cancel_case(monkeypatch, with_normal=True) as (
        location, command, normal_command, normal_source
    ):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_active_cancel_decision(command)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(normal_command, normal_source)
        mismatch = {
            "classification": "proven_coordinator_mismatch", "mismatch_class": "effect_head",
            "mismatch_ref": command.to_mapping()["target"]["effect_intent_ref"],
            "mismatch_digest": "1" * 64,
        }
        diagnostic = CancelCurrentnessV1(
            "proven_coordinator_mismatch", "effect_head", mismatch["mismatch_ref"],
            mismatch["mismatch_digest"], _canonical({"heads": {}}),
            _canonical({"stop": command.to_mapping()["stop"]}), _canonical(mismatch))
        proposed = RecordRW0CancelPreEffectTerminalCommandV1.prepare(
            mutation_ref="mutation.audit.alias", decision_command=command,
            committed=committed, verification=diagnostic)
        with sqlite3.connect(location.database_path) as db:
            pcols = c1_rows.PHASE_COLUMNS
            phase = dict(zip(pcols, db.execute(
                "SELECT " + ", ".join(pcols) + " FROM rw0_phase_instances"
            ).fetchone(), strict=True))
            phase.update(phase_basis_ref="phase.audit.other", phase_basis_digest="1" * 64,
                         k8_digest="2" * 64,
                         establishment_mutation_ref="mutation.audit.other")
            target = _row(db, "development_effect_intents", "effect_class=?",
                          ("validate_candidate",))
            fence = _row(db, "development_effect_fences", "effect_intent_ref=?",
                         (target["effect_intent_ref"],))
            delivery = _row(db, "development_delivery_attempts", "effect_intent_ref=?",
                            (target["effect_intent_ref"],))
            effect_head = _row(db, "development_effect_heads", "effect_intent_ref=?",
                               (target["effect_intent_ref"],))
            delivery_head = _row(db, "development_delivery_heads", "effect_intent_ref=?",
                                 (target["effect_intent_ref"],))
            phase.update(
                effect_intent_ref=target["effect_intent_ref"],
                effect_intent_digest=target["effect_intent_digest"],
                effect_fence_ref=fence["effect_fence_ref"],
                effect_fence_digest=fence["effect_fence_digest"],
                effect_authorization_ref=fence["effect_authorization_ref"],
                effect_authorization_digest=fence["effect_authorization_digest"],
                delivery_attempt_ref=delivery["delivery_attempt_ref"],
                delivery_envelope_digest=delivery["delivery_envelope_digest"],
                delivery_attempt_digest=delivery["delivery_attempt_digest"],
                current_effect_head_revision=effect_head["head_revision"],
                current_effect_head_state=effect_head["effect_state"],
                current_effect_head_digest=effect_head["head_digest"],
                current_effect_head_fence_ref=effect_head["current_effect_fence_ref"],
                current_effect_head_cancellation_effect_intent_ref=effect_head["cancellation_effect_intent_ref"],
                current_effect_head_updated_at=effect_head["updated_at"],
                current_delivery_head_revision=delivery_head["head_revision"],
                current_delivery_head_state=delivery_head["delivery_state"],
                current_delivery_head_digest=delivery_head["head_digest"],
                current_delivery_head_attempt_ref=delivery_head["current_delivery_attempt_ref"],
                current_delivery_head_updated_at=delivery_head["updated_at"],
            )
            phase["phase_row_digest"] = c1_rows.row_digest(
                phase["schema_id"], {key: phase[key] for key in pcols if key != "phase_row_digest"})
            c1_rows.rw0_c1_row_value_from_mapping("rw0_phase_instances", phase)
            db.execute(f"INSERT INTO rw0_phase_instances ({', '.join(pcols)}) "
                       f"VALUES ({', '.join('?' for _ in pcols)})",
                       tuple(phase[key] for key in pcols))
            row = terminal_plan.build_cancel_terminal_plan(proposed, "2020-01-01T00:00:00Z").rows[0]
            context = row.mapping
            context["phase_basis_ref"] = phase["phase_basis_ref"]
            context["phase_basis_digest"] = phase["phase_basis_digest"]
            context["context_digest"] = terminal_contracts._digest(
                terminal_plan.SCHEMAS[row.table] + ".identity",
                {key: value.hex() if type(value) is bytes else value
                 for key, value in context.items() if key != "context_digest"})
            columns = TERMINAL_COLUMNS[row.table]
            db.execute(f"INSERT INTO {row.table} ({', '.join(columns)}) "
                       f"VALUES ({', '.join('?' for _ in columns)})",
                       tuple(context[key] for key in columns))
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as raised:
                writer._read_cancel_pre_effect_block(proposed)
            assert raised.value.error_class == "database_integrity_failure"
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_cancel_pre_effect_block(proposed)
            assert writer._recover_cancel_pre_effect_block(proposed).status == "unresolved"
