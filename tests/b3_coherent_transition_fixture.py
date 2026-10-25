"""Tests-only synthetic B3 coherent transition fixture graph.

This module is not admission, not authorization, not production state initialization,
and not runtime authority. It directly seeds a historical schema-0001 B3/B4 graph
inside a temporary current-generation managed SQLite database, then validates the
seeded rows through existing Coordinator row contracts. The cumulative physical
schema is generation 2 / migration 0005; the seeded graph's meanings remain the
existing schema-0001 meanings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
from types import TracebackType
from typing import Any, Mapping

from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, BACKLOG_SCHEMA_VERSION, FiniteBacklog, WorkItem
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256
from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.lease import (
    AUTHORIZATION_DECISION_SCHEMA_ID,
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    LeaseIdentityValidation,
    LeaseRevocationState,
    Permission,
    StandingLease,
    UnsupportedAuthorizationProvider,
    derive_lease_runtime_decision,
)
from ge_nwp_coordinator.persistence_contracts import (
    ADMITTED_BACKLOG_ROW_COLUMNS,
    AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    DEPENDENCY_RECEIPT_ROW_COLUMNS,
    LEASE_IDENTITY_RECORD_ROW_COLUMNS,
    TRANSITION_EVENT_ROW_COLUMNS,
    WORK_ITEM_ROW_COLUMNS,
    AdmittedBacklogRecordEnvelope,
    AuthorizationReceiptEnvelope,
    DependencyReceiptEnvelope,
    GlobalStopCurrentRecordEnvelope,
    LeaseIdentityRecordEnvelope,
    TransitionEventRecordEnvelope,
    WorkItemRecordEnvelope,
    admitted_backlog_record_envelope_from_row,
    authorization_receipt_envelope_from_row,
    dependency_receipt_envelope_from_row,
    encode_sqlite_boolean,
    lease_identity_record_envelope_from_row,
    match_transition_event_idempotency,
    transition_event_record_envelope_from_row,
    work_item_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import DatabaseClassification, initialize_database, validate_database
from ge_nwp_coordinator.sqlite_transition_read_scope import (
    _read_admitted_backlog,
    _read_authorization_receipt,
    _read_current_work_item,
    _read_dependency_receipt,
    _read_global_stop_current,
    _read_lease_identity_record,
)
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_machine import (
    DEPENDENCY_DECISION_SCHEMA_ID,
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluationKind,
    TransitionEvent,
    WorkItemRecord,
    WorkItemState,
    evaluate_transition,
)
from ge_nwp_coordinator.state_store import CommittedTransition, SafeWriterMetadata, WriterSession

FIXTURE_TIMESTAMP = "2026-07-14T00:00:03Z"
_LEASE_ID = "lease-b3-fixture"
_BACKLOG_ID = "backlog-b3-fixture"
_WORK_ITEM_ID = "wi-b3-fixture"
_DEPENDENCY_DECISION_REF = "deps-b3-fixture-ready"
_CURRENT_PHYSICAL_SEQUENCE = 5
_CURRENT_PHYSICAL_MIGRATION_ID = "0005_section41_post_execution_proposal_family"
_FIXTURE_WRITER_GENERATION = 2
_C2B2_PHYSICAL_TABLES = (
    "development_program_heads",
    "development_program_versions",
    "development_accepted_intent_revisions",
    "development_work_item_heads",
    "development_work_item_revisions",
    "development_program_version_work_items",
    "development_revision_edges",
    "development_work_spec_bindings",
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_authority_evaluations",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
    "development_decisions",
    "development_mutation_receipts",
)
_SECTION41_PHYSICAL_TABLES = (
    "development_model_source_invocations",
    "development_pre_execution_planning_contexts",
    "development_private_proposal_artifact_bindings",
    "development_model_proposals",
    "development_pre_execution_plan_projections",
    "development_model_proposal_evidence_bindings",
    "development_pre_execution_dispositions",
    "development_pre_execution_selection_heads",
    "development_cognitive_mutation_receipts",
)
_RW0_C1_PHYSICAL_TABLES = (
    "rw0_phase_instances",
    "rw0_evidence_values",
    "rw0_evidence_memberships",
    "rw0_relation_bindings",
    "rw0_relation_operands",
    "rw0_c1_mutation_receipts",
    "rw0_authority_verification_observations",
    "rw0_subordinate_authorization_proposals",
    "rw0_custody_availability_observations",
    "rw0_retrieval_capability_event_observations",
    "rw0_remote_host_readiness_observations",
    "rw0_effect_host_qualifications",
    "rw0_worker_mechanism_capability_declarations",
    "rw0_worker_mechanism_capability_observations",
    "rw0_worker_mechanism_capability_qualifications",
    "rw0_wire_cancellation_request_observations",
    "rw0_wire_process_observations",
    "rw0_c2a_worker_observations",
    "rw0_wire_worker_result_bindings",
    "rw0_wire_process_result_classification_bindings",
    "rw0_section41_post_execution_proposal_family_members",
    "rw0_authority_observation_effect_classes",
    "rw0_c2a_worker_observation_evidence_refs",
)
_FIXTURE_EMPTY_PHYSICAL_TABLES = (
    *_C2B2_PHYSICAL_TABLES,
    *_SECTION41_PHYSICAL_TABLES,
    *_RW0_C1_PHYSICAL_TABLES,
)
if not (
    len(_C2B2_PHYSICAL_TABLES) == 19
    and len(_SECTION41_PHYSICAL_TABLES) == 9
    and len(_RW0_C1_PHYSICAL_TABLES) == 23
    and not set(_C2B2_PHYSICAL_TABLES).intersection(_SECTION41_PHYSICAL_TABLES)
    and not set(_C2B2_PHYSICAL_TABLES).intersection(_RW0_C1_PHYSICAL_TABLES)
    and not set(_SECTION41_PHYSICAL_TABLES).intersection(_RW0_C1_PHYSICAL_TABLES)
    and len(_FIXTURE_EMPTY_PHYSICAL_TABLES)
    == len(set(_FIXTURE_EMPTY_PHYSICAL_TABLES))
    == 51
):
    raise RuntimeError("fixture-physical-table-inventory-invalid")


class BlockedFixtureAuthorityContract(RuntimeError):
    """Tests-only stop condition for an impossible coherent fixture graph."""

    def __init__(self) -> None:
        super().__init__("blocked-fixture-authority-contract")


@dataclass(frozen=True)
class CoherentTransitionFixture:
    """Context-managed tests-only fixture; not a production authority object."""

    location: CoordinatorStateLocation = field(repr=False)
    writer_session: WriterSession = field(repr=False)
    metadata: SafeWriterMetadata
    lease: StandingLease = field(repr=False)
    lease_identity_validation: LeaseIdentityValidation = field(repr=False)
    authorization: AuthorizationDecision = field(repr=False)
    backlog: FiniteBacklog = field(repr=False)
    work_item: WorkItemRecord = field(repr=False)
    dependency_decision: DependencyDecision | None = field(repr=False)
    global_stop: GlobalStopState = field(repr=False)
    command: TransitionCommand = field(repr=False)
    transition_event_envelope: TransitionEventRecordEnvelope | None = field(repr=False)

    def __enter__(self) -> "CoherentTransitionFixture":
        if not self.writer_session.active:
            raise RuntimeError("fixture-writer-session-closed")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.writer_session.close()


@dataclass(frozen=True)
class CoherentTransitionReadBack:
    """Tests-only readback envelopes; no connection or raw rows retained."""

    work_item: WorkItemRecordEnvelope = field(repr=False)
    lease_identity: LeaseIdentityRecordEnvelope = field(repr=False)
    authorization: AuthorizationReceiptEnvelope = field(repr=False)
    dependency: DependencyReceiptEnvelope | None = field(repr=False)
    admitted_backlog: AdmittedBacklogRecordEnvelope = field(repr=False)
    global_stop: GlobalStopCurrentRecordEnvelope = field(repr=False)


class _TestsOnlyTransitionReadCapabilityEpoch:
    """Tests-only active-transaction epoch, not production capability authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._active = False
        self._generation = 0

    def start_for_test(self) -> "_TestsOnlyTransitionReadCapability":
        self._generation += 1
        self._active = True
        return _TestsOnlyTransitionReadCapability(self, self._generation)

    def end_for_test(self) -> None:
        self._active = False

    def _connection_for_generation(self, generation: int) -> sqlite3.Connection:
        if not self._active or generation != self._generation:
            raise RuntimeError("transition-read-capability-expired-for-test")
        return self._connection


