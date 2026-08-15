from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import inspect
from pathlib import Path
import traceback

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_transition_dry_run_contracts as dry_run_contracts
from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, FiniteBacklog, WorkItem
from ge_nwp_coordinator.global_stop import GlobalStopReasonClass, GlobalStopState
from ge_nwp_coordinator.lease import (
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    AuthorizationDecision,
    AuthorizationModel,
    LeaseIdentityValidation,
    LeaseRuntimeDecision,
    LeaseRuntimeStatus,
    LeaseRevocationState,
    Permission,
    StandingLease,
    derive_lease_runtime_decision,
)
from ge_nwp_coordinator.models import ValidationIssue
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import (
    _bind_b3c3_transition_authority,
    _BoundTransitionAuthority,
    _require_initialized_authorization,
    _require_initialized_committed_transition,
    _require_initialized_dependency,
    _require_initialized_finite_backlog,
    _require_initialized_global_stop,
    _require_initialized_lease_identity,
    _require_initialized_lease_runtime,
    _require_initialized_standing_lease,
    _require_initialized_transition_command,
    _require_initialized_transition_conflict,
    _require_initialized_transition_event,
    _require_initialized_transition_evaluation,
    _require_initialized_validation_issue,
    _require_initialized_work_item,
    _require_initialized_work_item_record,
    _RollbackOnlyTransitionDryRunResult,
    _RollbackOnlyTransitionDryRunResultKind,
    _TransitionDryRunPreflightError,
    _TransitionDryRunPreflightFailureReason,
    _validate_transition_dry_run_preflight,
)
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator.state_machine import (
    DependencyDecision,
    TransitionCommand,
    TransitionContext,
    TransitionEvaluation,
    TransitionEvaluationKind,
    TransitionEvent,
    WorkItemRecord,
    WorkItemState,
    evaluate_transition,
)
from ge_nwp_coordinator.state_store import CommittedTransition, TransitionConflict, WriterSessionFailureReason


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
DRY_RUN_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_dry_run_contracts.py"
TRANSACTION_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_transaction.py"
EXPECTED_MIGRATION_0001_CHECKSUM = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
PRIVATE_SENTINEL = "synthetic-private-sentinel"


def _item(work_item_id: str = "wi-1", *, dependencies: tuple[str, ...] = ()) -> WorkItem:
    return WorkItem(
        work_item_id=work_item_id,
        objective_label=f"{work_item_id} objective",
        opaque_private_assignment_ref=f"private-ref-{work_item_id}",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src", "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": 0, "compute_seconds": 0},
        dependencies=dependencies,
        stop_conditions=("global-stop",),
    )


def _backlog(*, items: tuple[WorkItem, ...] | None = None, lease_reference: str = "lease-a2-p1") -> FiniteBacklog:
    backlog = FiniteBacklog(
        schema_id=BACKLOG_SCHEMA_ID,
        schema_version=1,
        backlog_id="backlog-a2-p1",
        lease_reference=lease_reference,
        work_items=items or (_item(),),
        content_digest="0" * 64,
    )
    return backlog.with_digest()


def _lease(backlog: FiniteBacklog, *, with_identity_digest: bool = True, **overrides: object) -> StandingLease:
    values = {
        "schema_id": LEASE_SCHEMA_ID,
        "schema_version": 1,
        "lease_id": "lease-a2-p1",
        "issuer_label": "operator-policy",
        "issued_at": "2026-07-14T00:00:00Z",
        "valid_from": "2026-07-14T00:00:01Z",
        "expires_at": "2026-07-15T00:00:00Z",
        "revocation_state": LeaseRevocationState.NOT_REVOKED,
        "revocation_reference": None,
        "subject": "nwp-coordinator-p1",
        "repo_identity": {"component": "nwp-coordinator", "repo_label": "coordinator-local"},
        "branch_policy": {"base": "trunk_dev", "mode": "operator-approved"},
        "allowed_paths": ("tests", "src"),
        "forbidden_path_policy_identity": "governed-execution.nwp-forbidden-paths.v1",
        "task_classes": ("docs", "code"),
        "risk_lanes": ("low",),
        "finite_backlog_reference": backlog.backlog_id,
        "finite_backlog_digest": backlog.content_digest,
        "max_work_items": 1,
        "max_concurrency": 1,
        "max_attempts": 2,
        "max_repairs": 1,
        "compute_api_budget": {"api_calls": 0, "compute_seconds": 0},
        "wall_clock_budget_seconds": 3600,
        "validation_requirements": ("unit-tests",),
        "audit_requirements": ("boundary-audit",),
        "local_commit_permission": Permission.FORBIDDEN,
        "publication_permission": Permission.FORBIDDEN,
        "cross_repo_permission": Permission.FORBIDDEN,
        "maintenance_permission": Permission.FORBIDDEN,
        "cleanup_requirements": ("no-worker-artifacts",),
        "reporting_cadence": "on-transition",
        "retention_policy": "safe-projections-only",
        "global_stop_reference": "operator-global-stop",
        "canonical_digest_metadata": {"algorithm": "sha256", "canonicalization": CANONICALIZATION_ID},
        "authorization_mechanism": {"kind": "unsupported", "descriptor": "p1-fail-closed"},
    }
    values.update(overrides)
    lease = StandingLease(**values)
    return lease.with_digest() if with_identity_digest else lease


def _record(
    lease: StandingLease,
    backlog: FiniteBacklog,
    *,
    state: WorkItemState = WorkItemState.PROPOSED,
    version: int = 0,
    work_item_id: str = "wi-1",
) -> WorkItemRecord:
    return WorkItemRecord(
        work_item_id=work_item_id,
        lease_id=lease.lease_id,
        backlog_id=backlog.backlog_id,
        state=state,
        version=version,
        max_attempts=lease.max_attempts,
        max_repairs=lease.max_repairs,
    )


def _authorization(
    lease: StandingLease,
    identity: LeaseIdentityValidation,
    *,
    model: AuthorizationModel = AuthorizationModel.UNSUPPORTED,
    authorized: bool = False,
    executable: bool = False,
    reason: str = "unsupported_authorization_model",
) -> AuthorizationDecision:
    return AuthorizationDecision(
        decision_ref="authz-lease-a2-p1",
        lease_ref=lease.lease_id,
        lease_identity_decision_ref=identity.decision_ref,
        lease_identity_valid=identity.identity_valid,
        authorization_model=model,
        authorized=authorized,
        executable=executable,
        reason=reason,
    )


def _context(
    lease: StandingLease,
    identity: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
    *,
    dependency: DependencyDecision | None = None,
    global_stop: GlobalStopState | None = None,
) -> TransitionContext:
    return TransitionContext(
        lease_identity=identity,
        authorization=authorization,
        lease_runtime=derive_lease_runtime_decision(lease, "2026-07-14T00:00:02Z"),
        global_stop=global_stop or GlobalStopState(),
        dependency_decision=dependency or DependencyDecision(),
    )


def _command(
    record: WorkItemRecord,
    identity: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
    *,
    target_state: WorkItemState = WorkItemState.LEASE_ADMITTED,
    dependency_decision_ref: str | None = None,
    global_stop: GlobalStopState | None = None,
    budget_cost: int = 0,
) -> TransitionCommand:
    state = global_stop or GlobalStopState()
    return TransitionCommand.create(
        work_item_id=record.work_item_id,
        idempotency_key=f"transition-{target_state.value.replace('_', '-')}",
        expected_version=record.version,
        target_state=target_state,
        lease_identity_decision_ref=identity.decision_ref,
        authorization_decision_ref=authorization.decision_ref,
        global_stop_ref=state.stop_ref,
        global_stop_version=state.version,
        dependency_decision_ref=dependency_decision_ref,
        budget_cost=budget_cost,
    )


def _binding_inputs(
    *,
    target_state: WorkItemState = WorkItemState.LEASE_ADMITTED,
    dependency: DependencyDecision | None = None,
    global_stop: GlobalStopState | None = None,
    authorization_model: AuthorizationModel = AuthorizationModel.UNSUPPORTED,
    authorization_reason: str = "unsupported_authorization_model",
    authorization_authorized: bool = False,
    with_identity_digest: bool = True,
) -> dict[str, object]:
    backlog = _backlog()
    lease = _lease(backlog, with_identity_digest=with_identity_digest)
    record_state = WorkItemState.LEASE_ADMITTED if target_state is WorkItemState.READY else WorkItemState.PROPOSED
    record = _record(lease, backlog, state=record_state)
    identity = lease.validate_identity()
    authorization = _authorization(
        lease,
        identity,
        model=authorization_model,
        authorized=authorization_authorized,
        reason=authorization_reason,
    )
    decision = dependency or DependencyDecision()
    state = global_stop or GlobalStopState()
    command = _command(
        record,
        identity,
        authorization,
        target_state=target_state,
        dependency_decision_ref=decision.decision_ref if target_state is WorkItemState.READY else None,
        global_stop=state,
    )
    return {
        "command": command,
        "current_record": record,
        "standing_lease": lease,
        "admitted_backlog": backlog,
        "lease_identity": identity,
        "authorization": authorization,
        "dependency": decision,
        "global_stop": state,
    }


