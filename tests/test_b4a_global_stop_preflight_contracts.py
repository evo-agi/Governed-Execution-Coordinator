from __future__ import annotations

from enum import Enum
import inspect
from pathlib import Path

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
)
from ge_nwp_coordinator.persistence_contracts import GlobalStopOperatorDecisionReceiptEnvelope
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_global_stop_preflight_contracts import (
    _GlobalStopApplyPreflightError,
    _GlobalStopApplyPreflightFailureReason,
    _GlobalStopApplyPreflightResult,
    _bind_global_stop_operator_decision_receipt,
    _validate_global_stop_apply_preflight,
)
from ge_nwp_coordinator.state_store import (
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    GlobalStopConflict,
    GlobalStopApplyOutcome,
    WriterSession,
)


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_SENTINEL = "PRIVATE-B4A-PREFLIGHT-SENTINEL"


class _OtherReason(str, Enum):
    INVALID_COMMAND = "global_stop_apply_invalid_command"


class _HostileInput:
    def __str__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)

    def __repr__(self) -> str:
        raise AssertionError(PRIVATE_SENTINEL)


def _command(*, decision_ref: str = "operator-decision-1", key: str = "global-stop-key-1") -> GlobalStopCommand:
    return GlobalStopCommand.create(
        action=GlobalStopAction.ACTIVATE,
        idempotency_key=key,
        expected_version=0,
        stop_id="global-stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-22T12:00:00Z",
        operator_decision_ref=decision_ref,
    )


def _decision(*, ref: str = "operator-decision-1", authorized: bool = True) -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref=ref,
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _receipt(decision: GlobalStopOperatorDecision) -> GlobalStopOperatorDecisionReceiptEnvelope:
    return GlobalStopOperatorDecisionReceiptEnvelope(decision=decision, created_at="2026-07-22T12:00:01Z")


def _forged_command(**overrides: object) -> GlobalStopCommand:
    command = _command()
    forged = object.__new__(GlobalStopCommand)
    for key, value in command.__dict__.items():
        object.__setattr__(forged, key, value)
    for key, value in overrides.items():
        object.__setattr__(forged, key, value)
    return forged


def _assert_public_preflight_error(
    error: GlobalStopApplyPreflightError,
    reason: GlobalStopApplyPreflightFailureReason,
) -> None:
    assert type(error) is GlobalStopApplyPreflightError
    assert error.reason is reason
    assert str(error) == reason.value
    assert error.args == (reason.value,)
    assert repr(error) == "<GlobalStopApplyPreflightError>"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not getattr(error, "__notes__", ())


def test_public_global_stop_preflight_vocabulary_is_exact_and_exported() -> None:
    assert [reason.name for reason in GlobalStopApplyPreflightFailureReason] == [
        "INVALID_COMMAND",
        "INVALID_OPERATOR_DECISION",
    ]
    assert GlobalStopApplyPreflightFailureReason.INVALID_COMMAND.value == "global_stop_apply_invalid_command"
    assert (
        GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION.value
        == "global_stop_apply_invalid_operator_decision"
    )

    _assert_public_preflight_error(
        GlobalStopApplyPreflightError(GlobalStopApplyPreflightFailureReason.INVALID_COMMAND),
        GlobalStopApplyPreflightFailureReason.INVALID_COMMAND,
    )
    for invalid in (
        "global_stop_apply_invalid_command",
        _OtherReason.INVALID_COMMAND,
        _HostileInput(),
        object(),
        None,
    ):
        with pytest.raises(ValueError) as exc_info:
            GlobalStopApplyPreflightError(invalid)  # type: ignore[arg-type]
        assert exc_info.value.args == ("invalid_field_type:global_stop_apply_preflight.reason",)

    assert ge_nwp_coordinator.GlobalStopApplyPreflightError is GlobalStopApplyPreflightError
    assert ge_nwp_coordinator.GlobalStopApplyPreflightFailureReason is GlobalStopApplyPreflightFailureReason
    assert "GlobalStopApplyPreflightError" in ge_nwp_coordinator.__all__
    assert "GlobalStopApplyPreflightFailureReason" in ge_nwp_coordinator.__all__
    assert GlobalStopApplyPreflightError not in getattr(GlobalStopApplyOutcome, "__args__", ())


