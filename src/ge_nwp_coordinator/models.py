"""Shared Coordinator value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionStatus(str, Enum):
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Decision:
    status: DecisionStatus
    reason: str

    @property
    def accepted(self) -> bool:
        return self.status is DecisionStatus.ACCEPTED


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    reason: str


def blocked(reason: str) -> Decision:
    return Decision(status=DecisionStatus.BLOCKED, reason=reason)


def accepted(reason: str = "accepted") -> Decision:
    return Decision(status=DecisionStatus.ACCEPTED, reason=reason)