def _unchecked_command(command: TransitionCommand, **overrides: object) -> TransitionCommand:
    unchecked = object.__new__(TransitionCommand)
    for field in fields(TransitionCommand):
        object.__setattr__(unchecked, field.name, getattr(command, field.name))
    for name, value in overrides.items():
        object.__setattr__(unchecked, name, value)
    return unchecked


def _reissued_command(command: TransitionCommand, **overrides: object) -> TransitionCommand:
    values = command.canonical_identity_payload()
    values.update(overrides)
    return TransitionCommand.create(
        work_item_id=values["work_item_id"],  # type: ignore[arg-type]
        idempotency_key=values["idempotency_key"],  # type: ignore[arg-type]
        expected_version=values["expected_version"],  # type: ignore[arg-type]
        target_state=values["target_state"],  # type: ignore[arg-type]
        lease_identity_decision_ref=values["lease_identity_decision_ref"],  # type: ignore[arg-type]
        authorization_decision_ref=values["authorization_decision_ref"],  # type: ignore[arg-type]
        global_stop_ref=values["global_stop_ref"],  # type: ignore[arg-type]
        global_stop_version=values["global_stop_version"],  # type: ignore[arg-type]
        dependency_decision_ref=values["dependency_decision_ref"],  # type: ignore[arg-type]
        evidence_refs=values["evidence_refs"],  # type: ignore[arg-type]
        safe_failure_class=values["safe_failure_class"],  # type: ignore[arg-type]
        budget_cost=values["budget_cost"],  # type: ignore[arg-type]
    )


def _forged_exact(model_type: type[object], **values: object) -> object:
    forged = object.__new__(model_type)
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _clone_into(model: object, model_type: type[object]) -> object:
    return model_type(**{field.name: getattr(model, field.name) for field in fields(model)})


def _forged_from_model(model: object, **overrides: object) -> object:
    values = {field.name: getattr(model, field.name) for field in fields(model)}
    values.update(overrides)
    return _forged_exact(type(model), **values)


class _HostileValue:
    def __str__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)

    def __repr__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)

    def __eq__(self, other: object) -> bool:
        raise AssertionError(PRIVATE_SENTINEL)

    def __hash__(self) -> int:
        raise AssertionError(PRIVATE_SENTINEL)


class _HostileEqualityKey:
    def __init__(self, forced_hash: int) -> None:
        self._forced_hash = forced_hash
        self.eq_calls = 0

    def __hash__(self) -> int:
        return self._forced_hash

    def __eq__(self, other: object) -> bool:
        self.eq_calls += 1
        raise AssertionError(PRIVATE_SENTINEL)

    def __str__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)

    def __repr__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)

    def __format__(self, format_spec: str) -> str:
        raise AssertionError(PRIVATE_SENTINEL)


class _HostileStringSubclassKey(str):
    eq_calls: int

    def __new__(cls, value: str) -> "_HostileStringSubclassKey":
        instance = str.__new__(cls, value)
        instance.eq_calls = 0
        return instance

    def __hash__(self) -> int:
        return str.__hash__(self)

    def __eq__(self, other: object) -> bool:
        self.eq_calls += 1
        raise AssertionError(PRIVATE_SENTINEL)

    def __repr__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)

    def __format__(self, format_spec: str) -> str:
        raise AssertionError(PRIVATE_SENTINEL)


class _BenignNonStringKey:
    pass


def _active_global_stop() -> GlobalStopState:
    return GlobalStopState(
        version=1,
        active=True,
        stop_id="stop-active",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-1",
        issued_at="2026-07-14T00:00:01Z",
        operator_decision_ref="operator-decision-1",
    )


def _trusted_payload(model: object) -> dict[str, object]:
    if type(model) is WorkItemRecord:
        return WorkItemRecord.to_dict(model)
    if type(model) is TransitionEvent:
        return TransitionEvent.to_dict(model)
    if type(model) is StandingLease:
        return StandingLease.to_dict(model)
    if type(model) is FiniteBacklog:
        return FiniteBacklog.to_dict(model)
    if type(model) is AuthorizationDecision:
        return AuthorizationDecision.to_dict(model)
    if type(model) is DependencyDecision:
        return DependencyDecision.to_dict(model)
    if type(model) is GlobalStopState:
        return GlobalStopState.to_dict(model)
    raise AssertionError(type(model).__name__)


def _conflicting_payload(model: object) -> dict[str, object]:
    payload = _trusted_payload(model)
    if type(model) is WorkItemRecord:
        payload["work_item_id"] = "wi-shadow"
    elif type(model) is TransitionEvent:
        payload["work_item_id"] = "wi-shadow"
    elif type(model) is StandingLease:
        payload["lease_id"] = "lease-shadow"
    elif type(model) is FiniteBacklog:
        payload["backlog_id"] = "backlog-shadow"
    elif type(model) is AuthorizationDecision:
        payload["decision_ref"] = "authz-shadow"
    elif type(model) is DependencyDecision:
        payload["decision_ref"] = "deps-shadow"
    elif type(model) is GlobalStopState:
        payload["stop_id"] = "stop-shadow"
    else:
        raise AssertionError(type(model).__name__)
    return payload


def _with_shadowed_to_dict(model: object, *, payload: object | None = None, hostile: bool = False) -> list[str]:
    calls: list[str] = []

    def shadow() -> object:
        calls.append("called")
        if hostile:
            raise RuntimeError(PRIVATE_SENTINEL)
        return payload

    object.__setattr__(model, "to_dict", shadow)
    return calls


def _empty_shell_with_extra_key(model_type: type[object], key: object) -> object:
    forged = object.__new__(model_type)
    dict.__setitem__(object.__getattribute__(forged, "__dict__"), key, PRIVATE_SENTINEL)
    return forged


def _forged_with_extra_key(model: object, key: object) -> object:
    forged = _forged_from_model(model)
    dict.__setitem__(object.__getattribute__(forged, "__dict__"), key, PRIVATE_SENTINEL)
    return forged


def _forged_without_field_with_extra_key(model: object, *, missing: str, key: object) -> object:
    forged = _forged_from_model(model)
    state = object.__getattribute__(forged, "__dict__")
    del state[missing]
    dict.__setitem__(state, key, PRIVATE_SENTINEL)
    return forged


def _forged_with_exact_string_extras(model: object) -> tuple[object, list[str]]:
    calls: list[str] = []

    def shadow() -> object:
        calls.append("called")
        raise AssertionError(PRIVATE_SENTINEL)

    forged = _forged_from_model(model)
    state = object.__getattribute__(forged, "__dict__")
    state["to_dict"] = shadow
    state["compute_digest"] = shadow
    state["canonical_json"] = shadow
    return forged, calls


def _non_colliding_hostile_key(model_type: type[object]) -> _HostileEqualityKey:
    field_hashes = {hash(field.name) for field in fields(model_type)}
    forced_hash = 0
    while forced_hash in field_hashes:
        forced_hash += 1
    return _HostileEqualityKey(forced_hash)


def _exception_text(exc: BaseException) -> str:
    parts = [
        str(exc),
        repr(exc),
        repr(exc.args),
        repr(getattr(exc, "internal_detail", None)),
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    ]
    if getattr(exc, "__notes__", None):
        parts.append(repr(exc.__notes__))
    return "\n".join(parts)


def _assert_exception_is_redacted(exc: BaseException, *, sentinel: str = PRIVATE_SENTINEL) -> None:
    assert sentinel not in _exception_text(exc)
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert not getattr(exc, "__notes__", ())


def _accepted_evaluation() -> TransitionEvaluation:
    backlog = _backlog()
    lease = _lease(backlog)
    record = _record(lease, backlog)
    identity = lease.validate_identity()
    authorization = _authorization(
        lease,
        identity,
        model=AuthorizationModel.OPERATOR_POLICY,
        authorized=True,
        reason="accepted",
    )
    context = _context(lease, identity, authorization)
    command = _command(record, identity, authorization)
    evaluation = evaluate_transition(record, command, context)
    assert evaluation.kind is TransitionEvaluationKind.ACCEPTED
    return evaluation


def _domain_rejected_evaluation() -> TransitionEvaluation:
    values = _binding_inputs()
    record = values["current_record"]
    command = values["command"]
    lease = values["standing_lease"]
    identity = values["lease_identity"]
    authorization = values["authorization"]
    evaluation = evaluate_transition(
        record,
        command,
        _context(lease, identity, authorization),  # type: ignore[arg-type]
    )
    assert evaluation.kind is TransitionEvaluationKind.DOMAIN_REJECTED
    return evaluation


