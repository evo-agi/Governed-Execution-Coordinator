"""Finite backlog parsing and canonical identity."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Mapping

from ge_nwp_coordinator.canonicalization import (
    canonical_sha256,
    normalize_set_like_strings,
    require_object,
    require_string,
    require_string_tuple,
)
from ge_nwp_coordinator.lease import require_digest

BACKLOG_SCHEMA_ID = "governed-execution.nwp-finite-backlog.v1"
BACKLOG_SCHEMA_VERSION = 1

FORBIDDEN_PRIVATE_KEYS = frozenset(
    {
        "private_assignment",
        "private_assignment_content",
        "private_brief",
        "raw_prompt",
        "prompt",
        "raw_log",
        "raw_logs",
        "worker_output",
    }
)
FORBIDDEN_EXPANSION_KEYS = frozenset(
    {
        "dynamic_discovery",
        "discovery_source",
        "issue_query",
        "api_source",
        "symphony_source",
        "chatgpt_source",
        "control_plane_source",
        "self_expansion",
        "expands_from",
    }
)


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
        object.__setattr__(self, "branches", normalize_set_like_strings(self.branches, "branches"))
        object.__setattr__(self, "allowed_paths", normalize_set_like_strings(self.allowed_paths, "allowed_paths"))
        object.__setattr__(self, "dependencies", normalize_set_like_strings(self.dependencies, "dependencies"))
        object.__setattr__(
            self,
            "stop_conditions",
            normalize_set_like_strings(self.stop_conditions, "stop_conditions"),
        )
        object.__setattr__(self, "budget_allocation", MappingProxyType(dict(self.budget_allocation)))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkItem":
        raw = require_object(dict(payload), "work_item")
        _reject_forbidden_keys(raw, "work_item")
        return cls(
            work_item_id=require_string(raw.get("work_item_id"), "work_item_id"),
            objective_label=require_string(raw.get("objective_label"), "objective_label"),
            opaque_private_assignment_ref=require_string(
                raw.get("opaque_private_assignment_ref"),
                "opaque_private_assignment_ref",
            ),
            repo=require_string(raw.get("repo"), "repo"),
            branches=require_string_tuple(raw.get("branches"), "branches", ordered=False),
            allowed_paths=require_string_tuple(raw.get("allowed_paths"), "allowed_paths", ordered=False),
            task_class=require_string(raw.get("task_class"), "task_class"),
            risk_lane=require_string(raw.get("risk_lane"), "risk_lane"),
            required_validation_profile=require_string(
                raw.get("required_validation_profile"),
                "required_validation_profile",
            ),
            budget_allocation=MappingProxyType(require_object(raw.get("budget_allocation"), "budget_allocation")),
            dependencies=require_string_tuple(raw.get("dependencies"), "dependencies", ordered=False),
            stop_conditions=require_string_tuple(raw.get("stop_conditions"), "stop_conditions", ordered=False),
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

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FiniteBacklog":
        raw = require_object(dict(payload), "backlog")
        _reject_forbidden_keys(raw, "backlog")
        schema_id = require_string(raw.get("schema_id"), "schema_id")
        if schema_id != BACKLOG_SCHEMA_ID:
            raise ValueError("unsupported backlog schema_id")
        schema_version = raw.get("schema_version")
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
            backlog_id=require_string(raw.get("backlog_id"), "backlog_id"),
            lease_reference=require_string(raw.get("lease_reference"), "lease_reference"),
            work_items=work_items,
            content_digest=require_digest(raw.get("content_digest"), "content_digest"),
        )
        if backlog.canonical_digest() != backlog.content_digest:
            raise ValueError("content_digest_mismatch")
        return backlog

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


def _reject_forbidden_keys(raw: Mapping[str, Any], field_name: str) -> None:
    forbidden = FORBIDDEN_PRIVATE_KEYS | FORBIDDEN_EXPANSION_KEYS
    present = sorted(key for key in raw if key in forbidden)
    if present:
        raise ValueError(f"{field_name} contains forbidden fields: {', '.join(present)}")


def _validate_work_item_graph(work_items: tuple[WorkItem, ...]) -> None:
    ids: set[str] = set()
    for item in work_items:
        if item.work_item_id in ids:
            raise ValueError(f"duplicate work_item_id {item.work_item_id!r}")
        ids.add(item.work_item_id)
    for item in work_items:
        for dependency in item.dependencies:
            if dependency == item.work_item_id:
                raise ValueError(f"self_dependency {item.work_item_id!r}")
            if dependency not in ids:
                raise ValueError(f"missing_dependency {dependency!r}")
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
