"""State-store port only.

A2-P1 intentionally provides no production implementation. Future stores must
provide one active authoritative writer, ownership generation, stale-writer
fencing, split-brain prevention, transactional current-state/counter updates,
crash consistency, migrations, restart reconciliation, corruption detection,
backup/restore, and persistent global stop.
"""

from __future__ import annotations

from typing import Protocol

from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator.models import Decision
from ge_nwp_coordinator.state_machine import TransitionReceipt, TransitionRequest, WorkItemRecord


class StateStore(Protocol):
    def read_current(self, work_item_id: str) -> WorkItemRecord | None:
        """Read the current record for a work item."""

    def compare_and_set_transition(
        self,
        current: WorkItemRecord,
        request: TransitionRequest,
        next_record: WorkItemRecord,
    ) -> Decision:
        """Atomically install a transition result if the expected record still matches."""

    def append_transition_receipt(self, receipt: TransitionReceipt) -> Decision:
        """Append immutable transition receipt evidence to the store audit trail."""

    def read_global_stop(self) -> GlobalStopState:
        """Read the authoritative global-stop projection."""

    def submit_operator_authorized_global_stop_update(self, state: GlobalStopState) -> Decision:
        """Submit an operator-authorized global-stop update to the future store."""