class _TestsOnlyTransitionReadCapability:
    """Clearly tests-only structural stand-in for the private B3b2b readers."""

    def __init__(self, epoch: _TestsOnlyTransitionReadCapabilityEpoch, generation: int) -> None:
        self._epoch = epoch
        self._generation = generation

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        return self._epoch._connection_for_generation(self._generation)


def make_coherent_transition_fixture_for_test(
    tmp_path: Path,
    *,
    ready_dependency: bool = False,
    existing_event: bool = False,
    dependencies_satisfied: bool = True,
) -> CoherentTransitionFixture:
    """Create one temporary managed SQLite graph by direct tests-only seeding.

    The setup transaction is not the future B3c transaction path: it performs
    no writer fencing, context assembly, evaluator integration, admission, or
    production mutation.
    """

    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "b3-coherent-transition-fixture-state")
    inspection = initialize_database(location)
    if (
        inspection.classification is not DatabaseClassification.MANAGED
        or inspection.current_sequence != _CURRENT_PHYSICAL_SEQUENCE
        or inspection.current_sequence != inspection.latest_sequence
        or inspection.current_migration_id != _CURRENT_PHYSICAL_MIGRATION_ID
    ):
        raise RuntimeError("fixture-managed-generation-2-schema-required")

    graph = _build_graph_for_test(
        ready_dependency=ready_dependency,
        existing_event=existing_event,
        dependencies_satisfied=dependencies_satisfied,
    )
    _seed_graph_for_test(location, graph)
    _require_current_physical_schema_for_test(location)
    _require_c2b2_physical_tables_empty_for_test(location)
    _require_section41_physical_tables_empty_for_test(location)
    _require_rw0_c1_physical_tables_empty_for_test(location)

    first_writer_session = acquire_sqlite_writer_session(location)
    try:
        if first_writer_session.metadata.generation != 1:
            raise RuntimeError("fixture-initial-writer-generation-1-required")
    finally:
        first_writer_session.close()

    writer_session = acquire_sqlite_writer_session(location)
    try:
        metadata = writer_session.metadata
        if metadata.generation != _FIXTURE_WRITER_GENERATION:
            raise RuntimeError("fixture-writer-generation-2-required")
        _require_current_physical_schema_for_test(location)
        _require_c2b2_physical_tables_empty_for_test(location)
        _require_section41_physical_tables_empty_for_test(location)
        _require_rw0_c1_physical_tables_empty_for_test(location)
        return CoherentTransitionFixture(
            location=location,
            writer_session=writer_session,
            metadata=metadata,
            lease=graph.lease,
            lease_identity_validation=graph.lease_identity_validation,
            authorization=graph.authorization,
            backlog=graph.backlog,
            work_item=graph.work_item,
            dependency_decision=graph.dependency_decision,
            global_stop=graph.global_stop,
            command=graph.command,
            transition_event_envelope=graph.transition_event_envelope,
        )
    except Exception:
        writer_session.close()
        raise