def test_private_preflight_reconstructs_safe_command_and_decision() -> None:
    command = _command()
    decision = _decision()
    result = _validate_global_stop_apply_preflight(command, decision)

    assert type(result) is _GlobalStopApplyPreflightResult
    assert result.command == command
    assert result.command is not command
    assert result.typed_operator_decision == decision
    assert result.typed_operator_decision is not decision
    assert repr(result) == "<_GlobalStopApplyPreflightResult>"


def test_private_preflight_rejects_hostile_subclass_and_forged_shells_safely() -> None:
    class CommandSubclass(GlobalStopCommand):
        pass

    with pytest.raises(_GlobalStopApplyPreflightError) as invalid_command:
        _validate_global_stop_apply_preflight(CommandSubclass(**_command().__dict__), _decision())
    assert invalid_command.value.reason is _GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
    assert invalid_command.value.__cause__ is None
    assert invalid_command.value.__context__ is None

    with pytest.raises(_GlobalStopApplyPreflightError) as forged_command:
        _validate_global_stop_apply_preflight(
            _forged_command(canonical_command_digest="0" * 64),
            _decision(),
        )
    assert forged_command.value.reason is _GlobalStopApplyPreflightFailureReason.INVALID_COMMAND

    forged_decision = object.__new__(GlobalStopOperatorDecision)
    object.__setattr__(forged_decision, "schema_id", "governed-execution.nwp-global-stop-operator-decision.v1")
    object.__setattr__(forged_decision, "decision_ref", "operator-decision-1")
    object.__setattr__(forged_decision, "authorized", True)
    object.__setattr__(forged_decision, "reason", "operator_authorization_required")
    with pytest.raises(_GlobalStopApplyPreflightError) as invalid_decision:
        _validate_global_stop_apply_preflight(_command(), forged_decision)
    assert invalid_decision.value.reason is _GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION


def test_receipt_binding_taxonomy_never_uses_caller_decision_as_authority() -> None:
    authorized = _decision()
    unauthorized = _decision(authorized=False)

    assert _bind_global_stop_operator_decision_receipt(
        command=_command(),
        typed_operator_decision=authorized,
        receipt=_receipt(authorized),
    ) == authorized
    assert _bind_global_stop_operator_decision_receipt(
        command=_command(),
        typed_operator_decision=unauthorized,
        receipt=_receipt(unauthorized),
    ) == unauthorized

    missing = _bind_global_stop_operator_decision_receipt(
        command=_command(),
        typed_operator_decision=authorized,
        receipt=None,
    )
    assert type(missing) is GlobalStopConflict
    assert missing.conflict_class == "validation_failed"

    caller_mismatch = _bind_global_stop_operator_decision_receipt(
        command=_command(),
        typed_operator_decision=unauthorized,
        receipt=_receipt(authorized),
    )
    assert type(caller_mismatch) is GlobalStopConflict
    assert caller_mismatch.conflict_class == "validation_failed"

    command_mismatch = _bind_global_stop_operator_decision_receipt(
        command=_command(decision_ref="other-decision"),
        typed_operator_decision=authorized,
        receipt=_receipt(authorized),
    )
    assert type(command_mismatch) is GlobalStopConflict
    assert command_mismatch.conflict_class == "validation_failed"

    malformed_receipt = object.__new__(GlobalStopOperatorDecisionReceiptEnvelope)
    object.__setattr__(malformed_receipt, "decision", object())
    object.__setattr__(malformed_receipt, "created_at", "2026-07-22T12:00:01Z")
    with pytest.raises(SQLiteMutationStoreError) as malformed:
        _bind_global_stop_operator_decision_receipt(
            command=_command(decision_ref="other-decision"),
            typed_operator_decision=authorized,
            receipt=malformed_receipt,
        )
    assert malformed.value.error_class == "database_integrity_failure"


def test_public_method_signature_is_unchanged_and_b4c_adapter_owns_mapping() -> None:
    assert list(inspect.signature(WriterSession.apply_global_stop_update).parameters) == [
        "self",
        "global_stop_command",
        "typed_operator_decision",
    ]
    writer_source = (ROOT / "src/ge_nwp_coordinator/sqlite_writer_session.py").read_text(encoding="utf-8")
    assert "_run_atomic_global_stop_apply" in writer_source
    assert "GlobalStopApplyPreflightError" in writer_source