def _pre_apply_invalid_evaluation() -> TransitionEvaluation:
    values = _binding_inputs()
    record = values["current_record"]
    command = _unchecked_command(values["command"], work_item_id="wi-other")  # type: ignore[arg-type]
    lease = values["standing_lease"]
    identity = values["lease_identity"]
    authorization = values["authorization"]
    evaluation = evaluate_transition(
        record,
        command,
        _context(lease, identity, authorization),  # type: ignore[arg-type]
    )
    assert evaluation.kind is TransitionEvaluationKind.PRE_APPLY_INVALID
    return evaluation


def _assert_integrity_failure(call: object) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()  # type: ignore[operator]
    assert exc_info.value.error_class == "database_integrity_failure"
    assert str(exc_info.value) == "database_integrity_failure"
    assert "private-ref" not in repr(exc_info.value)
    assert "canonical_command_digest" not in repr(exc_info.value)
    assert not isinstance(exc_info.value, (AttributeError, ValueError))
    _assert_exception_is_redacted(exc_info.value)
    return exc_info.value


def _assert_validation_conflict(result: object) -> None:
    assert type(result) is TransitionConflict
    assert result.conflict_class == "validation_failed"


def _candidate_reconstruction_cases() -> tuple[tuple[str, object, object, str], ...]:
    values = _binding_inputs(global_stop=_active_global_stop())
    accepted = _accepted_evaluation()
    return (
        ("work_item", values["admitted_backlog"].work_items[0], _require_initialized_work_item, "work_item_id"),
        ("work_item_record", values["current_record"], _require_initialized_work_item_record, "work_item_id"),
        ("lease_runtime", accepted.event.lease_runtime, _require_initialized_lease_runtime, "lease_ref"),
        ("transition_event", accepted.event, _require_initialized_transition_event, "event_ref"),
        (
            "transition_command",
            values["command"],
            _require_initialized_transition_command,
            "work_item_id",
        ),
        (
            "transition_conflict",
            TransitionConflict("stale_writer_token"),
            _require_initialized_transition_conflict,
            "conflict_class",
        ),
        (
            "committed_transition",
            CommittedTransition(record=accepted.record, event=accepted.event, replayed=True),
            _require_initialized_committed_transition,
            "record",
        ),
        (
            "transition_evaluation",
            accepted,
            _require_initialized_transition_evaluation,
            "kind",
        ),
        ("standing_lease", values["standing_lease"], _require_initialized_standing_lease, "lease_id"),
        ("finite_backlog", values["admitted_backlog"], _require_initialized_finite_backlog, "backlog_id"),
        ("lease_identity", values["lease_identity"], _require_initialized_lease_identity, "decision_ref"),
        (
            "validation_issue",
            ValidationIssue(field="schema_id", reason="schema_id_mismatch"),
            _require_initialized_validation_issue,
            "field",
        ),
        ("authorization", values["authorization"], _require_initialized_authorization, "decision_ref"),
        ("dependency", values["dependency"], _require_initialized_dependency, "decision_ref"),
        ("global_stop", values["global_stop"], _require_initialized_global_stop, "schema_id"),
    )


def _assert_preflight_error(call: object, reason: _TransitionDryRunPreflightFailureReason) -> None:
    with pytest.raises(_TransitionDryRunPreflightError) as exc_info:
        call()  # type: ignore[operator]
    assert exc_info.value.reason is reason
    assert str(exc_info.value) == reason.value
    assert repr(exc_info.value) == "<_TransitionDryRunPreflightError>"
    assert "wi-1" not in repr(exc_info.value)
    assert "transition-" not in repr(exc_info.value)
    _assert_exception_is_redacted(exc_info.value)


def test_preflight_error_constructor_accepts_only_exact_private_enum(capsys: pytest.CaptureFixture[str]) -> None:
    for reason in _TransitionDryRunPreflightFailureReason:
        exc = _TransitionDryRunPreflightError(reason)
        assert exc.reason is reason
        assert str(exc) == reason.value
        assert exc.args == (reason.value,)
        assert repr(exc) == "<_TransitionDryRunPreflightError>"
        _assert_exception_is_redacted(exc)

    private_value = "synthetic-" + "private-sentinel"
    invalid_inputs = (
        "transition_dry_run_invalid_command",
        private_value,
        object(),
        _HostileValue(),
    )
    for invalid in invalid_inputs:
        with pytest.raises(ValueError) as exc_info:
            _TransitionDryRunPreflightError(invalid)  # type: ignore[arg-type]
        assert str(exc_info.value) == "invalid_field_type:transition_dry_run_preflight.reason"
        assert exc_info.value.args == ("invalid_field_type:transition_dry_run_preflight.reason",)
        _assert_exception_is_redacted(exc_info.value, sentinel=private_value)
        captured = capsys.readouterr()
        assert private_value not in captured.out
        assert private_value not in captured.err


def test_dry_run_result_accepts_all_valid_private_variants() -> None:
    accepted = _accepted_evaluation()
    rejected = _domain_rejected_evaluation()
    replay = CommittedTransition(record=accepted.record, event=accepted.event, replayed=True)
    conflict = TransitionConflict("stale_writer_token")

    replay_result = _RollbackOnlyTransitionDryRunResult(
        kind=_RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
        replayed_transition=replay,
    )
    conflict_result = _RollbackOnlyTransitionDryRunResult(
        kind=_RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT,
        conflict=conflict,
    )
    accepted_result = _RollbackOnlyTransitionDryRunResult(
        kind=_RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
        evaluation=accepted,
    )
    rejected_result = _RollbackOnlyTransitionDryRunResult(
        kind=_RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED,
        evaluation=rejected,
    )

    assert replay_result.replayed_transition == replay
    assert replay_result.replayed_transition is not replay
    assert conflict_result.conflict == TransitionConflict("stale_writer_token")
    assert conflict_result.conflict is not conflict
    assert accepted_result.evaluation == accepted
    assert accepted_result.evaluation is not accepted
    assert rejected_result.evaluation == rejected
    assert rejected_result.evaluation is not rejected


def test_dry_run_result_requires_exactly_one_matching_payload_and_exact_types() -> None:
    accepted = _accepted_evaluation()
    replay = CommittedTransition(record=accepted.record, event=accepted.event, replayed=True)

    class ReplaySubclass(CommittedTransition):
        pass

    class ConflictSubclass(TransitionConflict):
        pass

    class EvaluationSubclass(TransitionEvaluation):
        pass

    cases = (
        lambda: _RollbackOnlyTransitionDryRunResult(_RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY),
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=replay,
            conflict=TransitionConflict("stale_writer_token"),
        ),
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=ReplaySubclass(record=accepted.record, event=accepted.event, replayed=True),
        ),
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT,
            conflict=ConflictSubclass("stale_writer_token"),
        ),
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
            evaluation=EvaluationSubclass(
                kind=accepted.kind,
                reason=accepted.reason,
                record=accepted.record,
                event=accepted.event,
            ),
        ),
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
            evaluation=object(),  # type: ignore[arg-type]
        ),
    )
    for case in cases:
        _assert_integrity_failure(case)


def test_replay_conflict_and_evaluation_invariants_are_closed() -> None:
    accepted = _accepted_evaluation()
    rejected = _domain_rejected_evaluation()
    pre_apply = _pre_apply_invalid_evaluation()

    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=CommittedTransition(record=accepted.record, event=accepted.event, replayed=False),
        )
    )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT,
            conflict=TransitionConflict("split_brain_writer"),
        )
    )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
            evaluation=rejected,
        )
    )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED,
            evaluation=accepted,
        )
    )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED,
            evaluation=pre_apply,
        )
    )