def read_back_fixture_for_test(fixture: CoherentTransitionFixture) -> CoherentTransitionReadBack:
    """Read fixture rows through B3b2b readers in one tests-only transaction."""

    connection = open_existing_sqlite_connection(fixture.location, read_only=False)
    epoch = _TestsOnlyTransitionReadCapabilityEpoch(connection)
    try:
        connection.execute("BEGIN IMMEDIATE")
        capability = epoch.start_for_test()
        try:
            work_item = _read_current_work_item(capability, fixture.work_item.work_item_id)
            lease_identity = _read_lease_identity_record(
                capability,
                fixture.lease_identity_validation.decision_ref,
            )
            authorization = _read_authorization_receipt(capability, fixture.authorization.decision_ref)
            dependency = (
                _read_dependency_receipt(capability, fixture.dependency_decision.decision_ref)
                if fixture.dependency_decision is not None
                else None
            )
            admitted_backlog = _read_admitted_backlog(capability, fixture.backlog.backlog_id)
            global_stop = _read_global_stop_current(capability)
            if work_item is None or lease_identity is None or authorization is None or admitted_backlog is None:
                raise SQLiteMutationStoreError("database_integrity_failure")
            return CoherentTransitionReadBack(
                work_item=work_item,
                lease_identity=lease_identity,
                authorization=authorization,
                dependency=dependency,
                admitted_backlog=admitted_backlog,
                global_stop=global_stop,
            )
        finally:
            epoch.end_for_test()
            _rollback_for_test(connection)
    finally:
        connection.close()


