from __future__ import annotations

import pytest

from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator._rw0_d1_workspace import PATHS
from test_rw0_d1_offline_integration import work_spec


def test_worker_decodes_existing_wire_and_changes_one_authorized_file() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        assert handback.status == "capsule_ready"
        assert handback.wire_result is not None
        assert handback.wire_classification.classification == "usable"
        assert handback.capture.changed_path == PATHS[2]
        assert handback.capture.entries[0].before == handback.capture.entries[0].after
        assert handback.capture.entries[1].before == handback.capture.entries[1].after
        assert handback.capture.entries[2].before != handback.capture.entries[2].after
        assert handback.worker_process.pid != handback.planner_process.pid


@pytest.mark.parametrize("behavior", (
    "missing_candidate", "extra_path", "unsafe_path", "malformed", "nonzero",
))
def test_worker_faults_never_return_capsule(behavior: str) -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work, worker_behavior=behavior)) as run:
        assert run.handback.status == "stopped"
        assert run.handback.capsule_manifest is None
        assert run.handback.worker_process.cleanup_complete
        if behavior in {"missing_candidate", "extra_path", "unsafe_path"}:
            assert run.handback.adapter_exit is not None
            assert run.handback.wire_result is not None
        else:
            assert run.handback.adapter_exit is None