def test_dry_run_result_rejects_forged_exact_and_hostile_nested_payloads() -> None:
    accepted = _accepted_evaluation()
    replay = CommittedTransition(record=accepted.record, event=accepted.event, replayed=True)

    class RecordSubclass(WorkItemRecord):
        pass

    class EventSubclass(TransitionEvent):
        pass

    class ReplaySubclass(CommittedTransition):
        pass

    class ConflictSubclass(TransitionConflict):
        pass

    class EvaluationSubclass(TransitionEvaluation):
        pass

    record_subclass = _clone_into(accepted.record, RecordSubclass)
    event_subclass = _clone_into(accepted.event, EventSubclass)
    forged_record_shell = object.__new__(WorkItemRecord)
    forged_event_shell = object.__new__(TransitionEvent)
    forged_record_hostile = _forged_from_model(accepted.record, work_item_id=_HostileValue())
    forged_event_hostile = _forged_from_model(accepted.event, event_ref=_HostileValue())

    invalid_replays = (
        ReplaySubclass(record=accepted.record, event=accepted.event, replayed=True),
        object.__new__(CommittedTransition),
        _forged_exact(CommittedTransition, record=record_subclass, event=accepted.event, replayed=True),
        _forged_exact(CommittedTransition, record=forged_record_shell, event=accepted.event, replayed=True),
        _forged_exact(CommittedTransition, record=forged_record_hostile, event=accepted.event, replayed=True),
        _forged_exact(CommittedTransition, record=accepted.record, event=event_subclass, replayed=True),
        _forged_exact(CommittedTransition, record=accepted.record, event=forged_event_shell, replayed=True),
        _forged_exact(CommittedTransition, record=accepted.record, event=forged_event_hostile, replayed=True),
        _forged_exact(CommittedTransition, record=accepted.record, event=accepted.event, replayed=_HostileValue()),
        replay,
    )
    for invalid in invalid_replays[:-1]:
        _assert_integrity_failure(
            lambda invalid=invalid: _RollbackOnlyTransitionDryRunResult(
                _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
                replayed_transition=invalid,  # type: ignore[arg-type]
            )
        )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=CommittedTransition(record=accepted.record, event=accepted.event, replayed=False),
        )
    )

    conflict_cases = (
        ConflictSubclass("stale_writer_token"),
        object.__new__(TransitionConflict),
        _forged_exact(TransitionConflict, conflict_class=_HostileValue()),
        TransitionConflict("split_brain_writer"),
    )
    for invalid in conflict_cases:
        _assert_integrity_failure(
            lambda invalid=invalid: _RollbackOnlyTransitionDryRunResult(
                _RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT,
                conflict=invalid,  # type: ignore[arg-type]
            )
        )

    forged_accepted = _forged_exact(
        TransitionEvaluation,
        kind=TransitionEvaluationKind.ACCEPTED,
        reason="transition_accepted",
        record=forged_record_shell,
        event=accepted.event,
    )
    forged_event_accepted = _forged_exact(
        TransitionEvaluation,
        kind=TransitionEvaluationKind.ACCEPTED,
        reason="transition_accepted",
        record=accepted.record,
        event=forged_event_shell,
    )
    hostile_reason = _forged_exact(
        TransitionEvaluation,
        kind=TransitionEvaluationKind.ACCEPTED,
        reason=_HostileValue(),
        record=accepted.record,
        event=accepted.event,
    )
    evaluation_cases = (
        EvaluationSubclass(
            kind=accepted.kind,
            reason=accepted.reason,
            record=accepted.record,
            event=accepted.event,
        ),
        object.__new__(TransitionEvaluation),
        forged_accepted,
        forged_event_accepted,
        hostile_reason,
        _forged_exact(
            TransitionEvaluation,
            kind=TransitionEvaluationKind.PRE_APPLY_INVALID,
            reason="work_item_id_mismatch",
            record=accepted.record,
            event=None,
        ),
    )
    for invalid in evaluation_cases:
        _assert_integrity_failure(
            lambda invalid=invalid: _RollbackOnlyTransitionDryRunResult(
                _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
                evaluation=invalid,  # type: ignore[arg-type]
            )
        )


def test_dry_run_result_repr_privacy_and_no_serialization_surface() -> None:
    accepted = _accepted_evaluation()
    result = _RollbackOnlyTransitionDryRunResult(
        _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
        evaluation=accepted,
    )

    assert repr(result) == "<_RollbackOnlyTransitionDryRunResult kind=accepted_evaluation_not_persisted>"
    for private_value in (
        accepted.event.event_ref,
        accepted.event.command_digest,
        accepted.event.idempotency_key,
        accepted.record.work_item_id,
    ):
        assert private_value not in repr(result)
    for method_name in ("to_dict", "from_dict", "canonical_json", "canonical_digest", "report", "serialize"):
        assert not hasattr(result, method_name)


def test_preflight_accepts_only_exact_command_with_valid_digest_and_supported_bounded_slice() -> None:
    values = _binding_inputs()
    command = values["command"]

    assert _validate_transition_dry_run_preflight(command) is command

    class CommandSubclass(TransitionCommand):
        pass

    subclass = CommandSubclass(**{field.name: getattr(command, field.name) for field in fields(TransitionCommand)})
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(subclass),
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(object()),  # type: ignore[arg-type]
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(object.__new__(TransitionCommand)),
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(_unchecked_command(command, canonical_command_digest="0" * 64)),
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(_unchecked_command(command, target_state="ready")),
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(_unchecked_command(command, target_state=_HostileValue())),
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )

    hostile_digest = _unchecked_command(command)

    def raise_hostile_digest() -> str:
        digest_calls.append("called")
        raise RuntimeError(PRIVATE_SENTINEL)

    digest_calls: list[str] = []
    object.__setattr__(hostile_digest, "compute_digest", raise_hostile_digest)
    assert _validate_transition_dry_run_preflight(hostile_digest) is hostile_digest
    assert digest_calls == []

    digest_mismatch_with_shadow = _unchecked_command(command, canonical_command_digest="0" * 64)

    def forged_digest() -> str:
        digest_calls.append("mismatch-called")
        return "0" * 64

    object.__setattr__(digest_mismatch_with_shadow, "compute_digest", forged_digest)
    _assert_preflight_error(
        lambda: _validate_transition_dry_run_preflight(digest_mismatch_with_shadow),
        _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
    )
    assert digest_calls == []


def test_preflight_rejects_non_ready_dependency_refs_and_nonzero_budget_without_other_results() -> None:
    values = _binding_inputs()
    record = values["current_record"]
    identity = values["lease_identity"]
    authorization = values["authorization"]
    non_ready_with_dependency = _command(
        record,
        identity,
        authorization,
        dependency_decision_ref="deps-ready",
    )
    nonzero_budget = _command(record, identity, authorization, budget_cost=1)

    for invalid in (non_ready_with_dependency, nonzero_budget):
        _assert_preflight_error(
            lambda invalid=invalid: _validate_transition_dry_run_preflight(invalid),  # type: ignore[arg-type]
            _TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND,
        )


def test_model_reconstructors_ignore_instance_shadowed_to_dict_and_use_real_fields() -> None:
    values = _binding_inputs()
    accepted = _accepted_evaluation()
    active_stop = _active_global_stop()
    cases = (
        (
            "work_item_record",
            values["current_record"],
            lambda model: _forged_from_model(model, work_item_id=_HostileValue()),
            _require_initialized_work_item_record,
        ),
        (
            "transition_event",
            accepted.event,
            lambda model: _forged_from_model(model, event_ref=_HostileValue()),
            _require_initialized_transition_event,
        ),
        (
            "standing_lease",
            values["standing_lease"],
            lambda model: _forged_from_model(model, lease_id=_HostileValue()),
            _require_initialized_standing_lease,
        ),
        (
            "finite_backlog",
            values["admitted_backlog"],
            lambda model: _forged_from_model(model, backlog_id=_HostileValue()),
            _require_initialized_finite_backlog,
        ),
        (
            "authorization",
            values["authorization"],
            lambda model: _forged_from_model(model, decision_ref=_HostileValue()),
            _require_initialized_authorization,
        ),
        (
            "dependency",
            values["dependency"],
            lambda model: _forged_from_model(model, decision_ref=_HostileValue()),
            _require_initialized_dependency,
        ),
        (
            "global_stop",
            active_stop,
            lambda model: _forged_from_model(model, stop_id=_HostileValue()),
            _require_initialized_global_stop,
        ),
    )

    for _name, valid_model, invalid_factory, reconstructor in cases:
        clean_shadow = invalid_factory(valid_model)
        clean_calls = _with_shadowed_to_dict(clean_shadow, payload=_trusted_payload(valid_model))
        _assert_integrity_failure(lambda clean_shadow=clean_shadow: reconstructor(clean_shadow))
        assert clean_calls == []

        hostile_shadow = invalid_factory(valid_model)
        hostile_calls = _with_shadowed_to_dict(hostile_shadow, hostile=True)
        _assert_integrity_failure(lambda hostile_shadow=hostile_shadow: reconstructor(hostile_shadow))
        assert hostile_calls == []

        conflicting_shadow = _forged_from_model(valid_model)
        conflicting_calls = _with_shadowed_to_dict(
            conflicting_shadow,
            payload=_conflicting_payload(valid_model),
        )
        reconstructed = reconstructor(conflicting_shadow)
        assert reconstructed == valid_model
        assert reconstructed is not conflicting_shadow
        assert conflicting_calls == []

        hostile_valid_shadow = _forged_from_model(valid_model)
        hostile_valid_calls = _with_shadowed_to_dict(hostile_valid_shadow, hostile=True)
        reconstructed = reconstructor(hostile_valid_shadow)
        assert reconstructed == valid_model
        assert reconstructed is not hostile_valid_shadow
        assert hostile_valid_calls == []


