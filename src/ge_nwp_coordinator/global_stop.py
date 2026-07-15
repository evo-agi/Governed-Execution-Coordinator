"""Operator-owned global stop models and pure enforcement checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ge_nwp_coordinator.models import Decision, DecisionStatus

GLOBAL_STOP_SCHEMA_ID = "governed-execution.nwp-global-stop.v1"


class GlobalStopTransitionClass(str, Enum):
    LEASE_ADMISSION = "lease_admission"
    READY = "ready"
    CYCLE_START = "cycle_start"
    RETRY = "retry"
    REPAIR = "repair"
    COMMIT_ELIGIBILITY = "commit_eligibility"


@dataclass(frozen=True)
class GlobalStopState:
    schema_id: str = GLOBAL_STOP_SCHEMA_ID
    active: bool = False
    stop_id: str | None = None
    reason: str | None = None
    issued_by: str | None = None
    issued_at: str | None = None

    def to_report_dict(self) -> dict[str, str | bool | None]:
        return {
            "schema_id": self.schema_id,
            "active": self.active,
            "stop_id": self.stop_id,
            "status": "active" if self.active else "clear",
        }


def enforce_global_stop(state: GlobalStopState, transition_class: GlobalStopTransitionClass) -> Decision:
    if state.active:
        return Decision(
            status=DecisionStatus.BLOCKED,
            reason=f"global_stop_active:{transition_class.value}",
        )
    return Decision(status=DecisionStatus.ACCEPTED, reason="global_stop_clear")


def coordinator_clear_global_stop(state: GlobalStopState) -> Decision:
    if state.active:
        return Decision(status=DecisionStatus.BLOCKED, reason="coordinator_cannot_clear_global_stop")
    return Decision(status=DecisionStatus.BLOCKED, reason="coordinator_cannot_replace_global_stop")