def exact_replay_for_test(fixture: CoherentTransitionFixture) -> CommittedTransition:
    envelope = fixture.transition_event_envelope
    if envelope is None:
        raise RuntimeError("fixture-transition-event-required")
    replay = match_transition_event_idempotency(envelope, fixture.command)
    if not isinstance(replay, CommittedTransition):
        raise RuntimeError("fixture-exact-replay-required")
    return replay


def transition_event_count_for_test(fixture: CoherentTransitionFixture) -> int:
    return _table_count_for_test(fixture.location, "transition_events")


def dependency_receipt_count_for_test(fixture: CoherentTransitionFixture) -> int:
    return _table_count_for_test(fixture.location, "dependency_decision_receipts")


def global_stop_event_count_for_test(fixture: CoherentTransitionFixture) -> int:
    return _table_count_for_test(fixture.location, "global_stop_events")


def authorization_receipt_rows_for_test(fixture: CoherentTransitionFixture) -> tuple[tuple[str, int, int], ...]:
    connection = open_existing_sqlite_connection(fixture.location, read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT authorization_model, authorized, executable
            FROM authorization_decision_receipts
            ORDER BY decision_ref
            """
        ).fetchall()
        return tuple((str(row[0]), int(row[1]), int(row[2])) for row in rows)
    finally:
        connection.close()


def _replace_work_item_lease_for_test(
    fixture: CoherentTransitionFixture,
    *,
    replacement_lease_id: str = "lease-b3-fixture-other",
) -> None:
    connection = open_existing_sqlite_connection(fixture.location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            UPDATE work_items
            SET lease_id = ?
            WHERE work_item_id = ?
            """,
            (replacement_lease_id, fixture.work_item.work_item_id),
        )
        connection.execute("COMMIT")
    except Exception:
        _rollback_for_test(connection)
        raise
    finally:
        connection.close()