def test_model_reconstructors_reject_hostile_instance_dictionary_keys_before_lookup(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name, valid_model, reconstructor, required_field in _candidate_reconstruction_cases():
        hostile_collision = _HostileEqualityKey(hash(required_field))
        colliding_shell = _empty_shell_with_extra_key(type(valid_model), hostile_collision)
        assert hostile_collision.eq_calls == 0
        exc = _assert_integrity_failure(lambda reconstructor=reconstructor, model=colliding_shell: reconstructor(model))
        assert hostile_collision.eq_calls == 0
        assert "_HostileEqualityKey" not in _exception_text(exc)

        string_subclass_key = _HostileStringSubclassKey("to_dict")
        string_subclass_shell = _empty_shell_with_extra_key(type(valid_model), string_subclass_key)
        assert string_subclass_key.eq_calls == 0
        exc = _assert_integrity_failure(
            lambda reconstructor=reconstructor, model=string_subclass_shell: reconstructor(model)
        )
        assert string_subclass_key.eq_calls == 0
        assert "_HostileStringSubclassKey" not in _exception_text(exc)

        benign_key = _BenignNonStringKey()
        benign_shell = _empty_shell_with_extra_key(type(valid_model), benign_key)
        exc = _assert_integrity_failure(lambda reconstructor=reconstructor, model=benign_shell: reconstructor(model))
        assert "_BenignNonStringKey" not in _exception_text(exc)

        hostile_extra = _non_colliding_hostile_key(type(valid_model))
        valid_with_hostile_extra = _forged_with_extra_key(valid_model, hostile_extra)
        assert hostile_extra.eq_calls == 0
        exc = _assert_integrity_failure(
            lambda reconstructor=reconstructor, model=valid_with_hostile_extra: reconstructor(model)
        )
        assert hostile_extra.eq_calls == 0
        assert "_HostileEqualityKey" not in _exception_text(exc)

        missing_collision = _HostileEqualityKey(hash(required_field))
        missing_with_collision = _forged_without_field_with_extra_key(
            valid_model,
            missing=required_field,
            key=missing_collision,
        )
        assert missing_collision.eq_calls == 0
        exc = _assert_integrity_failure(
            lambda reconstructor=reconstructor, model=missing_with_collision: reconstructor(model)
        )
        assert missing_collision.eq_calls == 0
        assert "_HostileEqualityKey" not in _exception_text(exc)

        captured = capsys.readouterr()
        assert PRIVATE_SENTINEL not in captured.out
        assert PRIVATE_SENTINEL not in captured.err
        assert name


def test_model_reconstructors_ignore_extra_exact_string_shadow_attributes() -> None:
    for _name, valid_model, reconstructor, _required_field in _candidate_reconstruction_cases():
        forged, calls = _forged_with_exact_string_extras(valid_model)

        reconstructed = reconstructor(forged)  # type: ignore[operator]

        assert reconstructed == valid_model
        assert reconstructed is not forged
        assert calls == []


def test_composite_result_reconstructors_ignore_shadowed_nested_model_to_dict() -> None:
    accepted = _accepted_evaluation()
    replay = CommittedTransition(record=accepted.record, event=accepted.event, replayed=True)

    invalid_record = _forged_from_model(accepted.record, work_item_id=_HostileValue())
    invalid_record_calls = _with_shadowed_to_dict(invalid_record, payload=_trusted_payload(accepted.record))
    forged_replay = _forged_exact(CommittedTransition, record=invalid_record, event=accepted.event, replayed=True)
    _assert_integrity_failure(lambda: _require_initialized_committed_transition(forged_replay))
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=forged_replay,  # type: ignore[arg-type]
        )
    )
    assert invalid_record_calls == []

    invalid_event = _forged_from_model(accepted.event, event_ref=_HostileValue())
    invalid_event_calls = _with_shadowed_to_dict(invalid_event, payload=_trusted_payload(accepted.event))
    forged_event_replay = _forged_exact(CommittedTransition, record=accepted.record, event=invalid_event, replayed=True)
    _assert_integrity_failure(lambda: _require_initialized_committed_transition(forged_event_replay))
    assert invalid_event_calls == []

    shadowed_record = _forged_from_model(accepted.record)
    shadowed_record_calls = _with_shadowed_to_dict(shadowed_record, payload=_conflicting_payload(accepted.record))
    shadowed_replay = _forged_exact(CommittedTransition, record=shadowed_record, event=accepted.event, replayed=True)
    reconstructed_replay = _require_initialized_committed_transition(shadowed_replay)
    assert reconstructed_replay == replay
    assert reconstructed_replay.record is not shadowed_record
    assert shadowed_record_calls == []

    shadowed_event = _forged_from_model(accepted.event)
    shadowed_event_calls = _with_shadowed_to_dict(shadowed_event, hostile=True)
    shadowed_evaluation = _forged_exact(
        TransitionEvaluation,
        kind=accepted.kind,
        reason=accepted.reason,
        record=accepted.record,
        event=shadowed_event,
    )
    reconstructed_evaluation = _require_initialized_transition_evaluation(shadowed_evaluation)
    assert reconstructed_evaluation == accepted
    assert reconstructed_evaluation.event is not shadowed_event
    assert shadowed_event_calls == []

    invalid_evaluation = _forged_exact(
        TransitionEvaluation,
        kind=accepted.kind,
        reason=accepted.reason,
        record=invalid_record,
        event=accepted.event,
    )
    _assert_integrity_failure(lambda: _require_initialized_transition_evaluation(invalid_evaluation))
    assert invalid_record_calls == []


def test_hostile_dictionary_keys_are_rejected_through_result_and_authority_entry_paths(
    capsys: pytest.CaptureFixture[str],
) -> None:
    values = _binding_inputs(global_stop=_active_global_stop())
    accepted = _accepted_evaluation()

    replay_record_key = _non_colliding_hostile_key(WorkItemRecord)
    replay_record = _forged_with_extra_key(accepted.record, replay_record_key)
    forged_replay = _forged_exact(
        CommittedTransition,
        record=replay_record,
        event=accepted.event,
        replayed=True,
    )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY,
            replayed_transition=forged_replay,  # type: ignore[arg-type]
        )
    )
    assert replay_record_key.eq_calls == 0

    evaluation_event_key = _non_colliding_hostile_key(TransitionEvent)
    evaluation_event = _forged_with_extra_key(accepted.event, evaluation_event_key)
    forged_evaluation = _forged_exact(
        TransitionEvaluation,
        kind=accepted.kind,
        reason=accepted.reason,
        record=accepted.record,
        event=evaluation_event,
    )
    _assert_integrity_failure(
        lambda: _RollbackOnlyTransitionDryRunResult(
            _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
            evaluation=forged_evaluation,  # type: ignore[arg-type]
        )
    )
    assert evaluation_event_key.eq_calls == 0

    authority_record_key = _non_colliding_hostile_key(WorkItemRecord)
    authority_record = _forged_with_extra_key(values["current_record"], authority_record_key)
    _assert_integrity_failure(
        lambda: _BoundTransitionAuthority(
            current_record=authority_record,  # type: ignore[arg-type]
            standing_lease=values["standing_lease"],  # type: ignore[arg-type]
            lease_identity=values["lease_identity"],  # type: ignore[arg-type]
            authorization=values["authorization"],  # type: ignore[arg-type]
            dependency=values["dependency"],  # type: ignore[arg-type]
            global_stop=values["global_stop"],  # type: ignore[arg-type]
        )
    )
    assert authority_record_key.eq_calls == 0

    binding_command_key = _non_colliding_hostile_key(TransitionCommand)
    binding_command = _forged_with_extra_key(values["command"], binding_command_key)
    _assert_integrity_failure(
        lambda: _bind_b3c3_transition_authority(
            **{**values, "command": binding_command},  # type: ignore[arg-type]
        )
    )
    assert binding_command_key.eq_calls == 0

    binding_backlog_key = _non_colliding_hostile_key(FiniteBacklog)
    binding_backlog = _forged_with_extra_key(values["admitted_backlog"], binding_backlog_key)
    _assert_integrity_failure(
        lambda: _bind_b3c3_transition_authority(
            **{**values, "admitted_backlog": binding_backlog},  # type: ignore[arg-type]
        )
    )
    assert binding_backlog_key.eq_calls == 0

    captured = capsys.readouterr()
    assert PRIVATE_SENTINEL not in captured.out
    assert PRIVATE_SENTINEL not in captured.err


