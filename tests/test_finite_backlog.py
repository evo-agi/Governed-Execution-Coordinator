from dataclasses import FrozenInstanceError

import pytest

from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, FiniteBacklog, WorkItem


def _items() -> tuple[WorkItem, WorkItem]:
    first = WorkItem(
        work_item_id="wi-1",
        objective_label="first finite item",
        opaque_private_assignment_ref="private-ref-1",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src", "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": 0, "compute_seconds": 0},
        dependencies=(),
        stop_conditions=("global-stop",),
    )
    second = WorkItem(
        work_item_id="wi-2",
        objective_label="second finite item",
        opaque_private_assignment_ref="private-ref-2",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src",),
        task_class="docs",
        risk_lane="low",
        required_validation_profile="docs-tests",
        budget_allocation={"api_calls": 0, "compute_seconds": 0},
        dependencies=("wi-1",),
        stop_conditions=("global-stop",),
    )
    return first, second


def _backlog() -> FiniteBacklog:
    backlog = FiniteBacklog(
        schema_id=BACKLOG_SCHEMA_ID,
        schema_version=1,
        backlog_id="backlog-a2-p1",
        lease_reference="lease-a2-p1",
        work_items=_items(),
        content_digest="0" * 64,
    )
    return backlog.with_digest()


def test_canonical_digest_and_deterministic_order() -> None:
    backlog = FiniteBacklog.from_dict(_backlog().to_dict())
    assert backlog.content_digest == backlog.canonical_digest()
    assert backlog.deterministic_order() == ("wi-1", "wi-2")


def test_finite_items_are_immutable_and_do_not_store_private_content() -> None:
    backlog = FiniteBacklog.from_dict(_backlog().to_dict())
    with pytest.raises(FrozenInstanceError):
        backlog.backlog_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        backlog.work_items[0].budget_allocation["api_calls"] = 1  # type: ignore[index]
    assert "private_assignment_content" not in repr(backlog.to_dict())


def test_duplicate_ids_missing_dependencies_and_self_dependency_are_rejected() -> None:
    payload = _backlog().to_dict()
    payload["work_items"][1]["work_item_id"] = "wi-1"
    payload["content_digest"] = "0" * 64
    with pytest.raises(ValueError, match="duplicate"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][1]["dependencies"] = ["missing"]
    payload["content_digest"] = "0" * 64
    with pytest.raises(ValueError, match="missing_dependency"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["dependencies"] = ["wi-1"]
    payload["content_digest"] = "0" * 64
    with pytest.raises(ValueError, match="self_dependency"):
        FiniteBacklog.from_dict(payload)


def test_dependency_cycle_is_rejected() -> None:
    payload = _backlog().to_dict()
    payload["work_items"][0]["dependencies"] = ["wi-2"]
    payload["work_items"][1]["dependencies"] = ["wi-1"]
    payload["content_digest"] = "0" * 64
    with pytest.raises(ValueError, match="dependency_cycle"):
        FiniteBacklog.from_dict(payload)


def test_no_self_expansion_or_private_brief_fields() -> None:
    payload = _backlog().to_dict()
    payload["dynamic_discovery"] = True
    with pytest.raises(ValueError, match="forbidden fields"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["private_brief"] = "not public state"
    with pytest.raises(ValueError, match="forbidden fields"):
        FiniteBacklog.from_dict(payload)


def test_content_digest_mismatch_rejected() -> None:
    payload = _backlog().to_dict()
    payload["work_items"][0]["objective_label"] = "changed"
    with pytest.raises(ValueError, match="content_digest_mismatch"):
        FiniteBacklog.from_dict(payload)
