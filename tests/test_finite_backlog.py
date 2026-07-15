from dataclasses import FrozenInstanceError
import json

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
    with pytest.raises(ValueError, match="unknown_field:backlog.dynamic_discovery"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["private_brief"] = "not public state"
    with pytest.raises(ValueError, match="unknown_field:work_item.private_brief"):
        FiniteBacklog.from_dict(payload)


def test_content_digest_mismatch_rejected() -> None:
    payload = _backlog().to_dict()
    payload["work_items"][0]["objective_label"] = "changed"
    with pytest.raises(ValueError, match="content_digest_mismatch"):
        FiniteBacklog.from_dict(payload)


def test_closed_world_rejects_unknown_backlog_and_work_item_fields_before_digest() -> None:
    payload = _backlog().to_dict()
    payload["operator_notes"] = "RAW_VALUE_SHOULD_NOT_LEAK"
    with pytest.raises(ValueError, match="unknown_field:backlog.operator_notes") as exc_info:
        FiniteBacklog.from_dict(payload)
    assert "RAW_VALUE" not in str(exc_info.value)

    payload = _backlog().to_dict()
    payload["work_items"][0]["operator_notes"] = "not-part-of-v1"
    with pytest.raises(ValueError, match="unknown_field:work_item.operator_notes"):
        FiniteBacklog.from_dict(payload)


def test_closed_world_rejects_unknown_nested_budget_and_misspelled_fields() -> None:
    payload = _backlog().to_dict()
    payload["work_items"][0]["budget_allocation"]["tokens"] = 1
    with pytest.raises(ValueError, match="unknown_field:budget_allocation.tokens"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["dependency"] = payload["work_items"][0].pop("dependencies")
    with pytest.raises(ValueError, match="unknown_field:work_item.dependency"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["stopCondition"] = payload["work_items"][0].pop("stop_conditions")
    with pytest.raises(ValueError, match="unknown_field:work_item.stopCondition"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["branch"] = payload["work_items"][0].pop("branches")
    with pytest.raises(ValueError, match="unknown_field:work_item.branch"):
        FiniteBacklog.from_dict(payload)


def test_duplicate_json_object_keys_are_rejected_for_backlog_inputs() -> None:
    with pytest.raises(ValueError, match="duplicate_field:work_item_id"):
        FiniteBacklog.from_json('{"work_items":[{"work_item_id":"a","work_item_id":"b"}]}')


def test_unknown_field_cannot_preserve_an_accepted_backlog_digest() -> None:
    clean = _backlog().to_dict()
    dirty = json.loads(json.dumps(clean))
    dirty["metadata"] = {"anything": "not-allowed"}
    assert FiniteBacklog.from_dict(clean).content_digest == clean["content_digest"]
    with pytest.raises(ValueError, match="unknown_field:backlog.metadata"):
        FiniteBacklog.from_dict(dirty)


def test_no_arbitrary_metadata_extensions_or_boolean_integer_budget() -> None:
    payload = _backlog().to_dict()
    payload["extensions"] = {}
    with pytest.raises(ValueError, match="unknown_field:backlog.extensions"):
        FiniteBacklog.from_dict(payload)

    payload = _backlog().to_dict()
    payload["work_items"][0]["budget_allocation"]["api_calls"] = True
    with pytest.raises(ValueError, match="budget_allocation.api_calls must be a non-negative integer"):
        FiniteBacklog.from_dict(payload)