def test_bound_authority_and_binding_ignore_shadowed_to_dict_for_all_authority_inputs() -> None:
    values = _binding_inputs(global_stop=_active_global_stop())
    binding_cases = (
        ("current_record", lambda model: _forged_from_model(model, work_item_id=_HostileValue())),
        ("standing_lease", lambda model: _forged_from_model(model, lease_id=_HostileValue())),
        ("admitted_backlog", lambda model: _forged_from_model(model, backlog_id=_HostileValue())),
        ("lease_identity", lambda model: _forged_from_model(model, decision_ref=_HostileValue())),
        ("authorization", lambda model: _forged_from_model(model, decision_ref=_HostileValue())),
        ("dependency", lambda model: _forged_from_model(model, decision_ref=_HostileValue())),
        ("global_stop", lambda model: _forged_from_model(model, stop_id=_HostileValue())),
    )

    for field_name, invalid_factory in binding_cases:
        valid_value = values[field_name]
        clean_shadow = invalid_factory(valid_value)
        clean_calls = _with_shadowed_to_dict(
            clean_shadow,
            payload=_trusted_payload(valid_value) if field_name != "lease_identity" else {},
        )
        _assert_integrity_failure(
            lambda clean_shadow=clean_shadow, field_name=field_name: _bind_b3c3_transition_authority(
                **{**values, field_name: clean_shadow},  # type: ignore[arg-type]
            )
        )
        assert clean_calls == []

        hostile_shadow = invalid_factory(valid_value)
        hostile_calls = _with_shadowed_to_dict(hostile_shadow, hostile=True)
        _assert_integrity_failure(
            lambda hostile_shadow=hostile_shadow, field_name=field_name: _bind_b3c3_transition_authority(
                **{**values, field_name: hostile_shadow},  # type: ignore[arg-type]
            )
        )
        assert hostile_calls == []

        if field_name == "lease_identity":
            valid_shadow = _forged_from_model(valid_value)
            valid_calls = _with_shadowed_to_dict(valid_shadow, hostile=True)
        else:
            valid_shadow = _forged_from_model(valid_value)
            valid_calls = _with_shadowed_to_dict(valid_shadow, payload=_conflicting_payload(valid_value))
        result = _bind_b3c3_transition_authority(
            **{**values, field_name: valid_shadow},  # type: ignore[arg-type]
        )
        assert type(result) is _BoundTransitionAuthority
        assert valid_calls == []

    direct_values = dict(values)
    for field_name, invalid_factory in (
        ("current_record", lambda model: _forged_from_model(model, work_item_id=_HostileValue())),
        ("standing_lease", lambda model: _forged_from_model(model, lease_id=_HostileValue())),
        ("lease_identity", lambda model: _forged_from_model(model, decision_ref=_HostileValue())),
        ("authorization", lambda model: _forged_from_model(model, decision_ref=_HostileValue())),
        ("dependency", lambda model: _forged_from_model(model, decision_ref=_HostileValue())),
        ("global_stop", lambda model: _forged_from_model(model, stop_id=_HostileValue())),
    ):
        valid_shadow = _forged_from_model(direct_values[field_name])
        valid_calls = _with_shadowed_to_dict(valid_shadow, hostile=True)
        attempted = {**direct_values, field_name: valid_shadow}
        result = _BoundTransitionAuthority(
            current_record=attempted["current_record"],  # type: ignore[arg-type]
            standing_lease=attempted["standing_lease"],  # type: ignore[arg-type]
            lease_identity=attempted["lease_identity"],  # type: ignore[arg-type]
            authorization=attempted["authorization"],  # type: ignore[arg-type]
            dependency=attempted["dependency"],  # type: ignore[arg-type]
            global_stop=attempted["global_stop"],  # type: ignore[arg-type]
        )
        assert getattr(result, field_name) == direct_values[field_name]
        assert getattr(result, field_name) is not valid_shadow
        assert valid_calls == []

        clean_shadow = invalid_factory(direct_values[field_name])
        calls = _with_shadowed_to_dict(
            clean_shadow,
            payload=_trusted_payload(direct_values[field_name]) if field_name != "lease_identity" else {},
        )
        attempted = {**direct_values, field_name: clean_shadow}
        _assert_integrity_failure(
            lambda attempted=attempted: _BoundTransitionAuthority(
                current_record=attempted["current_record"],  # type: ignore[arg-type]
                standing_lease=attempted["standing_lease"],  # type: ignore[arg-type]
                lease_identity=attempted["lease_identity"],  # type: ignore[arg-type]
                authorization=attempted["authorization"],  # type: ignore[arg-type]
                dependency=attempted["dependency"],  # type: ignore[arg-type]
                global_stop=attempted["global_stop"],  # type: ignore[arg-type]
            )
        )
        assert calls == []

        hostile_shadow = invalid_factory(direct_values[field_name])
        hostile_calls = _with_shadowed_to_dict(hostile_shadow, hostile=True)
        attempted = {**direct_values, field_name: hostile_shadow}
        _assert_integrity_failure(
            lambda attempted=attempted: _BoundTransitionAuthority(
                current_record=attempted["current_record"],  # type: ignore[arg-type]
                standing_lease=attempted["standing_lease"],  # type: ignore[arg-type]
                lease_identity=attempted["lease_identity"],  # type: ignore[arg-type]
                authorization=attempted["authorization"],  # type: ignore[arg-type]
                dependency=attempted["dependency"],  # type: ignore[arg-type]
                global_stop=attempted["global_stop"],  # type: ignore[arg-type]
            )
        )
        assert hostile_calls == []


def test_bound_authority_accepts_valid_rows_and_unsupported_authorization_fail_closed_input() -> None:
    values = _binding_inputs()

    result = _bind_b3c3_transition_authority(**values)  # type: ignore[arg-type]

    assert type(result) is _BoundTransitionAuthority
    assert result.current_record == values["current_record"]
    assert result.current_record is not values["current_record"]
    assert result.authorization.authorization_model is AuthorizationModel.UNSUPPORTED
    assert repr(result) == "<_BoundTransitionAuthority>"
    assert "private-ref" not in repr(result)


def test_bound_authority_accepts_coherent_invalid_lease_identity_as_evaluator_input() -> None:
    values = _binding_inputs(with_identity_digest=False)

    result = _bind_b3c3_transition_authority(**values)  # type: ignore[arg-type]

    assert type(result) is _BoundTransitionAuthority
    assert result.lease_identity.identity_valid is False
    assert result.authorization.lease_identity_valid is False


def test_bound_authority_reconstructs_payloads_and_rejects_forged_private_shells() -> None:
    values = _binding_inputs()
    valid = _BoundTransitionAuthority(
        current_record=values["current_record"],  # type: ignore[arg-type]
        standing_lease=values["standing_lease"],  # type: ignore[arg-type]
        lease_identity=values["lease_identity"],  # type: ignore[arg-type]
        authorization=values["authorization"],  # type: ignore[arg-type]
        dependency=values["dependency"],  # type: ignore[arg-type]
        global_stop=values["global_stop"],  # type: ignore[arg-type]
    )

    assert valid.current_record == values["current_record"]
    assert valid.current_record is not values["current_record"]
    assert valid.standing_lease == values["standing_lease"]
    assert valid.standing_lease is not values["standing_lease"]
    assert valid.lease_identity == values["lease_identity"]
    assert valid.lease_identity is not values["lease_identity"]
    assert valid.authorization == values["authorization"]
    assert valid.authorization is not values["authorization"]
    assert valid.dependency == values["dependency"]
    assert valid.dependency is not values["dependency"]
    assert valid.global_stop == values["global_stop"]
    assert valid.global_stop is not values["global_stop"]

    repr_text = repr(valid)
    assert repr_text == "<_BoundTransitionAuthority>"
    for private_value in (
        "src",
        "tests",
        "coordinator-local",
        "trunk_dev",
        "operator-approved",
        "nwp-coordinator-p1",
        "operator-policy",
        "p1-fail-closed",
        "api_calls",
        "compute_seconds",
    ):
        assert private_value not in repr_text
    for method_name in ("to_dict", "from_dict", "canonical_json", "canonical_digest", "report", "serialize"):
        assert not hasattr(valid, method_name)

    class RecordSubclass(WorkItemRecord):
        pass

    class LeaseSubclass(StandingLease):
        pass

    class IdentitySubclass(LeaseIdentityValidation):
        pass

    class AuthorizationSubclass(AuthorizationDecision):
        pass

    class DependencySubclass(DependencyDecision):
        pass

    class GlobalStopSubclass(GlobalStopState):
        pass

    invalid_by_field = (
        ("current_record", _clone_into(values["current_record"], RecordSubclass)),
        ("standing_lease", _clone_into(values["standing_lease"], LeaseSubclass)),
        ("lease_identity", _clone_into(values["lease_identity"], IdentitySubclass)),
        ("authorization", _clone_into(values["authorization"], AuthorizationSubclass)),
        ("dependency", _clone_into(values["dependency"], DependencySubclass)),
        ("global_stop", _clone_into(values["global_stop"], GlobalStopSubclass)),
        ("current_record", object.__new__(WorkItemRecord)),
        ("standing_lease", object.__new__(StandingLease)),
        ("lease_identity", object.__new__(LeaseIdentityValidation)),
        ("authorization", object.__new__(AuthorizationDecision)),
        ("dependency", object.__new__(DependencyDecision)),
        ("global_stop", object.__new__(GlobalStopState)),
        ("current_record", _forged_from_model(values["current_record"], work_item_id=_HostileValue())),
        ("standing_lease", _forged_from_model(values["standing_lease"], lease_id=_HostileValue())),
        (
            "lease_identity",
            _forged_from_model(
                values["lease_identity"],
                decision_ref=_HostileValue(),
                issues=(ValidationIssue(field="schema_id", reason="schema_id_mismatch"),),
            ),
        ),
        ("authorization", _forged_from_model(values["authorization"], authorization_model=_HostileValue())),
        ("dependency", _forged_from_model(values["dependency"], decision_ref=_HostileValue())),
        (
            "global_stop",
            _forged_exact(
                GlobalStopState,
                schema_id=values["global_stop"].schema_id,  # type: ignore[union-attr]
                version=1,
                active=True,
                stop_id=_HostileValue(),
                reason_class=GlobalStopReasonClass.OPERATOR_STOP,
                issuer_ref="operator-1",
                issued_at="2026-07-14T00:00:01Z",
                operator_decision_ref="operator-decision-1",
            ),
        ),
    )
    for field_name, invalid in invalid_by_field:
        attempted = dict(values)
        attempted[field_name] = invalid
        _assert_integrity_failure(
            lambda attempted=attempted: _BoundTransitionAuthority(
                current_record=attempted["current_record"],  # type: ignore[arg-type]
                standing_lease=attempted["standing_lease"],  # type: ignore[arg-type]
                lease_identity=attempted["lease_identity"],  # type: ignore[arg-type]
                authorization=attempted["authorization"],  # type: ignore[arg-type]
                dependency=attempted["dependency"],  # type: ignore[arg-type]
                global_stop=attempted["global_stop"],  # type: ignore[arg-type]
            )
        )