def _replace_work_item_budget_limit_for_test(
    fixture: CoherentTransitionFixture,
    *,
    budget_limit: int = 1,
) -> None:
    connection = open_existing_sqlite_connection(fixture.location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            UPDATE work_items
            SET budget_limit = ?
            WHERE work_item_id = ?
            """,
            (budget_limit, fixture.work_item.work_item_id),
        )
        connection.execute("COMMIT")
    except Exception:
        _rollback_for_test(connection)
        raise
    finally:
        connection.close()


@dataclass(frozen=True)
class _GraphForTest:
    lease: StandingLease = field(repr=False)
    lease_identity_validation: LeaseIdentityValidation = field(repr=False)
    authorization: AuthorizationDecision = field(repr=False)
    backlog: FiniteBacklog = field(repr=False)
    work_item: WorkItemRecord = field(repr=False)
    dependency_decision: DependencyDecision | None = field(repr=False)
    global_stop: GlobalStopState = field(repr=False)
    command: TransitionCommand = field(repr=False)
    transition_event_envelope: TransitionEventRecordEnvelope | None = field(repr=False)
    transition_event_row: Mapping[str, object] | None = field(repr=False)


def _build_graph_for_test(
    *,
    ready_dependency: bool,
    existing_event: bool,
    dependencies_satisfied: bool,
) -> _GraphForTest:
    backlog = _backlog_for_test()
    lease = _lease_for_test(backlog)
    lease_identity_validation = lease.validate_identity()
    if not lease_identity_validation.identity_valid:
        raise RuntimeError("fixture-valid-lease-identity-required")
    authorization = UnsupportedAuthorizationProvider().authorize(lease)
    dependency_decision = _dependency_decision_for_test(dependencies_satisfied) if ready_dependency else None
    work_item = _work_item_record_for_test(ready_dependency=ready_dependency)
    global_stop = GlobalStopState()
    command = _transition_command_for_test(
        work_item=work_item,
        lease_identity_validation=lease_identity_validation,
        authorization=authorization,
        global_stop=global_stop,
        dependency_decision=dependency_decision,
        ready_dependency=ready_dependency,
    )
    transition_event_envelope: TransitionEventRecordEnvelope | None = None
    transition_event_row: Mapping[str, object] | None = None
    if existing_event:
        transition_event_row, transition_event_envelope = _domain_rejected_event_row_for_test(
            lease=lease,
            lease_identity_validation=lease_identity_validation,
            authorization=authorization,
            global_stop=global_stop,
            dependency_decision=dependency_decision,
            work_item=work_item,
            command=command,
        )
    return _GraphForTest(
        lease=lease,
        lease_identity_validation=lease_identity_validation,
        authorization=authorization,
        backlog=backlog,
        work_item=work_item,
        dependency_decision=dependency_decision,
        global_stop=global_stop,
        command=command,
        transition_event_envelope=transition_event_envelope,
        transition_event_row=transition_event_row,
    )


def _item_for_test() -> WorkItem:
    return WorkItem(
        work_item_id=_WORK_ITEM_ID,
        objective_label="b3 fixture objective",
        opaque_private_assignment_ref="assignment-b3-fixture",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src", "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": 2, "compute_seconds": 10},
        dependencies=(),
        stop_conditions=("global-stop",),
    )


def _backlog_for_test() -> FiniteBacklog:
    return FiniteBacklog(
        schema_id=BACKLOG_SCHEMA_ID,
        schema_version=BACKLOG_SCHEMA_VERSION,
        backlog_id=_BACKLOG_ID,
        lease_reference=_LEASE_ID,
        work_items=(_item_for_test(),),
        content_digest="0" * 64,
    ).with_digest()


def _lease_for_test(backlog: FiniteBacklog) -> StandingLease:
    return StandingLease(
        schema_id=LEASE_SCHEMA_ID,
        schema_version=1,
        lease_id=_LEASE_ID,
        issuer_label="operator-policy",
        issued_at="2026-07-14T00:00:00Z",
        valid_from="2026-07-14T00:00:01Z",
        expires_at="2026-07-15T00:00:00Z",
        revocation_state=LeaseRevocationState.NOT_REVOKED,
        revocation_reference=None,
        subject="nwp-coordinator-p1",
        repo_identity={"component": "nwp-coordinator", "repo_label": "coordinator-local"},
        branch_policy={"base": "trunk_dev", "mode": "operator-approved"},
        allowed_paths=("src", "tests"),
        forbidden_path_policy_identity="governed-execution.nwp-forbidden-paths.v1",
        task_classes=("code",),
        risk_lanes=("low",),
        finite_backlog_reference=backlog.backlog_id,
        finite_backlog_digest=backlog.content_digest,
        max_work_items=1,
        max_concurrency=1,
        max_attempts=2,
        max_repairs=1,
        compute_api_budget={"api_calls": 5, "compute_seconds": 30},
        wall_clock_budget_seconds=3600,
        validation_requirements=("unit-tests",),
        audit_requirements=("boundary-audit",),
        local_commit_permission=Permission.FORBIDDEN,
        publication_permission=Permission.FORBIDDEN,
        cross_repo_permission=Permission.FORBIDDEN,
        maintenance_permission=Permission.FORBIDDEN,
        cleanup_requirements=("no-worker-artifacts",),
        reporting_cadence="on-transition",
        retention_policy="safe-projections-only",
        global_stop_reference="operator-global-stop",
        canonical_digest_metadata={"algorithm": "sha256", "canonicalization": CANONICALIZATION_ID},
        authorization_mechanism={"kind": "unsupported", "descriptor": "p1-fail-closed"},
    ).with_digest()


def _dependency_decision_for_test(dependencies_satisfied: bool) -> DependencyDecision:
    return DependencyDecision(
        decision_ref=_DEPENDENCY_DECISION_REF,
        work_item_id=_WORK_ITEM_ID,
        dependencies_satisfied=dependencies_satisfied,
        reason="accepted" if dependencies_satisfied else "dependencies_not_satisfied",
    )


def _work_item_record_for_test(*, ready_dependency: bool) -> WorkItemRecord:
    return WorkItemRecord(
        schema_id=WORK_ITEM_STATE_SCHEMA_ID,
        work_item_id=_WORK_ITEM_ID,
        lease_id=_LEASE_ID,
        backlog_id=_BACKLOG_ID,
        state=WorkItemState.LEASE_ADMITTED if ready_dependency else WorkItemState.PROPOSED,
        version=1 if ready_dependency else 0,
        attempt_count=0,
        repair_count=0,
        budget_consumed=0,
        budget_limit=0,
        max_attempts=2,
        max_repairs=1,
        cleanup_required=False,
    )


def _transition_command_for_test(
    *,
    work_item: WorkItemRecord,
    lease_identity_validation: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
    global_stop: GlobalStopState,
    dependency_decision: DependencyDecision | None,
    ready_dependency: bool,
) -> TransitionCommand:
    target_state = WorkItemState.READY if ready_dependency else WorkItemState.LEASE_ADMITTED
    return TransitionCommand.create(
        work_item_id=work_item.work_item_id,
        idempotency_key="transition-b3-fixture-k1",
        expected_version=work_item.version,
        target_state=target_state,
        lease_identity_decision_ref=lease_identity_validation.decision_ref,
        authorization_decision_ref=authorization.decision_ref,
        global_stop_ref=global_stop.stop_ref,
        global_stop_version=global_stop.version,
        dependency_decision_ref=dependency_decision.decision_ref if ready_dependency else None,
        evidence_refs=(),
        budget_cost=0,
    )


def _domain_rejected_event_row_for_test(
    *,
    lease: StandingLease,
    lease_identity_validation: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
    global_stop: GlobalStopState,
    dependency_decision: DependencyDecision | None,
    work_item: WorkItemRecord,
    command: TransitionCommand,
) -> tuple[Mapping[str, object], TransitionEventRecordEnvelope]:
    context_dependency = dependency_decision if dependency_decision is not None else DependencyDecision()
    context = TransitionContext(
        lease_identity=lease_identity_validation,
        authorization=authorization,
        lease_runtime=derive_lease_runtime_decision(lease, FIXTURE_TIMESTAMP),
        global_stop=global_stop,
        dependency_decision=context_dependency,
    )
    evaluation = evaluate_transition(work_item, command, context)
    if evaluation.kind is not TransitionEvaluationKind.DOMAIN_REJECTED or evaluation.event is None:
        raise BlockedFixtureAuthorityContract()
    event = evaluation.event
    row = _transition_event_row_for_test(event, evaluation.record, event_sequence=0)
    return row, transition_event_record_envelope_from_row(row)


def _seed_graph_for_test(location: CoordinatorStateLocation, graph: _GraphForTest) -> None:
    connection = open_existing_sqlite_connection(location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _insert_row_for_test(
            connection,
            "lease_identity_records",
            LEASE_IDENTITY_RECORD_ROW_COLUMNS,
            _lease_identity_row_for_test(graph.lease),
        )
        _insert_row_for_test(
            connection,
            "admitted_backlogs",
            ADMITTED_BACKLOG_ROW_COLUMNS,
            _admitted_backlog_row_for_test(graph.backlog),
        )
        _insert_row_for_test(
            connection,
            "authorization_decision_receipts",
            AUTHORIZATION_RECEIPT_ROW_COLUMNS,
            _authorization_row_for_test(graph.authorization),
        )
        if graph.dependency_decision is not None:
            _insert_row_for_test(
                connection,
                "dependency_decision_receipts",
                DEPENDENCY_RECEIPT_ROW_COLUMNS,
                _dependency_row_for_test(graph.dependency_decision),
            )
        _insert_row_for_test(
            connection,
            "work_items",
            WORK_ITEM_ROW_COLUMNS,
            _work_item_row_for_test(graph.work_item),
        )
        if graph.transition_event_row is not None:
            _insert_row_for_test(
                connection,
                "transition_events",
                TRANSITION_EVENT_ROW_COLUMNS,
                graph.transition_event_row,
            )
        connection.execute("COMMIT")
    except Exception:
        _rollback_for_test(connection)
        raise
    finally:
        connection.close()


def _lease_identity_row_for_test(lease: StandingLease) -> Mapping[str, object]:
    validation = lease.validate_identity()
    row = _ordered_row_for_test(
        LEASE_IDENTITY_RECORD_ROW_COLUMNS,
        {
            "decision_ref": validation.decision_ref,
            "lease_ref": validation.lease_ref,
            "identity_valid": encode_sqlite_boolean(validation.identity_valid, "lease_identity_record.identity_valid"),
            "lease_digest": validation.digest,
            "schema_id": LEASE_SCHEMA_ID,
            "canonical_json": canonical_json_bytes(lease.to_dict()).decode("utf-8"),
            "canonical_digest": canonical_sha256(lease.to_dict()),
            "created_at": FIXTURE_TIMESTAMP,
        },
    )
    lease_identity_record_envelope_from_row(row)
    return row


def _authorization_row_for_test(decision: AuthorizationDecision) -> Mapping[str, object]:
    row = _ordered_row_for_test(
        AUTHORIZATION_RECEIPT_ROW_COLUMNS,
        {
            "decision_ref": decision.decision_ref,
            "lease_ref": decision.lease_ref,
            "lease_identity_decision_ref": decision.lease_identity_decision_ref,
            "lease_identity_valid": encode_sqlite_boolean(
                decision.lease_identity_valid,
                "authorization_receipt.lease_identity_valid",
            ),
            "authorization_model": decision.authorization_model.value,
            "authorized": encode_sqlite_boolean(decision.authorized, "authorization_receipt.authorized"),
            "executable": encode_sqlite_boolean(decision.executable, "authorization_receipt.executable"),
            "reason": decision.reason,
            "schema_id": AUTHORIZATION_DECISION_SCHEMA_ID,
            "canonical_json": decision.canonical_json(),
            "canonical_digest": decision.canonical_digest(),
            "created_at": FIXTURE_TIMESTAMP,
        },
    )
    authorization_receipt_envelope_from_row(row)
    return row


def _dependency_row_for_test(decision: DependencyDecision) -> Mapping[str, object]:
    row = _ordered_row_for_test(
        DEPENDENCY_RECEIPT_ROW_COLUMNS,
        {
            "decision_ref": decision.decision_ref,
            "work_item_id": decision.work_item_id,
            "dependencies_satisfied": encode_sqlite_boolean(
                decision.dependencies_satisfied,
                "dependency_receipt.dependencies_satisfied",
            ),
            "reason": decision.reason,
            "schema_id": DEPENDENCY_DECISION_SCHEMA_ID,
            "canonical_json": decision.canonical_json(),
            "canonical_digest": decision.canonical_digest(),
            "created_at": FIXTURE_TIMESTAMP,
        },
    )
    dependency_receipt_envelope_from_row(row)
    return row


def _admitted_backlog_row_for_test(backlog: FiniteBacklog) -> Mapping[str, object]:
    row = _ordered_row_for_test(
        ADMITTED_BACKLOG_ROW_COLUMNS,
        {
            "backlog_id": backlog.backlog_id,
            "lease_ref": backlog.lease_reference,
            "schema_id": backlog.schema_id,
            "schema_version": backlog.schema_version,
            "content_digest": backlog.content_digest,
            "canonical_json": canonical_json_bytes(backlog.to_dict()).decode("utf-8"),
            "admitted_at": FIXTURE_TIMESTAMP,
        },
    )
    admitted_backlog_record_envelope_from_row(row)
    return row


def _work_item_row_for_test(record: WorkItemRecord) -> Mapping[str, object]:
    row = _ordered_row_for_test(
        WORK_ITEM_ROW_COLUMNS,
        {
            **record.to_dict(),
            "state": record.state.value,
            "cleanup_required": encode_sqlite_boolean(record.cleanup_required, "work_item_row.cleanup_required"),
            "updated_at": FIXTURE_TIMESTAMP,
        },
    )
    work_item_record_envelope_from_row(row)
    return row


def _transition_event_row_for_test(
    event: TransitionEvent,
    replay_record: WorkItemRecord,
    *,
    event_sequence: int,
) -> Mapping[str, object]:
    row = _ordered_row_for_test(
        TRANSITION_EVENT_ROW_COLUMNS,
        {
            "event_ref": event.event_ref,
            "event_sequence": event_sequence,
            "work_item_id": event.work_item_id,
            "lease_id": event.lease_id,
            "idempotency_key": event.idempotency_key,
            "command_digest": event.command_digest,
            "source_state": event.source_state.value,
            "source_version": event.source_version,
            "resulting_state": event.resulting_state.value,
            "resulting_version": event.resulting_version,
            "outcome": event.outcome.value,
            "reason": event.reason,
            "evidence_refs_json": canonical_json_bytes(list(event.evidence_refs)).decode("utf-8"),
            "budget_cost_delta": event.budget_cost_delta,
            "attempt_count_delta": event.attempt_count_delta,
            "repair_count_delta": event.repair_count_delta,
            "lease_identity_decision_ref": event.lease_identity_decision_ref,
            "authorization_decision_ref": event.authorization_decision_ref,
            "dependency_decision_ref": event.dependency_decision_ref,
            "global_stop_ref": event.global_stop_ref,
            "global_stop_version": event.global_stop_version,
            "schema_id": event.schema_id,
            "event_json": event.canonical_json(),
            "event_digest": event.canonical_digest(),
            "replay_work_item_json": replay_record.canonical_json(),
            "replay_work_item_digest": replay_record.canonical_digest(),
            "created_at": event.lease_runtime.evaluated_at,
        },
    )
    transition_event_record_envelope_from_row(row)
    return row


def _ordered_row_for_test(columns: tuple[str, ...], values: Mapping[str, object]) -> Mapping[str, object]:
    return {column: values[column] for column in columns}


def _insert_row_for_test(
    connection: sqlite3.Connection,
    table_name: str,
    columns: tuple[str, ...],
    row: Mapping[str, object],
) -> None:
    columns_sql = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})",
        tuple(row[column] for column in columns),
    )


def _require_current_physical_schema_for_test(location: CoordinatorStateLocation) -> None:
    inspection = validate_database(location)
    if (
        inspection.classification is not DatabaseClassification.MANAGED
        or inspection.current_sequence != _CURRENT_PHYSICAL_SEQUENCE
        or inspection.current_sequence != inspection.latest_sequence
        or inspection.current_migration_id != _CURRENT_PHYSICAL_MIGRATION_ID
    ):
        raise RuntimeError("fixture-managed-generation-2-schema-required")


def _require_c2b2_physical_tables_empty_for_test(location: CoordinatorStateLocation) -> None:
    connection = open_existing_sqlite_connection(location, read_only=True)
    try:
        for table_name in _C2B2_PHYSICAL_TABLES:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            if row != (0,):
                raise RuntimeError("fixture-c2b2-physical-table-not-empty")
    finally:
        connection.close()


def _require_section41_physical_tables_empty_for_test(
    location: CoordinatorStateLocation,
) -> None:
    connection = open_existing_sqlite_connection(location, read_only=True)
    try:
        for table_name in _SECTION41_PHYSICAL_TABLES:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            if row != (0,):
                raise RuntimeError("fixture-section41-physical-table-not-empty")
    finally:
        connection.close()


def _require_rw0_c1_physical_tables_empty_for_test(
    location: CoordinatorStateLocation,
) -> None:
    connection = open_existing_sqlite_connection(location, read_only=True)
    try:
        for table_name in _RW0_C1_PHYSICAL_TABLES:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            if row != (0,):
                raise RuntimeError("fixture-rw0-c1-physical-table-not-empty")
    finally:
        connection.close()


def _table_count_for_test(location: CoordinatorStateLocation, table_name: str) -> int:
    connection = open_existing_sqlite_connection(location, read_only=True)
    try:
        row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        if row is None:
            raise RuntimeError("fixture-count-required")
        return int(row[0])
    finally:
        connection.close()


def _rollback_for_test(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass
