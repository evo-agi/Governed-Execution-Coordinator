"""Private pure B4a global-stop apply preflight and receipt binding contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Callable, TypeVar

from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
)
from ge_nwp_coordinator.persistence_contracts import GlobalStopOperatorDecisionReceiptEnvelope
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator.state_store import GlobalStopConflict

_T = TypeVar("_T")


class _GlobalStopApplyPreflightFailureReason(str, Enum):
    INVALID_COMMAND = "global_stop_apply_preflight_invalid_command"
    INVALID_OPERATOR_DECISION = "global_stop_apply_preflight_invalid_operator_decision"


class _GlobalStopApplyPreflightError(RuntimeError):
    """Safe private command-local global-stop preflight failure."""

    __slots__ = ("reason",)

    def __init__(self, reason: _GlobalStopApplyPreflightFailureReason) -> None:
        if type(reason) is not _GlobalStopApplyPreflightFailureReason:
            raise ValueError("invalid_field_type:global_stop_apply_preflight.reason") from None
        self.reason = reason
        super().__init__(reason.value)

    def __repr__(self) -> str:
        return "<_GlobalStopApplyPreflightError>"


@dataclass(frozen=True, slots=True, repr=False)
class _GlobalStopApplyPreflightResult:
    command: GlobalStopCommand = field(repr=False)
    typed_operator_decision: GlobalStopOperatorDecision = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "command", _require_initialized_global_stop_command(self.command))
        object.__setattr__(
            self,
            "typed_operator_decision",
            _require_initialized_global_stop_operator_decision(self.typed_operator_decision),
        )

    def __repr__(self) -> str:
        return "<_GlobalStopApplyPreflightResult>"


_GLOBAL_STOP_PUBLIC_PREFLIGHT_MAPPING_CONTRACT = (
    (
        _GlobalStopApplyPreflightFailureReason.INVALID_COMMAND.value,
        "GlobalStopApplyPreflightFailureReason.INVALID_COMMAND",
    ),
    (
        _GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION.value,
        "GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION",
    ),
    ("malformed_private_preflight_object_or_reason", "database_integrity_failure"),
    ("import_or_load_failure_before_delegate_invocation", "mutation_failed"),
    ("delegate_exceptions", "no_generic_delegate_catch_all"),
)


def _validate_global_stop_apply_preflight(
    command: GlobalStopCommand,
    typed_operator_decision: GlobalStopOperatorDecision,
) -> _GlobalStopApplyPreflightResult:
    invalid_command = False
    try:
        safe_command = _require_initialized_global_stop_command(command)
    except Exception:
        invalid_command = True
    if invalid_command:
        raise _GlobalStopApplyPreflightError(_GlobalStopApplyPreflightFailureReason.INVALID_COMMAND) from None
    invalid_decision = False
    try:
        safe_decision = _require_initialized_global_stop_operator_decision(typed_operator_decision)
    except Exception:
        invalid_decision = True
    if invalid_decision:
        raise _GlobalStopApplyPreflightError(_GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION) from None
    return _GlobalStopApplyPreflightResult(command=safe_command, typed_operator_decision=safe_decision)


def _bind_global_stop_operator_decision_receipt(
    *,
    command: GlobalStopCommand,
    typed_operator_decision: GlobalStopOperatorDecision,
    receipt: GlobalStopOperatorDecisionReceiptEnvelope | None,
) -> GlobalStopOperatorDecision | GlobalStopConflict:
    def bind() -> GlobalStopOperatorDecision | GlobalStopConflict:
        if receipt is None:
            return _validation_failed()
        if type(receipt) is not GlobalStopOperatorDecisionReceiptEnvelope:
            raise ValueError("invalid_receipt")
        persisted_decision = _require_initialized_global_stop_operator_decision(receipt.decision)
        safe_command = _require_initialized_global_stop_command(command)
        safe_typed_decision = _require_initialized_global_stop_operator_decision(typed_operator_decision)
        if safe_command.operator_decision_ref != persisted_decision.decision_ref:
            return _validation_failed()
        if safe_typed_decision.decision_ref != safe_command.operator_decision_ref:
            return _validation_failed()
        if safe_typed_decision.authorized != persisted_decision.authorized:
            return _validation_failed()
        if safe_typed_decision.reason != persisted_decision.reason:
            return _validation_failed()
        if safe_typed_decision.schema_id != persisted_decision.schema_id:
            return _validation_failed()
        return persisted_decision

    return _collapse_private_contract_failure(bind)


def _require_initialized_global_stop_command(value: object) -> GlobalStopCommand:
    state = _candidate_state_snapshot(value, GlobalStopCommand)

    def reconstruct() -> GlobalStopCommand:
        action = _field(state, "action")
        reason_class = _field(state, "reason_class")
        if type(action) is not GlobalStopAction:
            raise ValueError("invalid_action")
        if type(reason_class) is not GlobalStopReasonClass:
            raise ValueError("invalid_reason_class")
        return GlobalStopCommand(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            action=action,
            idempotency_key=_require_exact_str(_field(state, "idempotency_key")),
            expected_version=_require_exact_int(_field(state, "expected_version")),
            source_stop_id=_require_optional_exact_str(_field(state, "source_stop_id")),
            stop_id=_require_exact_str(_field(state, "stop_id")),
            reason_class=reason_class,
            issuer_ref=_require_exact_str(_field(state, "issuer_ref")),
            issued_at=_require_exact_str(_field(state, "issued_at")),
            operator_decision_ref=_require_exact_str(_field(state, "operator_decision_ref")),
            canonical_command_digest=_require_exact_str(_field(state, "canonical_command_digest")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _require_initialized_global_stop_operator_decision(value: object) -> GlobalStopOperatorDecision:
    state = _candidate_state_snapshot(value, GlobalStopOperatorDecision)

    def reconstruct() -> GlobalStopOperatorDecision:
        return GlobalStopOperatorDecision(
            schema_id=_require_exact_str(_field(state, "schema_id")),
            decision_ref=_require_exact_str(_field(state, "decision_ref")),
            authorized=_require_exact_bool(_field(state, "authorized")),
            reason=_require_exact_str(_field(state, "reason")),
        )

    return _collapse_private_contract_failure(reconstruct)


def _candidate_state_snapshot(value: object, expected: type[object]) -> dict[str, object]:
    if type(value) is not expected:
        raise _database_integrity_failure()
    failed = False
    try:
        raw_state = object.__getattribute__(value, "__dict__")
        expected_fields = fields(expected)
    except Exception:
        failed = True
    if failed or type(raw_state) is not dict:
        raise _database_integrity_failure()
    failed = False
    try:
        raw_items = tuple(dict.items(raw_state))
    except Exception:
        failed = True
    if failed:
        raise _database_integrity_failure()
    for key, _field_value in raw_items:
        if type(key) is not str:
            raise _database_integrity_failure()
    trusted_state = {key: field_value for key, field_value in raw_items}
    for model_field in expected_fields:
        if model_field.name not in trusted_state:
            raise _database_integrity_failure()
    return trusted_state


def _field(state: dict[str, object], name: str) -> object:
    return state[name]


def _require_exact_str(value: object) -> str:
    if type(value) is not str:
        raise ValueError("invalid_string")
    return value


def _require_optional_exact_str(value: object) -> str | None:
    if value is None:
        return None
    return _require_exact_str(value)


def _require_exact_bool(value: object) -> bool:
    if type(value) is not bool:
        raise ValueError("invalid_bool")
    return value


def _require_exact_int(value: object) -> int:
    if type(value) is not int:
        raise ValueError("invalid_int")
    return value


def _validation_failed() -> GlobalStopConflict:
    return GlobalStopConflict("validation_failed")


def _collapse_private_contract_failure(callback: Callable[[], _T]) -> _T:
    ordinary_failure = False
    try:
        return callback()
    except SQLiteMutationStoreError:
        raise
    except Exception:
        ordinary_failure = True
    if ordinary_failure:
        raise _database_integrity_failure()
    raise _database_integrity_failure()


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)