def test_private_wrappers_are_slots_only_and_cannot_carry_instance_dictionary_shadows() -> None:
    values = _binding_inputs()
    accepted = _accepted_evaluation()
    bound = _BoundTransitionAuthority(
        current_record=values["current_record"],  # type: ignore[arg-type]
        standing_lease=values["standing_lease"],  # type: ignore[arg-type]
        lease_identity=values["lease_identity"],  # type: ignore[arg-type]
        authorization=values["authorization"],  # type: ignore[arg-type]
        dependency=values["dependency"],  # type: ignore[arg-type]
        global_stop=values["global_stop"],  # type: ignore[arg-type]
    )
    result = _RollbackOnlyTransitionDryRunResult(
        _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED,
        evaluation=accepted,
    )

    for wrapper in (bound, result):
        assert not hasattr(wrapper, "__dict__")
        with pytest.raises(AttributeError):
            object.__setattr__(wrapper, "to_dict", lambda: PRIVATE_SENTINEL)

    for _name, valid_model, _reconstructor, _required_field in _candidate_reconstruction_cases():
        shell = object.__new__(type(valid_model))
        assert type(object.__getattribute__(shell, "__dict__")) is dict
        with pytest.raises(TypeError):
            object.__setattr__(shell, "__dict__", [])


def test_bound_authority_classifies_lease_backlog_current_contradictions_as_integrity() -> None:
    values = _binding_inputs()
    changed_record = replace(values["current_record"], backlog_id="backlog-other")  # type: ignore[arg-type]

    _assert_integrity_failure(
        lambda: _bind_b3c3_transition_authority(
            **{**values, "current_record": changed_record},  # type: ignore[arg-type]
        )
    )

    mismatched_command = _reissued_command(values["command"], work_item_id="wi-other")  # type: ignore[arg-type]
    _assert_integrity_failure(
        lambda: _bind_b3c3_transition_authority(
            **{**values, "command": mismatched_command, "current_record": changed_record},  # type: ignore[arg-type]
        )
    )


def test_binding_helper_rejects_forged_exact_inputs_without_raw_attribute_leakage() -> None:
    values = _binding_inputs()
    forged_inputs = (
        ("command", object.__new__(TransitionCommand)),
        ("command", _unchecked_command(values["command"], work_item_id=_HostileValue())),  # type: ignore[arg-type]
        ("current_record", object.__new__(WorkItemRecord)),
        ("current_record", _forged_from_model(values["current_record"], state=_HostileValue())),
        ("standing_lease", object.__new__(StandingLease)),
        ("standing_lease", _forged_from_model(values["standing_lease"], revocation_state=_HostileValue())),
        ("admitted_backlog", object.__new__(FiniteBacklog)),
        ("admitted_backlog", _forged_from_model(values["admitted_backlog"], work_items=(_HostileValue(),))),
        ("lease_identity", object.__new__(LeaseIdentityValidation)),
        (
            "lease_identity",
            _forged_from_model(
                values["lease_identity"],
                issues=(_HostileValue(),),
            ),
        ),
        ("authorization", object.__new__(AuthorizationDecision)),
        ("authorization", _forged_from_model(values["authorization"], authorization_model=_HostileValue())),
        ("dependency", object.__new__(DependencyDecision)),
        ("dependency", _forged_from_model(values["dependency"], decision_ref=_HostileValue())),
        ("global_stop", object.__new__(GlobalStopState)),
        ("global_stop", _forged_from_model(values["global_stop"], active=_HostileValue())),
    )
    for field_name, forged in forged_inputs:
        attempted = {**values, field_name: forged}
        _assert_integrity_failure(
            lambda attempted=attempted: _bind_b3c3_transition_authority(**attempted)  # type: ignore[arg-type]
        )


def test_bound_authority_command_ref_mismatches_are_validation_conflicts() -> None:
    values = _binding_inputs()
    command = values["command"]
    identity_mismatch = _reissued_command(command, lease_identity_decision_ref="lease-identity-other")  # type: ignore[arg-type]
    authorization_mismatch = _reissued_command(command, authorization_decision_ref="authz-other")  # type: ignore[arg-type]

    _assert_validation_conflict(
        _bind_b3c3_transition_authority(
            **{**values, "command": identity_mismatch},  # type: ignore[arg-type]
        )
    )
    _assert_validation_conflict(
        _bind_b3c3_transition_authority(
            **{**values, "command": authorization_mismatch},  # type: ignore[arg-type]
        )
    )

    digest_mismatch = _unchecked_command(command, lease_identity_decision_ref="lease-identity-other")  # type: ignore[arg-type]
    _assert_integrity_failure(
        lambda: _bind_b3c3_transition_authority(
            **{**values, "command": digest_mismatch},  # type: ignore[arg-type]
        )
    )


def test_bound_authority_authorization_model_and_receipt_binding_classification() -> None:
    operator_policy_values = _binding_inputs(
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorization_authorized=True,
        authorization_reason="accepted",
    )
    _assert_validation_conflict(_bind_b3c3_transition_authority(**operator_policy_values))  # type: ignore[arg-type]

    unsupported_values = _binding_inputs()
    unsupported_result = _bind_b3c3_transition_authority(**unsupported_values)  # type: ignore[arg-type]
    assert type(unsupported_result) is _BoundTransitionAuthority

    contradicted_auth = replace(unsupported_values["authorization"], lease_ref="lease-other")  # type: ignore[arg-type]
    _assert_integrity_failure(
        lambda: _bind_b3c3_transition_authority(
            **{**unsupported_values, "authorization": contradicted_auth},  # type: ignore[arg-type]
        )
    )


def test_bound_authority_ready_dependency_false_passes_and_ready_mismatches_conflict() -> None:
    false_dependency = DependencyDecision(
        decision_ref="deps-ready",
        work_item_id="wi-1",
        dependencies_satisfied=False,
        reason="dependencies_not_satisfied",
    )
    values = _binding_inputs(target_state=WorkItemState.READY, dependency=false_dependency)
    result = _bind_b3c3_transition_authority(**values)  # type: ignore[arg-type]
    assert type(result) is _BoundTransitionAuthority
    assert result.dependency.dependencies_satisfied is False

    wrong_ref = replace(false_dependency, decision_ref="deps-other")
    _assert_validation_conflict(
        _bind_b3c3_transition_authority(
            **{**values, "dependency": wrong_ref},  # type: ignore[arg-type]
        )
    )
    wrong_work_item = replace(false_dependency, work_item_id="wi-other")
    _assert_validation_conflict(
        _bind_b3c3_transition_authority(
            **{**values, "dependency": wrong_work_item},  # type: ignore[arg-type]
        )
    )


def test_bound_authority_non_ready_requires_neutral_dependency() -> None:
    values = _binding_inputs()
    result = _bind_b3c3_transition_authority(**values)  # type: ignore[arg-type]
    assert type(result) is _BoundTransitionAuthority
    assert result.dependency == DependencyDecision()

    non_neutral = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    _assert_validation_conflict(
        _bind_b3c3_transition_authority(
            **{**values, "dependency": non_neutral},  # type: ignore[arg-type]
        )
    )


