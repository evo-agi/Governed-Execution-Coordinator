"""Finite backlog parsing and canonical identity."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Mapping

from ge_nwp_coordinator.canonicalization import (
    canonical_sha256,
    decode_json_object,
    normalize_set_like_strings,
    require_exact_keys,
    require_non_negative_int,
    require_positive_int,
    require_safe_ref,
    require_safe_ref_list,
    require_safe_ref_tuple,
    require_safe_relative_path_list,
    require_safe_relative_path_tuple,
    require_safe_string,
)
from ge_nwp_coordinator.lease import require_digest

BACKLOG_SCHEMA_ID = "governed-execution.nwp-finite-backlog.v1"
BACKLOG_SCHEMA_VERSION = 1
BACKLOG_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "backlog_id",
        "lease_reference",
        "work_items",
        "content_digest",
    }
)
WORK_ITEM_KEYS = frozenset(
    {
        "work_item_id",
        "objective_label",
        "opaque_private_assignment_ref",
        "repo",
        "branches",
        "allowed_paths",
        "task_class",
        "risk_lane",
        "required_validation_profile",
        "budget_allocation",
        "dependencies",
        "stop_conditions",
    }
)
BUDGET_ALLOCATION_KEYS = frozenset({"api_calls", "compute_seconds"})


@dataclass(frozen=True)
class WorkItem:
    work_item_id: str
    objective_label: str
    opaque_private_assignment_ref: str
    repo: str
    branches: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    task_class: str
    risk_lane: str
    required_validation_profile: str
    budget_allocation: Mapping[str, Any]
    dependencies: tuple[str, ...]
    stop_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "work_item_id", require_safe_ref(self.work_item_id, "work_item_id"))
        object.__setattr__(
            self,
            "objective_label",
            require_safe_string(self.objective_label, "objective_label", max_length=96),
        )
        object.__setattr__(
            self,
            "opaque_private_assignment_ref",
            require_safe_ref(self.opaque_private_assignment_ref, "opaque_private_assignment_ref"),
        )
        object.__setattr__(self, "repo", require_safe_ref(self.repo, "repo"))
        object.__setattr__(
            self,
            "branches",
            normalize_set_like_strings(_require_safe_branch_tuple(self.branches, "branches"), "branches"),
        )
        object.__setattr__(
            self,
            "allowed_paths",
            normalize_set_like_strings(
                require_safe_relative_path_tuple(self.allowed_paths, "allowed_paths"),
                "allowed_paths",
            ),
        )
        object.__setattr__(self, "task_class", require_safe_ref(self.task_class, "task_class"))
        object.__setattr__(self, "risk_lane", require_safe_ref(self.risk_lane, "risk_lane"))
        object.__setattr__(
            self,
            "required_validation_profile",
            require_safe_ref(self.required_validation_profile, "required_validation_profile"),
        )
        object.__setattr__(self, "budget_allocation", _require_budget_allocation(self.budget_allocation))
        object.__setattr__(
            self,
            "dependencies",
            normalize_set_like_strings(require_safe_ref_tuple(self.dependencies, "dependencies"), "dependencies"),
        )
        object.__setattr__(
            self,
            "stop_conditions",
            normalize_set_like_strings(require_safe_ref_tuple(self.stop_conditions, "stop_conditions"), "stop_conditions"),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkItem":
        raw = require_exact_keys(payload, "work_item", WORK_ITEM_KEYS)
        return cls(
            work_item_id=require_safe_ref(raw.get("work_item_id"), "work_item_id"),
            objective_label=require_safe_string(raw.get("objective_label"), "objective_label", max_length=96),
            opaque_private_assignment_ref=require_safe_ref(
                raw.get("opaque_private_assignment_ref"),
                "opaque_private_assignment_ref",
            ),
            repo=require_safe_ref(raw.get("repo"), "repo"),
            branches=_require_safe_branch_list(raw.get("branches"), "branches", ordered=False),
            allowed_paths=require_safe_relative_path_list(raw.get("allowed_paths"), "allowed_paths", ordered=False),
            task_class=require_safe_ref(raw.get("task_class"), "task_class"),
            risk_lane=require_safe_ref(raw.get("risk_lane"), "risk_lane"),
            required_validation_profile=require_safe_ref(
                raw.get("required_validation_profile"),
                "required_validation_profile",
            ),
            budget_allocation=_require_budget_allocation(raw.get("budget_allocation")),
            dependencies=require_safe_ref_list(raw.get("dependencies"), "dependencies", ordered=False),
            stop_conditions=require_safe_ref_list(raw.get("stop_conditions"), "stop_conditions", ordered=False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_item_id": self.work_item_id,
            "objective_label": self.objective_label,
            "opaque_private_assignment_ref": self.opaque_private_assignment_ref,
            "repo": self.repo,
            "branches": list(self.branches),
            "allowed_paths": list(self.allowed_paths),
            "task_class": self.task_class,
            "risk_lane": self.risk_lane,
            "required_validation_profile": self.required_validation_profile,
            "budget_allocation": dict(self.budget_allocation),
            "dependencies": list(self.dependencies),
            "stop_conditions": list(self.stop_conditions),
        }


@dataclass(frozen=True)
class FiniteBacklog:
    schema_id: str
    schema_version: int
    backlog_id: str
    lease_reference: str
    work_items: tuple[WorkItem, ...]
    content_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_safe_ref(self.schema_id, "schema_id"))
        object.__setattr__(self, "schema_version", require_positive_int(self.schema_version, "schema_version"))
        object.__setattr__(self, "backlog_id", require_safe_ref(self.backlog_id, "backlog_id"))
        object.__setattr__(self, "lease_reference", require_safe_ref(self.lease_reference, "lease_reference"))
        if not isinstance(self.work_items, tuple) or not self.work_items:
            raise ValueError("invalid_field_type:work_items")
        object.__setattr__(self, "work_items", tuple(self.work_items))
        object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        _validate_work_item_graph(self.work_items)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FiniteBacklog":
        raw = require_exact_keys(payload, "backlog", BACKLOG_KEYS)
        schema_id = require_safe_ref(raw.get("schema_id"), "schema_id")
        if schema_id != BACKLOG_SCHEMA_ID:
            raise ValueError("unsupported backlog schema_id")
        schema_version = require_positive_int(raw.get("schema_version"), "schema_version")
        if schema_version != BACKLOG_SCHEMA_VERSION:
            raise ValueError("unsupported backlog schema_version")
        items_raw = raw.get("work_items")
        if not isinstance(items_raw, list) or not items_raw:
            raise ValueError("work_items must be a non-empty finite array")
        work_items = tuple(WorkItem.from_dict(item) for item in items_raw)
        _validate_work_item_graph(work_items)
        backlog = cls(
            schema_id=schema_id,
            schema_version=schema_version,
            backlog_id=require_safe_ref(raw.get("backlog_id"), "backlog_id"),
            lease_reference=require_safe_ref(raw.get("lease_reference"), "lease_reference"),
            work_items=work_items,
            content_digest=require_digest(raw.get("content_digest"), "content_digest"),
        )
        if backlog.canonical_digest() != backlog.content_digest:
            raise ValueError("content_digest_mismatch")
        return backlog

    @classmethod
    def from_json(cls, text: str) -> "FiniteBacklog":
        return cls.from_dict(decode_json_object(text, "backlog"))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload = {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "backlog_id": self.backlog_id,
            "lease_reference": self.lease_reference,
            "work_items": [item.to_dict() for item in self.work_items],
        }
        if include_digest:
            payload["content_digest"] = self.content_digest
        return payload

    def canonical_identity_payload(self) -> dict[str, Any]:
        return self.to_dict(include_digest=False)

    def canonical_digest(self) -> str:
        return canonical_sha256(self.canonical_identity_payload())

    def with_digest(self) -> "FiniteBacklog":
        return replace(self, content_digest=self.canonical_digest())

    def deterministic_order(self) -> tuple[str, ...]:
        """Return dependency-respecting order while preserving original priority."""

        ids = [item.work_item_id for item in self.work_items]
        remaining = set(ids)
        resolved: set[str] = set()
        ordered: list[str] = []
        while remaining:
            progressed = False
            for item in self.work_items:
                if item.work_item_id not in remaining:
                    continue
                if all(dep in resolved for dep in item.dependencies):
                    ordered.append(item.work_item_id)
                    resolved.add(item.work_item_id)
                    remaining.remove(item.work_item_id)
                    progressed = True
            if not progressed:
                raise ValueError("dependency_cycle")
        return tuple(ordered)


def _require_safe_branch_tuple(value: Any, field_name: str, *, ordered: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise ValueError(f"invalid_field_type:{field_name}")
    items = tuple(require_safe_string(item, f"{field_name}[]", max_length=96) for item in value)
    if ordered:
        return items
    return normalize_set_like_strings(items, field_name)


def _require_safe_branch_list(value: Any, field_name: str, *, ordered: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"invalid_field_type:{field_name}")
    return _require_safe_branch_tuple(tuple(value), field_name, ordered=ordered)


def _require_budget_allocation(value: Any) -> Mapping[str, Any]:
    raw = require_exact_keys(value, "budget_allocation", BUDGET_ALLOCATION_KEYS)
    return MappingProxyType(
        {
            "api_calls": require_non_negative_int(raw.get("api_calls"), "budget_allocation.api_calls"),
            "compute_seconds": require_non_negative_int(
                raw.get("compute_seconds"),
                "budget_allocation.compute_seconds",
            ),
        }
    )


def _validate_work_item_graph(work_items: tuple[WorkItem, ...]) -> None:
    ids: set[str] = set()
    for item in work_items:
        if item.work_item_id in ids:
            raise ValueError("duplicate_field:work_items.work_item_id")
        ids.add(item.work_item_id)
    for item in work_items:
        for dependency in item.dependencies:
            if dependency == item.work_item_id:
                raise ValueError("self_dependency")
            if dependency not in ids:
                raise ValueError("missing_dependency")
    _assert_acyclic(work_items)


def _assert_acyclic(work_items: tuple[WorkItem, ...]) -> None:
    by_id = {item.work_item_id: item for item in work_items}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(work_item_id: str) -> None:
        if work_item_id in visited:
            return
        if work_item_id in visiting:
            raise ValueError("dependency_cycle")
        visiting.add(work_item_id)
        for dependency in by_id[work_item_id].dependencies:
            visit(dependency)
        visiting.remove(work_item_id)
        visited.add(work_item_id)

    for item in work_items:
        visit(item.work_item_id)