def test_bound_authority_global_stop_ref_and_version_are_command_bound() -> None:
    stop = GlobalStopState(
        version=1,
        active=True,
        stop_id="stop-active",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-1",
        issued_at="2026-07-14T00:00:01Z",
        operator_decision_ref="operator-decision-1",
    )
    values = _binding_inputs(global_stop=stop)
    result = _bind_b3c3_transition_authority(**values)  # type: ignore[arg-type]
    assert type(result) is _BoundTransitionAuthority
    assert result.global_stop == stop
    assert result.global_stop is not stop

    command = _reissued_command(values["command"], global_stop_version=0)  # type: ignore[arg-type]
    _assert_validation_conflict(
        _bind_b3c3_transition_authority(
            **{**values, "command": command},  # type: ignore[arg-type]
        )
    )


def test_dry_run_contract_module_has_static_private_no_io_boundary() -> None:
    source = DRY_RUN_MODULE_PATH.read_text(encoding="utf-8")
    imported_modules = {
        alias.name
        for node in __import__("ast").walk(__import__("ast").parse(source))
        if isinstance(node, __import__("ast").Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in __import__("ast").walk(__import__("ast").parse(source))
        if isinstance(node, __import__("ast").ImportFrom) and node.module is not None
    }

    assert "sqlite3" not in imported_modules
    assert "ge_nwp_coordinator.sqlite_transition_transaction" not in imported_from
    for forbidden in (
        "open(",
        "Path(",
        "socket",
        "requests",
        "urllib",
        "subprocess",
        "_read_transition_event_for_idempotency",
        "_read_transition_event_max_sequence",
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_admitted_backlog",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_global_stop_current",
        "TransitionContext",
        "derive_lease_runtime_decision",
        "evaluate_transition",
        "next_transition_event_sequence",
        "INSERT",
        "UPDATE",
        "DELETE",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "value.to_dict(",
        "command.compute_digest(",
        "type(value).to_dict",
        "getattr(",
    ):
        assert forbidden not in source


def test_candidate_state_snapshot_validates_raw_keys_before_trusted_lookup() -> None:
    snapshot_source = inspect.getsource(dry_run_contracts._candidate_state_snapshot)

    raw_items_index = snapshot_source.index("raw_items = tuple(dict.items(raw_state))")
    key_gate_index = snapshot_source.index("for key, _field_value in raw_items:")
    trusted_state_index = snapshot_source.index(
        "trusted_state = {key: field_value for key, field_value in raw_items}"
    )
    required_lookup_index = snapshot_source.index("model_field.name not in trusted_state")

    assert raw_items_index < key_gate_index < trusted_state_index < required_lookup_index
    assert "type(key) is not str" in snapshot_source
    for forbidden in (
        "model_field.name not in raw_state",
        "raw_state[",
        "raw_state.get",
        "set(raw_state)",
        "frozenset(raw_state)",
        "sorted(raw_state)",
        "dict(raw_state)",
        "raw_state ==",
    ):
        assert forbidden not in snapshot_source


def test_b3c3_runtime_entrypoint_remains_private_and_unexported() -> None:
    package_source = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
    transaction_source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    writer_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")

    for name in (
        "sqlite_transition_dry_run_contracts",
        "_RollbackOnlyTransitionDryRunResult",
        "_BoundTransitionAuthority",
        "_validate_transition_dry_run_preflight",
        "_bind_b3c3_transition_authority",
    ):
        assert name not in ge_nwp_coordinator.__all__
        assert name not in package_source

    for name in (
        "_RollbackOnlyTransitionDryRunResult",
        "_BoundTransitionAuthority",
        "_validate_transition_dry_run_preflight",
        "_bind_b3c3_transition_authority",
        "_run_rollback_only_transition_dry_run",
        "_utc_transaction_timestamp",
    ):
        assert not hasattr(ge_nwp_coordinator, name)

    assert hasattr(transaction_module, "_run_rollback_only_transition_dry_run")
    assert hasattr(transaction_module, "_utc_transaction_timestamp")
    assert "_run_rollback_only_transition_dry_run" in transaction_source
    assert "_utc_transaction_timestamp" in transaction_source
    assert "_validate_transition_dry_run_preflight" in transaction_source
    assert "_bind_b3c3_transition_authority" in transaction_source
    assert "_run_rollback_only_transition_dry_run" not in package_source
    assert "_run_rollback_only_transition_dry_run" not in writer_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in writer_source
    assert WriterSessionFailureReason.WRITER_SESSION_MUTATION_UNAVAILABLE.value == "writer_session_mutation_unavailable"


def test_b3c3_runtime_integrates_readers_context_and_evaluator_without_b3c4_mutation() -> None:
    transaction_source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    dry_run_source = "\n".join(
        (
            inspect.getsource(transaction_module._run_rollback_only_transition_dry_run),
            inspect.getsource(transaction_module._CoordinatorMutationTransactionController._run_transition_dry_run_transaction),
            inspect.getsource(transaction_module._CoordinatorMutationTransactionController._run_until_transition_resolution),
            inspect.getsource(transaction_module._evaluate_bound_transition),
            inspect.getsource(transaction_module._dry_run_result_from_transition_resolution),
        )
    )
    for required in (
        "_read_transition_event_for_idempotency",
        "match_transition_event_idempotency",
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_admitted_backlog",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_global_stop_current",
        "TransitionContext",
        "derive_lease_runtime_decision",
        "evaluate_transition",
    ):
        assert required in dry_run_source

    for forbidden in (
        "_read_transition_event_max_sequence",
        "next_transition_event_sequence",
        "_transition_write_plan",
        "_execute_transition_event_insert",
        "_execute_accepted_work_item_cas",
        "INSERT INTO transition_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
        ".commit(",
        "COMMIT",
    ):
        assert forbidden not in dry_run_source

    assert "_run_atomic_transition_apply" in transaction_source
    assert "_read_transition_event_max_sequence" in transaction_source


def test_b3c3_prerequisite_docs_and_schema_boundary_are_pinned() -> None:
    doc = (ROOT / ".docs/b3c3-prerequisite-contract.md").read_text(encoding="utf-8")
    normalized = " ".join(doc.split())
    for phrase in (
        "Status: private prerequisite contracts plus implemented rollback-only transition dry-run runtime",
        "_run_rollback_only_writer_fencing",
        "_run_rollback_only_transition_dry_run",
        "one controller class and one capability-construction path",
        "no callback, observer, raw connection, second controller, second capability, or generic mode",
        "stale writer before idempotency disclosure",
        "fresh evaluator output is non-durable",
        "_utc_transaction_timestamp() -> str",
        "B3c4b is the first private persistence/commit tranche",
        "No sequence read or allocation occurs in B3c3",
        "No writes, CAS, or COMMIT occur in B3c3",
        "preflight error constructor accepts only the exact private reason enum",
        "Exact type alone is not authority for this private boundary",
        "reconstructs command and persisted model inputs through model-owned pure validation",
        "Candidate validation and serialization methods are never dispatched through the candidate instance",
        "Instance-level method shadowing",
        "cannot substitute clean data for malformed real fields",
        "simultaneous persisted contradiction and command mismatch is an integrity failure",
        "Result payloads are reconstructed through model-owned pure validation",
        "trusted class-owned reconstruction rather than candidate instance method dispatch",
        "never retains forged exact shells",
    ):
        assert phrase in normalized

    migration = PACKAGE_DIR / "sqlite_migrations/0001_initial.sql"
    assert hashlib.sha256(migration.read_bytes()).hexdigest() == EXPECTED_MIGRATION_0001_CHECKSUM
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
    ]


def test_b3c3_private_contract_signatures_are_exact() -> None:
    preflight_signature = inspect.signature(_validate_transition_dry_run_preflight)
    assert list(preflight_signature.parameters) == ["command"]
    assert str(preflight_signature.return_annotation) == "TransitionCommand"

    binding_signature = inspect.signature(_bind_b3c3_transition_authority)
    assert list(binding_signature.parameters) == [
        "command",
        "current_record",
        "standing_lease",
        "admitted_backlog",
        "lease_identity",
        "authorization",
        "dependency",
        "global_stop",
    ]
    assert str(binding_signature.return_annotation) == "_BoundTransitionAuthority | TransitionConflict"

    assert [field.name for field in fields(_BoundTransitionAuthority)] == [
        "current_record",
        "standing_lease",
        "lease_identity",
        "authorization",
        "dependency",
        "global_stop",
    ]
    assert [field.name for field in fields(_RollbackOnlyTransitionDryRunResult)] == [
        "kind",
        "replayed_transition",
        "conflict",
        "evaluation",
    ]
