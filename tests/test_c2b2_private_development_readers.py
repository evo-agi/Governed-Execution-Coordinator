from __future__ import annotations

import ast
from collections.abc import Callable
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import traceback
from types import SimpleNamespace
from typing import Any

import pytest

from ge_nwp_coordinator import _development_decision_row_values as decision_rows
from ge_nwp_coordinator import _development_effect_row_values as effect_rows
from ge_nwp_coordinator import _development_program_row_values as program_rows
from ge_nwp_coordinator import _sqlite_development_reader_contracts as contracts
from ge_nwp_coordinator import _sqlite_development_readers as readers
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    CapsuleEntryV1,
    CeilingsV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
    WorkerObservationV1,
    WorkSpecV1,
    create_author_command_and_effect_fence,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
    _execute_select_fetch_bounded,
)
from ge_nwp_coordinator.sqlite_writer_session import (
    _WriterIssuanceMatch,
    acquire_sqlite_writer_session,
)
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module


NOW = "2026-08-15T12:34:56Z"
EXPIRES = "2026-08-16T12:34:56Z"
OID = "a" * 40
PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
PATHS_JSON = '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]'
CEILINGS = {
    "max_active_invocations": 1,
    "max_candidate_bytes": 2048,
    "max_changed_files": 3,
    "max_cost_microusd": 4000,
    "max_cpu_seconds": 50,
    "max_deliveries": 6,
    "max_deployments": 0,
    "max_local_commits": 0,
    "max_memory_bytes": 9000,
    "max_merges": 0,
    "max_model_input_tokens": 1100,
    "max_model_output_tokens": 1200,
    "max_pull_requests": 0,
    "max_pushes": 0,
    "max_wall_seconds": 150,
}
PRIVATE_SENTINEL = "PRIVATE-C2B2-READER-SENTINEL-DO-NOT-LEAK"
READERS_PATH = Path(readers.__file__).resolve()
SLICE_3_OWNED_FRAME_BASENAMES = frozenset(
    {"_sqlite_development_readers.py", "sqlite_transition_select_support.py"}
)


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


class _StructuralStandIn:
    def __init__(self) -> None:
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> object:
        self.borrow_count += 1
        return object()


class _PrivacyCursor:
    def __init__(
        self,
        *,
        rows: list[object],
        fetch_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.fetch_error = fetch_error
        self.close_error = close_error
        self.fetch_limits: list[int] = []
        self.close_count = 0

    def fetchmany(self, limit: int) -> list[object]:
        self.fetch_limits.append(limit)
        if self.fetch_error is not None:
            raise self.fetch_error
        return self.rows

    def close(self) -> None:
        self.close_count += 1
        if self.close_error is not None:
            raise self.close_error


class _PrivacyConnection(sqlite3.Connection):
    scripted_cursor: _PrivacyCursor
    execute_error: Exception | None
    execute_arguments: list[tuple[str, tuple[object, ...]]]

    def execute(  # type: ignore[override]
        self,
        sql: str,
        parameters: tuple[object, ...] = (),
    ) -> _PrivacyCursor:
        self.execute_arguments.append((sql, parameters))
        if self.execute_error is not None:
            raise self.execute_error
        return self.scripted_cursor


class _SupportCapability:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        self.borrow_count += 1
        return self.connection


def _digest(domain: str, identity: dict[str, object]) -> str:
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + canonical).hexdigest()


def _row_with_digest(
    *,
    columns: tuple[str, ...],
    identity: dict[str, object],
    digest_name: str,
    domain: str,
) -> tuple[object, ...]:
    physical = dict(identity)
    physical[digest_name] = _digest(domain, identity)
    return tuple(physical[column] for column in columns)


def _replace_digest_row_field(
    row: tuple[object, ...],
    *,
    columns: tuple[str, ...],
    field: str,
    value: object,
    digest_name: str,
    domain: str,
) -> tuple[object, ...]:
    identity = dict(zip(columns, row, strict=True))
    del identity[digest_name]
    identity[field] = value
    return _row_with_digest(
        columns=columns,
        identity=identity,
        digest_name=digest_name,
        domain=domain,
    )


def _insert(
    connection: sqlite3.Connection,
    table: str,
    columns: tuple[str, ...],
    row: tuple[object, ...],
) -> None:
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        row,
    )


def _program_version_row(
    *,
    program_ref: str = "program-1",
    program_version_ref: str = "version-1",
    decision_ref: str = "decision-1",
) -> tuple[object, ...]:
    return _row_with_digest(
        columns=program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-program-version.v1",
            "program_version_ref": program_version_ref,
            "program_ref": program_ref,
            "program_version_number": 1,
            "program_version_kind": "initial",
            "creating_decision_ref": decision_ref,
            "accepted_intent_revision_ref": "intent-1",
            "created_at": NOW,
        },
        digest_name="program_version_digest",
        domain="governed-execution.nwp-development-program-version.v1.identity",
    )


def _work_revision_row(
    *,
    work_item_ref: str,
    work_item_revision_ref: str,
    number: int = 1,
    prior: str | None = None,
) -> tuple[object, ...]:
    return _row_with_digest(
        columns=program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-work-item-revision.v1",
            "work_item_revision_ref": work_item_revision_ref,
            "program_ref": "program-1",
            "work_item_ref": work_item_ref,
            "work_item_revision_number": number,
            "work_item_revision_kind": "initial" if number == 1 else "replan",
            "prior_work_item_revision_ref": prior,
            "accepted_intent_revision_ref": "intent-1",
            "created_at": NOW,
        },
        digest_name="work_item_revision_digest",
        domain="governed-execution.nwp-development-work-item-revision.v1.identity",
    )


def _work_head_row(
    *,
    work_item_ref: str,
    current_ref: str,
    current_number: int,
) -> tuple[object, ...]:
    return _row_with_digest(
        columns=program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-work-item-head.v1",
            "work_item_ref": work_item_ref,
            "program_ref": "program-1",
            "current_work_item_revision_ref": current_ref,
            "current_work_item_revision_number": current_number,
            "head_revision": 0,
            "work_state": "planned",
            "updated_at": NOW,
        },
        digest_name="head_digest",
        domain="governed-execution.nwp-development-work-item-head.v1.identity",
    )


def _membership_row(
    *,
    ordinal: int,
    work_item_ref: str,
    work_item_revision_ref: str,
) -> tuple[object, ...]:
    return _row_with_digest(
        columns=program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-program-version-work-item.v1",
            "program_ref": "program-1",
            "program_version_ref": "version-1",
            "work_item_ref": work_item_ref,
            "work_item_revision_ref": work_item_revision_ref,
            "membership_ordinal": ordinal,
            "created_at": NOW,
        },
        digest_name="membership_digest",
        domain="governed-execution.nwp-development-program-version-work-item.v1.identity",
    )


def _attempt_fence_physical(attempt_fence: AttemptFenceV1) -> tuple[object, ...]:
    mapping = attempt_fence.to_mapping()
    physical = {key: value for key, value in mapping.items() if key not in {"path_ceiling", "allowed_effect_classes", "aggregate_ceilings"}}
    physical["path_ceiling_json"] = PATHS_JSON
    bit = {
        "author_candidate": 1,
        "cancel_effect": 2,
        "local_git_commit": 4,
        "review_candidate": 8,
        "validate_candidate": 16,
    }
    physical["allowed_effect_class_mask"] = sum(
        bit[value] for value in attempt_fence.allowed_effect_classes
    )
    for name, value in attempt_fence.aggregate_ceilings.to_mapping().items():
        physical[f"aggregate_{name}"] = value
    physical["recorded_at"] = NOW
    return tuple(physical[column] for column in effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS)


def _effect_fence_physical(effect_fence: EffectFenceV1) -> tuple[object, ...]:
    mapping = effect_fence.to_mapping()
    physical = {key: value for key, value in mapping.items() if key not in {"path_ceiling", "effect_ceilings"}}
    physical["path_ceiling_json"] = PATHS_JSON
    for name, value in effect_fence.effect_ceilings.to_mapping().items():
        physical[f"effect_{name}"] = value
    physical["recorded_at"] = NOW
    return tuple(physical[column] for column in effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS)


def _author_command_physical(author_command: object) -> tuple[object, ...]:
    mapping = author_command.to_mapping()
    physical = {key: value for key, value in mapping.items() if key not in {"path_ceiling", "effect_ceilings"}}
    physical["path_ceiling_json"] = PATHS_JSON
    for name, value in author_command.effect_ceilings.to_mapping().items():
        physical[f"effect_{name}"] = value
    physical["recorded_at"] = NOW
    return tuple(physical[column] for column in effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS)


def _decision_row() -> tuple[object, ...]:
    identity = {
        "schema_id": "governed-execution.nwp-development-decision.v1",
        "mutation_ref": "mutation-1",
        "decision_ref": "decision-1",
        "program_ref": "program-1",
        "decision_kind": "initialize",
        "decision_variant": "program_genesis",
        "basis_decision_ref": None,
        "basis_program_version_ref": None,
        "basis_program_version_number": None,
        "expected_program_head_revision": 0,
        "resulting_program_version_ref": "version-1",
        "resulting_program_version_number": 1,
        "selected_semantic_attempt_ref": None,
        "selected_candidate_ref": None,
        "selected_attempt_fence_ref": None,
        "selected_attempt_fence_digest": None,
        "target_effect_intent_ref": None,
        "target_effect_class": None,
        "target_effect_fence_ref": None,
        "target_effect_fence_digest": None,
        "expected_target_effect_head_revision": None,
        "target_delivery_attempt_ref": None,
        "originating_command_ref": None,
        "originating_command_digest": None,
        "target_capsule_manifest_ref": None,
        "target_portable_capsule_digest": None,
        "coding_global_stop_ref": "stop-1",
        "coding_global_stop_version": 0,
        "source_directive_ref": None,
        "source_directive_digest": None,
        "source_evidence_ref": None,
        "source_evidence_digest": None,
        "preassigned_semantic_attempt_ref": "attempt-1",
        "preassigned_candidate_ref": "candidate-1",
        "preassigned_effect_intent_ref": None,
        "preassigned_effect_fence_ref": None,
        "preassigned_delivery_attempt_ref": None,
        "resulting_accepted_intent_revision_ref": None,
        "resulting_work_item_ref": None,
        "resulting_work_item_revision_ref": None,
        "reason_code": "decision.recorded",
        "decided_at": NOW,
    }
    return _row_with_digest(
        columns=decision_rows._DEVELOPMENT_DECISION_COLUMNS,
        identity=identity,
        digest_name="decision_digest",
        domain="governed-execution.nwp-development-decision.v1.identity",
    )


def _receipt_row() -> tuple[object, ...]:
    projection = {
        "schema_id": "governed-execution.nwp-initialize-development-program-result.v1",
        "program_ref": "program-1",
        "decision_ref": "decision-1",
        "result_program_version_ref": "version-1",
        "result_decision_ref": "decision-1",
    }
    values = {
        "schema_id": "governed-execution.nwp-development-mutation-receipt.v1",
        "mutation_ref": "mutation-1",
        "mutation_family": "initialize_development_program",
        "command_schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "command_digest": "1" * 64,
        "program_ref": "program-1",
        "decision_ref": "decision-1",
        "result_program_version_ref": "version-1",
        "result_semantic_attempt_ref": None,
        "result_effect_intent_ref": None,
        "result_effect_fence_ref": None,
        "result_delivery_attempt_ref": None,
        "result_observation_ref": None,
        "result_decision_ref": "decision-1",
        "result_class": "development_program_initialized",
        "result_projection_digest": _digest(
            "governed-execution.nwp-initialize-development-program-result.v1.identity",
            projection,
        ),
        "mutation_graph_digest": "2" * 64,
        "outcome": "committed",
        "committed_at": NOW,
    }
    return tuple(
        values[column]
        for column in decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS
    )


def _seed_database(
    tmp_path: Path,
    *,
    member_count: int = 1,
) -> tuple[CoordinatorStateLocation, dict[str, tuple[object, ...]]]:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "state")
    initialize_database(location)
    ceilings = CeilingsV1.create(**CEILINGS)
    work_spec = WorkSpecV1.create(
        work_spec_ref="work-spec-1",
        program_ref="program-1",
        program_version_ref="version-1",
        accepted_intent_revision_ref="intent-1",
        work_item_ref="work-0000",
        work_item_revision_ref="revision-0000",
        repository_ref="repository-1",
        base_git_oid=OID,
        authorized_paths=list(PATHS),
        objective="PRIVATE OBJECTIVE SENTINEL",
        requirements=["PRIVATE REQUIREMENT SENTINEL"],
        exclusions=["PRIVATE EXCLUSION SENTINEL"],
        validation_requirement_ref="validation-1",
        review_requirement_ref="review-1",
    )
    attempt_fence = AttemptFenceV1.create(
        attempt_fence_ref="attempt-fence-1",
        parent_standing_grant_ref="grant-1",
        parent_standing_grant_digest="3" * 64,
        attempt_authorization_ref="attempt-authorization-1",
        attempt_authorization_digest="4" * 64,
        program_ref="program-1",
        program_version_ref="version-1",
        accepted_intent_revision_ref="intent-1",
        work_item_ref="work-0000",
        work_item_revision_ref="revision-0000",
        semantic_attempt_ref="attempt-1",
        repository_ref="repository-1",
        base_git_oid=OID,
        path_ceiling=list(PATHS),
        allowed_effect_classes=["author_candidate", "validate_candidate"],
        aggregate_ceilings=ceilings,
        expires_at=EXPIRES,
        global_stop_ref="stop-1",
        global_stop_version=0,
    )
    author_command, author_effect_fence = create_author_command_and_effect_fence(
        work_spec=work_spec,
        attempt_fence=attempt_fence,
        command_ref="command-1",
        effect_intent_ref="effect-1",
        effect_fence_ref="effect-fence-1",
        candidate_ref="candidate-1",
        effect_authorization_ref="effect-authorization-1",
        effect_authorization_digest="5" * 64,
        expires_at=EXPIRES,
        validation_requirement_digest="6" * 64,
        review_requirement_digest="7" * 64,
        capsule_profile_ref="capsule-profile-1",
        redaction_profile_ref="redaction-profile-1",
        effect_ceilings=ceilings,
    )
    bound_mapping = author_effect_fence.to_mapping()
    bound_mapping.update(
        {
            "effect_fence_ref": "effect-fence-bound",
            "effect_authorization_ref": "effect-authorization-bound",
            "effect_authorization_digest": "8" * 64,
            "effect_intent_ref": "effect-bound",
            "effect_class": "validate_candidate",
            "portable_capsule_digest": "9" * 64,
        }
    )
    bound_identity = {
        key: value
        for key, value in bound_mapping.items()
        if key != "effect_fence_digest"
    }
    bound_mapping["effect_fence_digest"] = _digest(
        "governed-execution.nwp-effect-fence.v1.identity",
        bound_identity,
    )
    bound_effect_fence = EffectFenceV1.from_mapping(bound_mapping)

    program_version = _program_version_row()
    program_head = _row_with_digest(
        columns=program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-program-head.v1",
            "program_ref": "program-1",
            "current_program_version_ref": "version-1",
            "current_program_version_number": 1,
            "head_revision": 0,
            "program_state": "active",
            "updated_at": NOW,
        },
        digest_name="head_digest",
        domain="governed-execution.nwp-development-program-head.v1.identity",
    )
    accepted_intent = _row_with_digest(
        columns=program_rows._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-accepted-intent-revision.v1",
            "accepted_intent_revision_ref": "intent-1",
            "program_ref": "program-1",
            "accepted_intent_revision_number": 1,
            "prior_accepted_intent_revision_ref": None,
            "source_intent_ref": "source-intent-1",
            "source_intent_digest": "a" * 64,
            "safe_projection_digest": "b" * 64,
            "created_at": NOW,
        },
        digest_name="accepted_intent_revision_digest",
        domain="governed-execution.nwp-development-accepted-intent-revision.v1.identity",
    )
    semantic_attempt = _row_with_digest(
        columns=program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-semantic-attempt.v1",
            "semantic_attempt_ref": "attempt-1",
            "program_ref": "program-1",
            "program_version_ref": "version-1",
            "accepted_intent_revision_ref": "intent-1",
            "work_item_ref": "work-0000",
            "work_item_revision_ref": "revision-0000",
            "attempt_number": 1,
            "candidate_ref": "candidate-1",
            "attempt_phase": "established",
            "selection_decision_ref": "decision-1",
            "created_at": NOW,
        },
        digest_name="semantic_attempt_digest",
        domain="governed-execution.nwp-development-semantic-attempt.v1.identity",
    )
    author_intent = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-effect-intent.v1",
            "effect_intent_ref": "effect-1",
            "program_ref": "program-1",
            "program_version_ref": "version-1",
            "semantic_attempt_ref": "attempt-1",
            "effect_class": "author_candidate",
            "candidate_ref": "candidate-1",
            "command_ref": "command-1",
            "basis_decision_ref": "decision-1",
            "cancellation_target_effect_intent_ref": None,
            "expected_target_effect_head_revision": None,
            "portable_capsule_digest": None,
            "created_at": NOW,
        },
        digest_name="effect_intent_digest",
        domain="governed-execution.nwp-development-effect-intent.v1.identity",
    )
    bound_intent = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-effect-intent.v1",
            "effect_intent_ref": "effect-bound",
            "program_ref": "program-1",
            "program_version_ref": "version-1",
            "semantic_attempt_ref": "attempt-1",
            "effect_class": "validate_candidate",
            "candidate_ref": "candidate-1",
            "command_ref": "command-1",
            "basis_decision_ref": "decision-1",
            "cancellation_target_effect_intent_ref": None,
            "expected_target_effect_head_revision": None,
            "portable_capsule_digest": "9" * 64,
            "created_at": NOW,
        },
        digest_name="effect_intent_digest",
        domain="governed-execution.nwp-development-effect-intent.v1.identity",
    )
    authority_one = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-authority-evaluation.v1",
            "authority_evaluation_ref": "evaluation-1",
            "program_ref": "program-1",
            "evaluation_scope": "attempt",
            "evaluation_subject_ref": "attempt-1",
            "semantic_attempt_ref": "attempt-1",
            "effect_intent_ref": None,
            "authority_ref": "authority-1",
            "authority_digest": "c" * 64,
            "authority_state": "verified",
            "reason_code": "authority.verified",
            "expires_at": EXPIRES,
            "evaluated_at": NOW,
        },
        digest_name="authority_evaluation_digest",
        domain="governed-execution.nwp-development-authority-evaluation.v1.identity",
    )
    authority_two = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-authority-evaluation.v1",
            "authority_evaluation_ref": "evaluation-2",
            "program_ref": "program-1",
            "evaluation_scope": "attempt",
            "evaluation_subject_ref": "attempt-1",
            "semantic_attempt_ref": "attempt-1",
            "effect_intent_ref": None,
            "authority_ref": "authority-2",
            "authority_digest": "d" * 64,
            "authority_state": "pending",
            "reason_code": "authority.pending",
            "expires_at": None,
            "evaluated_at": NOW,
        },
        digest_name="authority_evaluation_digest",
        domain="governed-execution.nwp-development-authority-evaluation.v1.identity",
    )
    effect_head = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-effect-head.v1",
            "effect_intent_ref": "effect-1",
            "program_ref": "program-1",
            "current_effect_fence_ref": "effect-fence-1",
            "head_revision": 0,
            "effect_state": "ready_for_delivery",
            "cancellation_effect_intent_ref": None,
            "updated_at": NOW,
        },
        digest_name="head_digest",
        domain="governed-execution.nwp-development-effect-head.v1.identity",
    )
    delivery_envelope = DeliveryEnvelopeV1.create(
        delivery_attempt_ref="delivery-1",
        adapter_kind="direct_local_bootstrap",
        adapter_safe_correlation_ref="correlation-1",
        author_command=author_command,
        attempt_fence=attempt_fence,
        author_effect_fence=author_effect_fence,
        effect_fence=author_effect_fence,
    )
    envelope = delivery_envelope.to_mapping()
    delivery_wrapper_identity = {
        "schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
        "delivery_envelope_digest": delivery_envelope.delivery_envelope_digest,
        "delivery_kind": "initial",
        "delivery_number": 1,
        "predecessor_delivery_attempt_ref": None,
        "basis_decision_ref": "decision-1",
        "recorded_at": NOW,
    }
    delivery_physical = dict(envelope)
    delivery_physical.update(
        {
            "delivery_kind": "initial",
            "delivery_number": 1,
            "predecessor_delivery_attempt_ref": None,
            "basis_decision_ref": "decision-1",
            "recorded_at": NOW,
            "delivery_attempt_digest": _digest(
                "governed-execution.nwp-development-delivery-attempt.v1.identity",
                delivery_wrapper_identity,
            ),
        }
    )
    delivery_attempt = tuple(
        delivery_physical[column]
        for column in effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS
    )
    delivery_head = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-delivery-head.v1",
            "effect_intent_ref": "effect-1",
            "program_ref": "program-1",
            "current_delivery_attempt_ref": "delivery-1",
            "head_revision": 0,
            "delivery_state": "planned",
            "updated_at": NOW,
        },
        digest_name="head_digest",
        domain="governed-execution.nwp-development-delivery-head.v1.identity",
    )
    safe_projection = program_rows.development_work_spec_safe_projection_from_work_spec(
        work_spec=work_spec
    )
    binding_identity = {
        "schema_id": "governed-execution.nwp-development-work-spec-binding.v1",
        "work_spec_ref": work_spec.work_spec_ref,
        "program_ref": work_spec.program_ref,
        "program_version_ref": work_spec.program_version_ref,
        "accepted_intent_revision_ref": work_spec.accepted_intent_revision_ref,
        "work_item_ref": work_spec.work_item_ref,
        "work_item_revision_ref": work_spec.work_item_revision_ref,
        "repository_ref": work_spec.repository_ref,
        "base_git_object_format": work_spec.base_git_object_format,
        "base_git_oid": work_spec.base_git_oid,
        "authorized_paths_json": PATHS_JSON,
        "validation_requirement_ref": work_spec.validation_requirement_ref,
        "review_requirement_ref": work_spec.review_requirement_ref,
        "privacy_classification": "private_work_spec",
        "work_spec_digest": work_spec.work_spec_digest,
        "safe_projection_digest": safe_projection.safe_projection_digest,
        "recorded_at": NOW,
    }
    work_spec_binding = _row_with_digest(
        columns=program_rows._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
        identity=binding_identity,
        digest_name="work_spec_binding_digest",
        domain="governed-execution.nwp-development-work-spec-binding.v1.identity",
    )
    attempt_fence_row = _attempt_fence_physical(attempt_fence)
    author_effect_fence_row = _effect_fence_physical(author_effect_fence)
    bound_effect_fence_row = _effect_fence_physical(bound_effect_fence)
    author_command_row = _author_command_physical(author_command)
    decision = _decision_row()
    receipt = _receipt_row()

    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        _insert(connection, "development_program_heads", program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS, program_head)
        _insert(connection, "development_program_versions", program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS, program_version)
        _insert(connection, "development_accepted_intent_revisions", program_rows._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS, accepted_intent)
        for ordinal in range(member_count):
            work_ref = f"work-{ordinal:04d}"
            revision_ref = f"revision-{ordinal:04d}"
            _insert(connection, "development_work_item_heads", program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS, _work_head_row(work_item_ref=work_ref, current_ref=revision_ref, current_number=1))
            _insert(connection, "development_work_item_revisions", program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS, _work_revision_row(work_item_ref=work_ref, work_item_revision_ref=revision_ref))
            _insert(connection, "development_program_version_work_items", program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS, _membership_row(ordinal=ordinal, work_item_ref=work_ref, work_item_revision_ref=revision_ref))
        historical_one = _work_revision_row(
            work_item_ref="work-history",
            work_item_revision_ref="revision-history-1",
        )
        historical_two = _work_revision_row(
            work_item_ref="work-history",
            work_item_revision_ref="revision-history-2",
            number=2,
            prior="revision-history-1",
        )
        history_head = _work_head_row(
            work_item_ref="work-history",
            current_ref="revision-history-2",
            current_number=2,
        )
        _insert(connection, "development_work_item_heads", program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS, history_head)
        _insert(connection, "development_work_item_revisions", program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS, historical_one)
        _insert(connection, "development_work_item_revisions", program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS, historical_two)
        _insert(connection, "development_work_spec_bindings", program_rows._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS, work_spec_binding)
        _insert(connection, "development_semantic_attempts", program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS, semantic_attempt)
        _insert(connection, "development_attempt_fences", effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS, attempt_fence_row)
        _insert(connection, "development_authority_evaluations", effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS, authority_one)
        _insert(connection, "development_authority_evaluations", effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS, authority_two)
        _insert(connection, "development_effect_intents", effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS, author_intent)
        _insert(connection, "development_effect_intents", effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS, bound_intent)
        _insert(connection, "development_effect_fences", effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS, author_effect_fence_row)
        _insert(connection, "development_effect_fences", effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS, bound_effect_fence_row)
        _insert(connection, "development_author_commands", effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS, author_command_row)
        _insert(connection, "development_effect_heads", effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS, effect_head)
        _insert(connection, "development_delivery_attempts", effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS, delivery_attempt)
        _insert(connection, "development_delivery_heads", effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS, delivery_head)
        _insert(connection, "development_decisions", decision_rows._DEVELOPMENT_DECISION_COLUMNS, decision)
        _insert(connection, "development_mutation_receipts", decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS, receipt)
    return location, {
        "receipt": receipt,
        "decision": decision,
        "program_head": program_head,
        "program_version": program_version,
        "accepted_intent": accepted_intent,
        "work_head": _work_head_row(work_item_ref="work-0000", current_ref="revision-0000", current_number=1),
        "work_revision": _work_revision_row(work_item_ref="work-0000", work_item_revision_ref="revision-0000"),
        "membership": _membership_row(ordinal=0, work_item_ref="work-0000", work_item_revision_ref="revision-0000"),
        "work_spec_binding": work_spec_binding,
        "semantic_attempt": semantic_attempt,
        "attempt_fence": attempt_fence_row,
        "authority_evaluation": authority_one,
        "author_intent": author_intent,
        "bound_intent": bound_intent,
        "author_effect_fence": author_effect_fence_row,
        "bound_effect_fence": bound_effect_fence_row,
        "author_command": author_command_row,
        "effect_head": effect_head,
        "delivery_head": delivery_head,
        "delivery_attempt": delivery_attempt,
    }


def _run_with_real_capability(
    location: CoordinatorStateLocation,
    monkeypatch: pytest.MonkeyPatch,
    probe: Callable[[object], None],
) -> object:
    session = acquire_sqlite_writer_session(location)
    captured: list[object] = []
    probe_errors: list[Exception] = []
    original_create = transaction_module._create_sqlite_mutation_read_capability

    def capture_create(**kwargs: object) -> object:
        capability = original_create(**kwargs)
        captured.append(capability)
        try:
            probe(capability)
        except Exception as error:
            probe_errors.append(error)
        return capability

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(
                transaction_module,
                "_create_sqlite_mutation_read_capability",
                capture_create,
            )
            with session._resource.operation_guard(session) as operation:
                result = transaction_module._run_rollback_only_writer_fencing(
                    operation_lease=operation
                )
            assert result is _WriterIssuanceMatch.MATCH
    finally:
        session.close()
    assert len(captured) == 1
    if probe_errors:
        assert len(probe_errors) == 1
        raise probe_errors[0]
    return captured[0]


_KNOWN_PRIVATE_VALUE_TYPES = (
    contracts._DevelopmentSelectSpecification,
    contracts.DevelopmentProgramHeadAndCurrentVersionRead,
    contracts.DevelopmentInitializeDecisionAndResultingVersionRead,
    contracts.DevelopmentWorkItemHeadAndRevisionRead,
    contracts.DevelopmentProgramVersionMembershipEntry,
    contracts.DevelopmentProgramVersionMembershipRead,
    contracts.DevelopmentAttemptFenceCommandEffectRead,
    contracts.DevelopmentDeliveryHeadAndCurrentAttemptRead,
    decision_rows._ProgramGenesisDecision,
    decision_rows._CandidateAcceptanceDecision,
    decision_rows._CandidateRepairDecision,
    decision_rows._ProgramReplanDecision,
    decision_rows._AttemptSelectingReplanDecision,
    decision_rows._ProgramTerminalRejectDecision,
    decision_rows._ProgramBlockDecision,
    decision_rows._ProductiveRedeliveryDecision,
    decision_rows._CancellationRedeliveryDecision,
    decision_rows._EffectCancellationDecision,
    decision_rows.DevelopmentDecisionRowValue,
    decision_rows._InitializeDevelopmentProgramResultProjection,
    decision_rows._EstablishDevelopmentAuthorEffectIntentResultProjection,
    decision_rows._EstablishDevelopmentBoundEffectIntentResultProjection,
    decision_rows._IngestDevelopmentSourceObservationResultProjection,
    decision_rows._RecordDevelopmentProgressionDecisionResultProjection,
    decision_rows.DevelopmentMutationReceiptRowValue,
    decision_rows.DevelopmentMutationGraphEntry,
    program_rows.DevelopmentProgramHeadRowValue,
    program_rows.DevelopmentProgramVersionRowValue,
    program_rows.DevelopmentAcceptedIntentRevisionRowValue,
    program_rows.DevelopmentWorkItemHeadRowValue,
    program_rows.DevelopmentWorkItemRevisionRowValue,
    program_rows.DevelopmentProgramVersionWorkItemRowValue,
    program_rows.DevelopmentRevisionEdgeRowValue,
    program_rows.DevelopmentWorkSpecSafeProjection,
    program_rows.DevelopmentWorkSpecBindingRowValue,
    program_rows.DevelopmentSemanticAttemptRowValue,
    effect_rows.DevelopmentAttemptFenceRowValue,
    effect_rows.DevelopmentAuthorityEvaluationRowValue,
    effect_rows.DevelopmentEffectIntentRowValue,
    effect_rows.DevelopmentEffectFenceRowValue,
    effect_rows.DevelopmentAuthorCommandRowValue,
    effect_rows.DevelopmentEffectHeadRowValue,
    effect_rows.DevelopmentDeliveryAttemptRowValue,
    effect_rows.DevelopmentDeliveryHeadRowValue,
    CeilingsV1,
    CapsuleEntryV1,
    WorkSpecV1,
    AttemptFenceV1,
    EffectFenceV1,
    WorkerCommandV1,
    DeliveryEnvelopeV1,
    CandidateCapsuleManifestV1,
    WorkerObservationV1,
)


def _private_value_children(value: object) -> tuple[object, ...]:
    children: list[object] = []
    for owner in type(value).__mro__:
        slots = owner.__dict__.get("__slots__", ())
        if type(slots) is str:
            slots = (slots,)
        if type(slots) is tuple:
            for slot in slots:
                if type(slot) is str and slot not in {"__dict__", "__weakref__"}:
                    try:
                        children.append(object.__getattribute__(value, slot))
                    except AttributeError:
                        pass
    return tuple(children)


def _assert_slice3_traceback_locals_private(
    error: BaseException,
    *,
    prohibited: tuple[object, ...] = (),
    prohibited_text: tuple[str, ...] = (),
) -> tuple[str, ...]:
    prohibited_ids = {id(value) for value in prohibited}
    found_identities: set[int] = set()
    found_text: set[str] = set()
    seen: set[int] = set()
    nodes = 0

    def inspect_value(value: object, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        assert nodes <= 4096
        assert depth <= 12
        identity = id(value)
        if identity in prohibited_ids:
            found_identities.add(identity)
        if identity in seen:
            return
        seen.add(identity)
        if type(value) is str:
            for marker in prohibited_text:
                if marker in value:
                    found_text.add(marker)
            return
        if type(value) is bytes:
            for marker in prohibited_text:
                if marker.encode("utf-8") in value:
                    found_text.add(marker)
            return
        if type(value) is dict:
            for key, item in value.items():
                inspect_value(key, depth + 1)
                inspect_value(item, depth + 1)
            return
        if type(value) in (list, tuple, set, frozenset):
            for item in value:
                inspect_value(item, depth + 1)
            return
        if type(value) in _KNOWN_PRIVATE_VALUE_TYPES:
            for item in _private_value_children(value):
                inspect_value(item, depth + 1)

    owned_basenames: list[str] = []
    trace = error.__traceback__
    frame_count = 0
    while trace is not None:
        frame_count += 1
        assert frame_count <= 64
        basename = Path(trace.tb_frame.f_code.co_filename).name
        if basename in SLICE_3_OWNED_FRAME_BASENAMES:
            owned_basenames.append(basename)
            inspect_value(dict(trace.tb_frame.f_locals), 0)
        trace = trace.tb_next
    assert owned_basenames
    inspect_value(object.__getattribute__(error, "__dict__"), 0)
    assert found_identities == set()
    assert found_text == set()
    return tuple(owned_basenames)


def _assert_safe_error(
    error: SQLiteMutationStoreError,
    expected: str,
    *,
    prohibited: tuple[object, ...] = (),
    prohibited_text: tuple[str, ...] = (),
) -> tuple[str, ...]:
    assert error.error_class == expected
    assert str(error) == expected
    assert repr(error) == f"SQLiteMutationStoreError('{expected}')"
    assert error.args == (expected,)
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None
    assert getattr(error, "__notes__", None) is None
    rendered = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )
    for forbidden in (PRIVATE_SENTINEL, *prohibited_text):
        assert forbidden not in rendered
        assert forbidden not in str(error)
        assert forbidden not in repr(error)
    return _assert_slice3_traceback_locals_private(
        error,
        prohibited=prohibited,
        prohibited_text=(PRIVATE_SENTINEL, *prohibited_text),
    )


def _assert_safe_capability_error(
    error: _MutationReadCapabilityError,
    expected: _MutationReadCapabilityFailureReason,
    *,
    prohibited: tuple[object, ...] = (),
    prohibited_text: tuple[str, ...] = (),
) -> tuple[str, ...]:
    assert error.reason is expected
    assert error.args == (expected.value,)
    assert str(error) == expected.value
    assert repr(error) == f"_MutationReadCapabilityError('{expected.value}')"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert getattr(error, "__notes__", None) is None
    rendered = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )
    for forbidden in (PRIVATE_SENTINEL, *prohibited_text):
        assert forbidden not in rendered
        assert forbidden not in str(error)
        assert forbidden not in repr(error)
    return _assert_slice3_traceback_locals_private(
        error,
        prohibited=prohibited,
        prohibited_text=(PRIVATE_SENTINEL, *prohibited_text),
    )


@pytest.mark.parametrize(
    ("failure_mode", "expected_error", "expected_close_count"),
    (
        ("execute", "database_integrity_failure", 0),
        ("fetch", "mutation_failed", 1),
        ("close_after_success", "mutation_failed", 1),
        ("fetch_and_close", "database_integrity_failure", 1),
    ),
)
def test_direct_bounded_select_failures_purge_all_raw_traceback_locals(
    failure_mode: str,
    expected_error: str,
    expected_close_count: int,
) -> None:
    marker_prefix = f"{PRIVATE_SENTINEL}-{failure_mode}"
    sql = f"SELECT '{marker_prefix}-SQL'"
    parameter = f"{marker_prefix}-PARAMETER"
    row_value = f"{marker_prefix}-ROW"
    mapping_value = f"{marker_prefix}-MAPPING"
    decoded_value = f"{marker_prefix}-DECODED"
    work_spec_marker = f"{marker_prefix}-WORK-SPEC"
    capsule_marker = f"{marker_prefix}-CAPSULE"
    credential_marker = f"{marker_prefix}-CREDENTIAL"
    endpoint_marker = f"{marker_prefix}-ENDPOINT"
    model_marker = f"{marker_prefix}-PROMPT-TRANSCRIPT-MODEL-RESPONSE"
    row = (
        row_value,
        {"private": mapping_value},
        decoded_value,
        work_spec_marker,
        capsule_marker,
        credential_marker,
        endpoint_marker,
        model_marker,
    )
    rows: list[object] = [row]
    fetch_error: Exception | None = None
    close_error: Exception | None = None
    execute_error: Exception | None = None
    if failure_mode == "execute":
        execute_error = sqlite3.OperationalError(f"{marker_prefix}-RAW-EXECUTE")
        execute_error.sqlite_errorcode = sqlite3.SQLITE_ERROR  # type: ignore[attr-defined]
    elif failure_mode == "fetch":
        fetch_error = RuntimeError(f"{marker_prefix}-RAW-FETCH")
    elif failure_mode == "close_after_success":
        close_error = RuntimeError(f"{marker_prefix}-RAW-CLOSE")
    else:
        fetch_error = sqlite3.OperationalError(f"{marker_prefix}-RAW-FETCH")
        fetch_error.sqlite_errorcode = sqlite3.SQLITE_ERROR  # type: ignore[attr-defined]
        close_error = RuntimeError(f"{marker_prefix}-RAW-CLOSE")
    cursor = _PrivacyCursor(
        rows=rows,
        fetch_error=fetch_error,
        close_error=close_error,
    )
    connection = sqlite3.connect(":memory:", factory=_PrivacyConnection)
    assert type(connection) is _PrivacyConnection
    connection.scripted_cursor = cursor
    connection.execute_error = execute_error
    connection.execute_arguments = []
    capability = _SupportCapability(connection)
    prohibited = (
        capability,
        connection,
        cursor,
        sql,
        parameter,
        rows,
        row,
        row_value,
        mapping_value,
        decoded_value,
        work_spec_marker,
        capsule_marker,
        credential_marker,
        endpoint_marker,
        model_marker,
    )
    prohibited_text = tuple(
        value
        for value in prohibited
        if type(value) is str
    )
    try:
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            _execute_select_fetch_bounded(
                capability=capability,
                sql=sql,
                parameters=(parameter,),
                limit=2,
            )
        _assert_safe_error(
            exc_info.value,
            expected_error,
            prohibited=prohibited,
            prohibited_text=prohibited_text,
        )
    finally:
        connection.close()
    assert capability.borrow_count == 1
    assert len(connection.execute_arguments) == 1
    assert cursor.fetch_limits == ([] if failure_mode == "execute" else [2])
    assert cursor.close_count == expected_close_count


def test_all_twelve_roles_execute_through_real_nominal_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    observed: dict[str, object] = {}

    def probe(capability: object) -> None:
        observed["receipt"] = readers._read_development_mutation_receipt_by_mutation_ref(capability, "mutation-1")
        observed["decision"] = readers._read_development_decision_by_decision_ref(capability, "decision-1")
        observed["program"] = readers._read_development_program_head_and_current_version(capability, "program-1")
        observed["initialize"] = readers._read_development_initialize_decision_and_resulting_version(capability, "program-1", "decision-1")
        observed["intent"] = readers._read_development_accepted_intent_revision_by_exact_ref(capability, "program-1", "intent-1")
        observed["work"] = readers._read_development_work_item_head_and_revision_by_exact_ref(capability, "program-1", "work-0000", "revision-0000")
        observed["membership"] = readers._read_development_paged_program_version_membership(capability, "program-1", "version-1", 1)
        observed["work_spec"] = readers._read_development_work_spec_safe_binding(capability, "program-1", "version-1", "work-0000", "revision-0000")
        observed["effect"] = readers._read_development_attempt_fence_command_effect_aggregate(capability, "program-1", "attempt-1", "effect-1")
        observed["authority"] = readers._read_development_authority_evaluation_by_exact_ref(capability, "program-1", "evaluation-1")
        observed["effect_head"] = readers._read_development_effect_head(capability, "program-1", "effect-1")
        observed["delivery"] = readers._read_development_delivery_head(capability, "program-1", "effect-1")

    _run_with_real_capability(location, monkeypatch, probe)
    assert observed["receipt"].mutation_ref == "mutation-1"
    assert not hasattr(observed["receipt"], "graph_verified")
    assert not hasattr(observed["receipt"], "graph_entries")
    assert observed["decision"].decision_ref == "decision-1"
    assert observed["program"].current_program_version.program_version_ref == "version-1"
    assert observed["initialize"].initialize_decision.decision_variant == "program_genesis"
    assert observed["intent"].accepted_intent_revision_ref == "intent-1"
    assert observed["work"].is_current is True
    assert len(observed["membership"].entries) == 1
    assert observed["work_spec"].safe_projection.work_spec_ref == "work-spec-1"
    assert not hasattr(observed["work_spec"], "objective")
    assert observed["effect"].current_effect_fence is observed["effect"].author_effect_fence
    assert not hasattr(observed["effect"], "authorized")
    assert observed["authority"].authority_evaluation_ref == "evaluation-1"
    assert not hasattr(observed["authority"], "authorized")
    assert observed["effect_head"].current_effect_fence_ref == "effect-fence-1"
    assert observed["delivery"].current_delivery_attempt.delivery_attempt_ref == "delivery-1"


def test_mutation_receipt_reader_never_infers_or_verifies_an_empty_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    graph_calls: list[str] = []

    def forbidden_graph_primitive(**kwargs: object) -> object:
        graph_calls.append("graph")
        raise AssertionError("C2B2_RECEIPT_READER_MUST_NOT_INFER_GRAPH")

    with monkeypatch.context() as scoped:
        scoped.setattr(
            decision_rows,
            "compute_development_mutation_graph_digest",
            forbidden_graph_primitive,
        )
        scoped.setattr(
            decision_rows,
            "require_development_mutation_graph_digest_matches_supplied_entries",
            forbidden_graph_primitive,
        )
        observed: list[object] = []
        _run_with_real_capability(
            location,
            scoped,
            lambda capability: observed.append(
                readers._read_development_mutation_receipt_by_mutation_ref(
                    capability,
                    "mutation-1",
                )
            ),
        )
    assert graph_calls == []
    assert len(observed) == 1
    receipt = observed[0]
    for forbidden_attribute in (
        "graph_entries",
        "graph_verified",
        "family_complete",
        "referenced_rows_exist",
        "replay",
        "recovery",
    ):
        assert not hasattr(receipt, forbidden_attribute)

    module = ast.parse(READERS_PATH.read_text(encoding="utf-8"))
    load_node = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_load_development_mutation_receipt_by_mutation_ref"
    )
    forbidden_fragments = (
        "graph_entries",
        "graph_verified",
        "family_complete",
        "referenced_rows_exist",
        "replay",
        "recovery",
    )
    for node in ast.walk(load_node):
        if isinstance(node, ast.Name):
            assert all(fragment not in node.id for fragment in forbidden_fragments)
        if isinstance(node, ast.Attribute):
            assert all(fragment not in node.attr for fragment in forbidden_fragments)
        assert not (isinstance(node, ast.Tuple) and len(node.elts) == 0)


def test_historical_work_revision_is_valid_and_not_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    observed: list[object] = []
    _run_with_real_capability(
        location,
        monkeypatch,
        lambda capability: observed.append(
            readers._read_development_work_item_head_and_revision_by_exact_ref(
                capability,
                "program-1",
                "work-history",
                "revision-history-1",
            )
        ),
    )
    assert observed[0].work_item_revision.work_item_revision_number == 1
    assert observed[0].is_current is False


@pytest.mark.parametrize("member_count", (1, 256, 257, 600))
def test_membership_completes_one_exact_and_multiple_pages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    member_count: int,
) -> None:
    location, _ = _seed_database(tmp_path, member_count=member_count)
    observed: list[object] = []
    query_ids: list[str] = []
    original_execute = readers._execute_select_fetch_bounded
    query_by_sql = {
        contracts._PROGRAM_VERSION_ROOT_SELECT.sql: "root",
        contracts._MEMBERSHIP_FIRST_PAGE_SELECT.sql: "first",
        contracts._MEMBERSHIP_CONTINUATION_PAGE_SELECT.sql: "continuation",
        contracts._MEMBERSHIP_WORK_ITEM_REVISION_SELECT.sql: "child",
    }

    def capture_execute(**kwargs: object) -> list[object]:
        query_ids.append(query_by_sql.get(str(kwargs["sql"]), "other"))
        return original_execute(**kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(readers, "_execute_select_fetch_bounded", capture_execute)
        _run_with_real_capability(
            location,
            scoped,
            lambda capability: observed.append(
                readers._read_development_paged_program_version_membership(
                    capability,
                    "program-1",
                    "version-1",
                    member_count,
                )
            ),
        )
    aggregate = observed[0]
    assert len(aggregate.entries) == member_count
    assert not hasattr(aggregate, "continuation")
    assert tuple(entry.membership.membership_ordinal for entry in aggregate.entries) == tuple(range(member_count))
    assert query_ids[0:2] == ["root", "first"]
    assert query_ids.count("continuation") == (0 if member_count <= 256 else (member_count - 1) // 256)
    assert query_ids.count("child") == member_count


def test_membership_maximum_fails_before_any_child_query_for_excess_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path, member_count=257)
    query_sql: list[str] = []
    original_execute = readers._execute_select_fetch_bounded

    def capture_execute(**kwargs: object) -> list[object]:
        query_sql.append(str(kwargs["sql"]))
        return original_execute(**kwargs)

    def probe(capability: object) -> None:
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            readers._read_development_paged_program_version_membership(
                capability,
                "program-1",
                "version-1",
                256,
            )
        _assert_safe_error(exc_info.value, "mutation_failed")

    with monkeypatch.context() as scoped:
        scoped.setattr(readers, "_execute_select_fetch_bounded", capture_execute)
        _run_with_real_capability(location, scoped, probe)
    assert contracts._MEMBERSHIP_WORK_ITEM_REVISION_SELECT.sql not in query_sql
    assert contracts._MEMBERSHIP_CONTINUATION_PAGE_SELECT.sql in query_sql


def test_role_nine_same_and_distinct_fences_use_exact_query_order_without_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    observed: list[object] = []
    query_ids: list[str] = []
    original_execute = readers._execute_select_fetch_bounded
    query_by_sql = {
        specification.sql: specification.query_id
        for specification in (
            contracts._EFFECT_INTENT_ROOT_SELECT,
            contracts._SEMANTIC_ATTEMPT_SELECT,
            contracts._AUTHOR_COMMAND_SELECT,
            contracts._ATTEMPT_FENCE_SELECT,
            contracts._CURRENT_EFFECT_FENCE_SELECT,
            contracts._AUTHOR_EFFECT_FENCE_SELECT,
            contracts._AUTHORITY_EVALUATION_SELECT,
        )
    }

    def capture_execute(**kwargs: object) -> list[object]:
        query_ids.append(query_by_sql[str(kwargs["sql"])])
        return original_execute(**kwargs)

    def probe(capability: object) -> None:
        observed.append(readers._read_development_attempt_fence_command_effect_aggregate(capability, "program-1", "attempt-1", "effect-1"))
        observed.append(readers._read_development_attempt_fence_command_effect_aggregate(capability, "program-1", "attempt-1", "effect-bound"))

    with monkeypatch.context() as scoped:
        scoped.setattr(readers, "_execute_select_fetch_bounded", capture_execute)
        _run_with_real_capability(location, scoped, probe)
    assert observed[0].current_effect_fence is observed[0].author_effect_fence
    assert observed[1].current_effect_fence is not observed[1].author_effect_fence
    assert query_ids == [
        "effect_intent_root", "semantic_attempt", "author_command", "attempt_fence", "current_effect_fence",
        "effect_intent_root", "semantic_attempt", "author_command", "attempt_fence", "current_effect_fence", "author_effect_fence",
    ]
    assert "authority_evaluation" not in query_ids
    for aggregate in observed:
        assert not hasattr(aggregate, "capsule")
        assert not hasattr(aggregate, "execution_permission")


def test_role_ten_selects_exact_ref_among_same_subject_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    observed: list[object] = []

    def probe(capability: object) -> None:
        observed.append(readers._read_development_authority_evaluation_by_exact_ref(capability, "program-1", "evaluation-1"))
        observed.append(readers._read_development_authority_evaluation_by_exact_ref(capability, "program-1", "evaluation-2"))

    _run_with_real_capability(location, monkeypatch, probe)
    assert [value.authority_evaluation_ref for value in observed] == ["evaluation-1", "evaluation-2"]
    assert [value.authority_state for value in observed] == ["verified", "pending"]


@pytest.mark.parametrize(
    "bad_ref",
    (None, "", "bad/ref", "user-secret", "x" * 97, _StrSubclass(PRIVATE_SENTINEL)),
)
def test_malformed_lookup_fails_before_nominal_import_borrow_or_sql(
    monkeypatch: pytest.MonkeyPatch,
    bad_ref: object,
) -> None:
    calls: list[str] = []
    stand_in = _StructuralStandIn()

    def forbidden_execute(**kwargs: object) -> list[object]:
        calls.append("sql")
        return []

    monkeypatch.setattr(readers, "_execute_select_fetch_bounded", forbidden_execute)
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        readers._read_development_effect_head(stand_in, bad_ref, "effect-1")
    prohibited = (bad_ref,) if type(bad_ref) is _StrSubclass else ()
    prohibited_text = (PRIVATE_SENTINEL,) if type(bad_ref) is _StrSubclass else ()
    _assert_safe_error(
        exc_info.value,
        "database_integrity_failure",
        prohibited=prohibited,
        prohibited_text=prohibited_text,
    )
    assert stand_in.borrow_count == 0
    assert calls == []


@pytest.mark.parametrize(
    ("role", "position"),
    (
        (1, "mutation_ref"),
        (2, "decision_ref"),
        (3, "program_ref"),
        (4, "program_ref"),
        (4, "decision_ref"),
        (5, "program_ref"),
        (5, "accepted_intent_revision_ref"),
        (6, "program_ref"),
        (6, "work_item_ref"),
        (6, "work_item_revision_ref"),
        (7, "program_ref"),
        (7, "program_version_ref"),
        (8, "program_ref"),
        (8, "program_version_ref"),
        (8, "work_item_ref"),
        (8, "work_item_revision_ref"),
        (9, "program_ref"),
        (9, "semantic_attempt_ref"),
        (9, "effect_intent_ref"),
        (10, "program_ref"),
        (10, "authority_evaluation_ref"),
        (11, "program_ref"),
        (11, "effect_intent_ref"),
        (12, "program_ref"),
        (12, "effect_intent_ref"),
    ),
)
def test_real_str_subclass_is_rejected_in_every_lookup_position_before_sql(
    monkeypatch: pytest.MonkeyPatch,
    role: int,
    position: str,
) -> None:
    bad = _StrSubclass(f"{PRIVATE_SENTINEL}-{role}-{position}")
    stand_in = _StructuralStandIn()
    calls: list[str] = []
    monkeypatch.setattr(
        readers,
        "_execute_select_fetch_bounded",
        lambda **kwargs: calls.append("sql"),
    )
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        if role == 1:
            readers._read_development_mutation_receipt_by_mutation_ref(stand_in, bad)
        elif role == 2:
            readers._read_development_decision_by_decision_ref(stand_in, bad)
        elif role == 3:
            readers._read_development_program_head_and_current_version(stand_in, bad)
        elif role == 4:
            readers._read_development_initialize_decision_and_resulting_version(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "decision_ref" else "decision-1",
            )
        elif role == 5:
            readers._read_development_accepted_intent_revision_by_exact_ref(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad
                if position == "accepted_intent_revision_ref"
                else "intent-1",
            )
        elif role == 6:
            readers._read_development_work_item_head_and_revision_by_exact_ref(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "work_item_ref" else "work-0000",
                bad
                if position == "work_item_revision_ref"
                else "revision-0000",
            )
        elif role == 7:
            readers._read_development_paged_program_version_membership(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "program_version_ref" else "version-1",
                1,
            )
        elif role == 8:
            readers._read_development_work_spec_safe_binding(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "program_version_ref" else "version-1",
                bad if position == "work_item_ref" else "work-0000",
                bad
                if position == "work_item_revision_ref"
                else "revision-0000",
            )
        elif role == 9:
            readers._read_development_attempt_fence_command_effect_aggregate(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "semantic_attempt_ref" else "attempt-1",
                bad if position == "effect_intent_ref" else "effect-1",
            )
        elif role == 10:
            readers._read_development_authority_evaluation_by_exact_ref(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad
                if position == "authority_evaluation_ref"
                else "evaluation-1",
            )
        elif role == 11:
            readers._read_development_effect_head(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "effect_intent_ref" else "effect-1",
            )
        else:
            readers._read_development_delivery_head(
                stand_in,
                bad if position == "program_ref" else "program-1",
                bad if position == "effect_intent_ref" else "effect-1",
            )
    _assert_safe_error(
        exc_info.value,
        "database_integrity_failure",
        prohibited=(bad, stand_in),
        prohibited_text=(str(bad),),
    )
    assert stand_in.borrow_count == 0
    assert calls == []


@pytest.mark.parametrize("bad_maximum", (True, False, 0, -1, _IntSubclass(2)))
def test_malformed_maximum_members_fails_before_borrow_or_sql(
    monkeypatch: pytest.MonkeyPatch,
    bad_maximum: object,
) -> None:
    stand_in = _StructuralStandIn()
    calls: list[str] = []
    monkeypatch.setattr(readers, "_execute_select_fetch_bounded", lambda **kwargs: calls.append("sql"))
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        readers._read_development_paged_program_version_membership(
            stand_in,
            "program-1",
            "version-1",
            bad_maximum,
        )
    _assert_safe_error(exc_info.value, "database_integrity_failure")
    assert stand_in.borrow_count == 0
    assert calls == []


@pytest.mark.parametrize("invalid_form", ("none", "object", "raw_connection"))
def test_wrong_capability_forms_fail_before_select(
    monkeypatch: pytest.MonkeyPatch,
    invalid_form: str,
) -> None:
    invalid_capability: object
    if invalid_form == "none":
        invalid_capability = None
    elif invalid_form == "object":
        invalid_capability = object()
    else:
        invalid_capability = sqlite3.connect(":memory:")
    calls: list[str] = []
    monkeypatch.setattr(readers, "_execute_select_fetch_bounded", lambda **kwargs: calls.append("sql"))
    try:
        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            readers._read_development_effect_head(invalid_capability, "program-1", "effect-1")
        _assert_safe_capability_error(
            exc_info.value,
            _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE,
            prohibited=() if invalid_capability is None else (invalid_capability,),
        )
        assert calls == []
    finally:
        if type(invalid_capability) is sqlite3.Connection:
            invalid_capability.close()


def test_structural_forged_and_nominal_subclass_forms_never_reach_borrow_or_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stand_in = _StructuralStandIn()

    class NominalSubclass(transaction_module._SQLiteMutationReadCapability):
        pass

    nominal_subclass_instance = object.__new__(NominalSubclass)
    calls: list[str] = []
    monkeypatch.setattr(
        readers,
        "_execute_select_fetch_bounded",
        lambda **kwargs: calls.append("sql"),
    )
    for invalid in (stand_in, nominal_subclass_instance):
        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            readers._read_development_effect_head(invalid, "program-1", "effect-1")
        _assert_safe_capability_error(
            exc_info.value,
            _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE,
            prohibited=(invalid,),
        )
    assert stand_in.borrow_count == 0
    assert calls == []


def test_expired_wrong_thread_and_wrong_process_capability_failures_are_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    thread_errors: list[_MutationReadCapabilityError] = []
    process_results: list[str] = []

    def probe(capability: object) -> None:
        def wrong_thread() -> None:
            try:
                readers._read_development_effect_head(capability, "program-1", "effect-1")
            except _MutationReadCapabilityError as error:
                thread_errors.append(error)

        thread = threading.Thread(target=wrong_thread)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
        if hasattr(os, "fork"):
            read_fd, write_fd = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(read_fd)
                try:
                    try:
                        readers._read_development_effect_head(capability, "program-1", "effect-1")
                    except _MutationReadCapabilityError as error:
                        payload = error.reason.value
                    else:
                        payload = "unexpected-success"
                    os.write(write_fd, payload.encode("ascii"))
                finally:
                    os.close(write_fd)
                    os._exit(0)
            os.close(write_fd)
            payload = os.read(read_fd, 128).decode("ascii")
            os.close(read_fd)
            os.waitpid(child, 0)
            process_results.append(payload)

    expired = _run_with_real_capability(location, monkeypatch, probe)
    assert len(thread_errors) == 1
    _assert_safe_capability_error(
        thread_errors[0],
        _MutationReadCapabilityFailureReason.THREAD_MISMATCH,
        prohibited=(expired,),
    )
    if hasattr(os, "fork"):
        assert process_results == [_MutationReadCapabilityFailureReason.PROCESS_MISMATCH.value]
    with pytest.raises(_MutationReadCapabilityError) as exc_info:
        readers._read_development_effect_head(expired, "program-1", "effect-1")
    _assert_safe_capability_error(
        exc_info.value,
        _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED,
        prohibited=(expired,),
    )


ROLE_9_RELATION_CASES = (
    ("semantic_program", "semantic", "program_ref", "program-other"),
    ("semantic_ref", "semantic", "semantic_attempt_ref", "attempt-other"),
    ("intent_program_version", "intent", "program_version_ref", "version-other"),
    ("intent_candidate", "intent", "candidate_ref", "candidate-other"),
    ("command_program", "command", "program_ref", "program-other"),
    ("intent_to_command", "intent", "command_ref", "command-other"),
    ("command_program_version", "command", "program_version_ref", "version-other"),
    ("command_accepted_intent", "command", "accepted_intent_revision_ref", "intent-other"),
    ("command_work_item", "command", "work_item_ref", "work-other"),
    ("command_work_revision", "command", "work_item_revision_ref", "revision-other"),
    ("command_semantic_attempt", "command", "semantic_attempt_ref", "attempt-other"),
    ("command_candidate", "command", "candidate_ref", "candidate-other"),
    ("attempt_program", "attempt", "program_ref", "program-other"),
    ("attempt_program_version", "attempt", "program_version_ref", "version-other"),
    ("attempt_accepted_intent", "attempt", "accepted_intent_revision_ref", "intent-other"),
    ("attempt_work_item", "attempt", "work_item_ref", "work-other"),
    ("attempt_work_revision", "attempt", "work_item_revision_ref", "revision-other"),
    ("attempt_semantic_attempt", "attempt", "semantic_attempt_ref", "attempt-other"),
    ("command_repository", "command", "repository_ref", "repository-other"),
    ("command_base_format", "command", "base_git_object_format", "sha256"),
    ("command_base_oid", "command", "base_git_oid", "b" * 40),
    ("command_path", "command_inner", "path_ceiling", ("PLANS.md",)),
    ("command_standing_grant_ref", "command", "standing_grant_ref", "grant-other"),
    ("command_standing_grant_digest", "command", "standing_grant_digest", "b" * 64),
    ("command_attempt_authorization_ref", "command", "attempt_authorization_ref", "authorization-other"),
    ("command_attempt_authorization_digest", "command", "attempt_authorization_digest", "b" * 64),
    ("command_attempt_fence_ref", "command", "attempt_fence_ref", "attempt-fence-other"),
    ("command_attempt_fence_digest", "command", "attempt_fence_digest", "b" * 64),
    ("command_global_stop_ref", "command", "global_stop_ref", "stop-other"),
    ("command_global_stop_version", "command", "global_stop_version", 1),
    ("command_no_wider_ceiling", "ceilings", "call", 1),
    ("current_program", "current", "program_ref", "program-other"),
    ("current_program_version", "current", "program_version_ref", "version-other"),
    ("current_accepted_intent", "current", "accepted_intent_revision_ref", "intent-other"),
    ("current_work_item", "current", "work_item_ref", "work-other"),
    ("current_work_revision", "current", "work_item_revision_ref", "revision-other"),
    ("current_semantic_attempt", "current", "semantic_attempt_ref", "attempt-other"),
    ("current_effect_intent", "current", "effect_intent_ref", "effect-other"),
    ("current_effect_class", "current", "effect_class", "author_candidate"),
    ("current_command_ref", "current", "command_ref", "command-other"),
    ("current_command_digest", "current", "command_digest", "b" * 64),
    ("current_candidate", "current", "candidate_ref", "candidate-other"),
    ("current_repository", "current", "repository_ref", "repository-other"),
    ("current_base_format", "current", "base_git_object_format", "sha256"),
    ("current_base_oid", "current", "base_git_oid", "b" * 40),
    ("current_path", "current_inner", "path_ceiling", ("PLANS.md",)),
    ("current_standing_grant_ref", "current", "parent_standing_grant_ref", "grant-other"),
    ("current_standing_grant_digest", "current", "parent_standing_grant_digest", "b" * 64),
    ("current_attempt_fence_ref", "current", "attempt_fence_ref", "attempt-fence-other"),
    ("current_attempt_fence_digest", "current", "attempt_fence_digest", "b" * 64),
    ("current_global_stop_ref", "current", "global_stop_ref", "stop-other"),
    ("current_global_stop_version", "current", "global_stop_version", 1),
    ("current_no_wider_ceiling", "ceilings", "call", 2),
    ("current_allowed_effect", "current", "effect_class", "cancel_effect"),
    ("current_expiry", "current", "expires_at", "2026-08-17T12:34:56Z"),
    ("author_program", "author", "program_ref", "program-other"),
    ("author_program_version", "author", "program_version_ref", "version-other"),
    ("author_accepted_intent", "author", "accepted_intent_revision_ref", "intent-other"),
    ("author_work_item", "author", "work_item_ref", "work-other"),
    ("author_work_revision", "author", "work_item_revision_ref", "revision-other"),
    ("author_semantic_attempt", "author", "semantic_attempt_ref", "attempt-other"),
    ("author_effect_intent", "author", "effect_intent_ref", "effect-other"),
    ("author_effect_class", "author", "effect_class", "validate_candidate"),
    ("author_command_ref", "author", "command_ref", "command-other"),
    ("author_command_digest", "author", "command_digest", "b" * 64),
    ("author_candidate", "author", "candidate_ref", "candidate-other"),
    ("author_repository", "author", "repository_ref", "repository-other"),
    ("author_base_format", "author", "base_git_object_format", "sha256"),
    ("author_base_oid", "author", "base_git_oid", "b" * 40),
    ("author_path", "author_inner", "path_ceiling", ("PLANS.md",)),
    ("author_effect_authorization_ref", "author", "effect_authorization_ref", "authorization-other"),
    ("author_effect_authorization_digest", "author", "effect_authorization_digest", "b" * 64),
    ("author_attempt_fence_ref", "author", "attempt_fence_ref", "attempt-fence-other"),
    ("author_attempt_fence_digest", "author", "attempt_fence_digest", "b" * 64),
    ("author_effect_fence_ref", "author", "effect_fence_ref", "effect-fence-other"),
    ("author_effect_fence_digest", "author", "effect_fence_digest", "e" * 64),
    ("author_ceiling_equality", "author_inner", "effect_ceilings", "smaller"),
    ("author_no_wider_ceiling", "ceilings", "call", 3),
    ("author_global_stop_ref", "author", "global_stop_ref", "stop-other"),
    ("author_global_stop_version", "author", "global_stop_version", 1),
    ("author_standing_grant_ref", "author", "parent_standing_grant_ref", "grant-other"),
    ("author_standing_grant_digest", "author", "parent_standing_grant_digest", "b" * 64),
    ("author_expiry", "author", "expires_at", "2026-08-17T12:34:56Z"),
    ("author_candidate_same_fence", "special", "same_fence", True),
)


def _role_nine_test_values() -> tuple[SimpleNamespace, ...]:
    ceilings = CeilingsV1.create(**CEILINGS)
    command_inner = SimpleNamespace(
        path_ceiling=PATHS,
        effect_ceilings=ceilings,
    )
    attempt_inner = SimpleNamespace(
        path_ceiling=PATHS,
        aggregate_ceilings=ceilings,
        allowed_effect_classes=("author_candidate", "validate_candidate"),
    )
    current_inner = SimpleNamespace(path_ceiling=PATHS, effect_ceilings=ceilings)
    author_inner = SimpleNamespace(path_ceiling=PATHS, effect_ceilings=ceilings)
    semantic = SimpleNamespace(
        program_ref="program-1",
        semantic_attempt_ref="attempt-1",
        program_version_ref="version-1",
        accepted_intent_revision_ref="intent-1",
        work_item_ref="work-0000",
        work_item_revision_ref="revision-0000",
        candidate_ref="candidate-1",
    )
    intent = SimpleNamespace(
        program_ref="program-1",
        effect_intent_ref="effect-bound",
        semantic_attempt_ref="attempt-1",
        program_version_ref="version-1",
        candidate_ref="candidate-1",
        command_ref="command-1",
        effect_class="validate_candidate",
    )
    command = SimpleNamespace(
        program_ref="program-1",
        command_ref="command-1",
        program_version_ref="version-1",
        accepted_intent_revision_ref="intent-1",
        work_item_ref="work-0000",
        work_item_revision_ref="revision-0000",
        semantic_attempt_ref="attempt-1",
        effect_intent_ref="effect-1",
        candidate_ref="candidate-1",
        repository_ref="repository-1",
        base_git_object_format="sha1",
        base_git_oid=OID,
        author_command=command_inner,
        standing_grant_ref="grant-1",
        standing_grant_digest="3" * 64,
        attempt_authorization_ref="attempt-authorization-1",
        attempt_authorization_digest="4" * 64,
        effect_authorization_ref="effect-authorization-1",
        effect_authorization_digest="5" * 64,
        attempt_fence_ref="attempt-fence-1",
        attempt_fence_digest="a" * 64,
        effect_fence_ref="effect-fence-1",
        effect_fence_digest="b" * 64,
        global_stop_ref="stop-1",
        global_stop_version=0,
        command_digest="c" * 64,
    )
    attempt = SimpleNamespace(
        program_ref="program-1",
        program_version_ref="version-1",
        accepted_intent_revision_ref="intent-1",
        work_item_ref="work-0000",
        work_item_revision_ref="revision-0000",
        semantic_attempt_ref="attempt-1",
        repository_ref="repository-1",
        base_git_object_format="sha1",
        base_git_oid=OID,
        attempt_fence=attempt_inner,
        parent_standing_grant_ref="grant-1",
        parent_standing_grant_digest="3" * 64,
        attempt_authorization_ref="attempt-authorization-1",
        attempt_authorization_digest="4" * 64,
        attempt_fence_ref="attempt-fence-1",
        attempt_fence_digest="a" * 64,
        global_stop_ref="stop-1",
        global_stop_version=0,
        expires_at=EXPIRES,
    )

    def fence(
        *,
        fence_ref: str,
        intent_ref: str,
        effect_class: str,
        authorization_ref: str,
        authorization_digest: str,
        inner: SimpleNamespace,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            program_ref="program-1",
            program_version_ref="version-1",
            accepted_intent_revision_ref="intent-1",
            work_item_ref="work-0000",
            work_item_revision_ref="revision-0000",
            semantic_attempt_ref="attempt-1",
            effect_intent_ref=intent_ref,
            effect_class=effect_class,
            command_ref="command-1",
            command_digest="c" * 64,
            candidate_ref="candidate-1",
            repository_ref="repository-1",
            base_git_object_format="sha1",
            base_git_oid=OID,
            effect_fence=inner,
            parent_standing_grant_ref="grant-1",
            parent_standing_grant_digest="3" * 64,
            effect_authorization_ref=authorization_ref,
            effect_authorization_digest=authorization_digest,
            attempt_fence_ref="attempt-fence-1",
            attempt_fence_digest="a" * 64,
            effect_fence_ref=fence_ref,
            effect_fence_digest=("d" if effect_class == "validate_candidate" else "b") * 64,
            global_stop_ref="stop-1",
            global_stop_version=0,
            expires_at=EXPIRES,
        )

    current = fence(
        fence_ref="effect-fence-bound",
        intent_ref="effect-bound",
        effect_class="validate_candidate",
        authorization_ref="effect-authorization-bound",
        authorization_digest="8" * 64,
        inner=current_inner,
    )
    author = fence(
        fence_ref="effect-fence-1",
        intent_ref="effect-1",
        effect_class="author_candidate",
        authorization_ref="effect-authorization-1",
        authorization_digest="5" * 64,
        inner=author_inner,
    )
    return (
        semantic,
        intent,
        command,
        attempt,
        current,
        author,
        command_inner,
        attempt_inner,
        current_inner,
        author_inner,
    )


def _scripted_probe(
    location: CoordinatorStateLocation,
    monkeypatch: pytest.MonkeyPatch,
    responses: list[list[object]],
    invocation: Callable[[object], object],
) -> tuple[object | None, BaseException | None, int]:
    result: object | None = None
    error: BaseException | None = None
    call_count = 0

    def scripted_execute(**kwargs: object) -> list[object]:
        nonlocal call_count
        call_count += 1
        if not responses:
            raise AssertionError("C2B2_PRIVATE_READER_UNEXPECTED_SQL")
        return responses.pop(0)

    def probe(capability: object) -> None:
        nonlocal result, error
        try:
            result = invocation(capability)
        except (SQLiteMutationStoreError, _MutationReadCapabilityError) as caught:
            error = caught

    with monkeypatch.context() as scoped:
        scoped.setattr(readers, "_execute_select_fetch_bounded", scripted_execute)
        _run_with_real_capability(location, scoped, probe)
    return result, error, call_count


@pytest.mark.parametrize("role", (1, 2, 5, 8, 10, 11))
@pytest.mark.parametrize("row_case", ("zero", "one", "two", "malformed"))
def test_singleton_reader_cardinality_matrix_is_independently_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    role: int,
    row_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    if role == 1:
        row = rows["receipt"]
    elif role == 2:
        row = rows["decision"]
    elif role == 5:
        row = rows["accepted_intent"]
    elif role == 8:
        row = rows["work_spec_binding"]
    elif role == 10:
        row = rows["authority_evaluation"]
    else:
        row = rows["effect_head"]
    if row_case == "zero":
        response: list[object] = []
    elif row_case == "one":
        response = [row]
    elif row_case == "two":
        response = [row, row]
    else:
        response = [row[:-1]]

    def invoke(capability: object) -> object:
        if role == 1:
            return readers._read_development_mutation_receipt_by_mutation_ref(
                capability,
                "mutation-1",
            )
        if role == 2:
            return readers._read_development_decision_by_decision_ref(
                capability,
                "decision-1",
            )
        if role == 5:
            return readers._read_development_accepted_intent_revision_by_exact_ref(
                capability,
                "program-1",
                "intent-1",
            )
        if role == 8:
            return readers._read_development_work_spec_safe_binding(
                capability,
                "program-1",
                "version-1",
                "work-0000",
                "revision-0000",
            )
        if role == 10:
            return readers._read_development_authority_evaluation_by_exact_ref(
                capability,
                "program-1",
                "evaluation-1",
            )
        return readers._read_development_effect_head(
            capability,
            "program-1",
            "effect-1",
        )

    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [response],
        invoke,
    )
    assert count == 1
    if row_case == "zero":
        assert result is None and error is None
    elif row_case == "one":
        assert result is not None and error is None
    else:
        assert result is None
        assert type(error) is SQLiteMutationStoreError
        _assert_safe_error(
            error,
            "database_integrity_failure",
            prohibited=(row, response),
        )


@pytest.mark.parametrize("role", (3, 4, 6, 7, 9, 12))
@pytest.mark.parametrize("root_case", ("absent", "duplicate", "malformed"))
def test_aggregate_reader_root_matrix_stops_before_child_sql(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    role: int,
    root_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    if role == 3:
        root = rows["program_head"]
    elif role == 4:
        root = rows["decision"]
    elif role == 6:
        root = rows["work_head"]
    elif role == 7:
        root = rows["program_version"]
    elif role == 9:
        root = rows["author_intent"]
    else:
        root = rows["delivery_head"]
    if root_case == "absent":
        response: list[object] = []
    elif root_case == "duplicate":
        response = [root, root]
    else:
        response = [root[:-1]]

    def invoke(capability: object) -> object:
        if role == 3:
            return readers._read_development_program_head_and_current_version(
                capability,
                "program-1",
            )
        if role == 4:
            return readers._read_development_initialize_decision_and_resulting_version(
                capability,
                "program-1",
                "decision-1",
            )
        if role == 6:
            return readers._read_development_work_item_head_and_revision_by_exact_ref(
                capability,
                "program-1",
                "work-0000",
                "revision-0000",
            )
        if role == 7:
            return readers._read_development_paged_program_version_membership(
                capability,
                "program-1",
                "version-1",
                2,
            )
        if role == 9:
            return readers._read_development_attempt_fence_command_effect_aggregate(
                capability,
                "program-1",
                "attempt-1",
                "effect-1",
            )
        return readers._read_development_delivery_head(
            capability,
            "program-1",
            "effect-1",
        )

    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [response],
        invoke,
    )
    assert count == 1
    assert result is None
    if root_case == "absent":
        assert error is None
    else:
        assert type(error) is SQLiteMutationStoreError
        _assert_safe_error(
            error,
            "database_integrity_failure",
            prohibited=(root, response),
        )


@pytest.mark.parametrize("root_case", ("absent", "duplicate", "wrong_length", "wrong_digest", "reordered"))
def test_root_cardinality_and_malformed_row_precedence_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    root_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    root = rows["program_head"]
    if root_case == "absent":
        response = []
    elif root_case == "duplicate":
        response = [root, root]
    elif root_case == "wrong_length":
        response = [root[:-1]]
    elif root_case == "wrong_digest":
        response = [root[:-1] + ("0" * 64,)]
    else:
        reordered = list(root)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        response = [tuple(reordered)]
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [response],
        lambda capability: readers._read_development_program_head_and_current_version(
            capability,
            "program-1",
        ),
    )
    assert result is None
    assert count == 1
    if root_case == "absent":
        assert error is None
    else:
        assert type(error) is SQLiteMutationStoreError
        _assert_safe_error(error, "database_integrity_failure")


@pytest.mark.parametrize("child_case", ("missing", "duplicate", "wrong_length", "wrong_digest", "relation"))
def test_required_child_cardinality_malformed_and_relation_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    child = rows["program_version"]
    if child_case == "missing":
        response: list[object] = []
    elif child_case == "duplicate":
        response = [child, child]
    elif child_case == "wrong_length":
        response = [child[:-1]]
    elif child_case == "wrong_digest":
        response = [child[:-1] + ("0" * 64,)]
    else:
        response = [_program_version_row(program_ref="program-other", program_version_ref="version-other")]
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [[rows["program_head"]], response],
        lambda capability: readers._read_development_program_head_and_current_version(
            capability,
            "program-1",
        ),
    )
    assert result is None
    assert count == 2
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(error, "database_integrity_failure")


@pytest.mark.parametrize("role", (3, 4, 6, 7, 9, 12))
@pytest.mark.parametrize("child_case", ("missing", "duplicate", "malformed", "relation"))
def test_aggregate_reader_required_child_matrix_is_independently_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    role: int,
    child_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    if role == 3:
        root = rows["program_head"]
        child = rows["program_version"]
        relation_child = _program_version_row(
            program_ref="program-other",
            program_version_ref="version-1",
        )
    elif role == 4:
        root = rows["decision"]
        child = rows["program_version"]
        relation_child = _program_version_row(decision_ref="decision-other")
    elif role == 6:
        root = rows["work_head"]
        child = rows["work_revision"]
        relation_child = _work_revision_row(
            work_item_ref="work-other",
            work_item_revision_ref="revision-0000",
        )
    elif role == 7:
        root = rows["program_version"]
        child = rows["membership"]
        relation_child = _replace_digest_row_field(
            child,
            columns=program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
            field="program_version_ref",
            value="version-other",
            digest_name="membership_digest",
            domain="governed-execution.nwp-development-program-version-work-item.v1.identity",
        )
    elif role == 9:
        root = rows["author_intent"]
        child = rows["semantic_attempt"]
        relation_child = _replace_digest_row_field(
            child,
            columns=program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
            field="program_ref",
            value="program-other",
            digest_name="semantic_attempt_digest",
            domain="governed-execution.nwp-development-semantic-attempt.v1.identity",
        )
    else:
        root = _replace_digest_row_field(
            rows["delivery_head"],
            columns=effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
            field="current_delivery_attempt_ref",
            value="delivery-other",
            digest_name="head_digest",
            domain="governed-execution.nwp-development-delivery-head.v1.identity",
        )
        child = rows["delivery_attempt"]
        relation_child = child
    if child_case == "missing":
        child_response: list[object] = []
    elif child_case == "duplicate":
        child_response = [child, child]
    elif child_case == "malformed":
        child_response = [child[:-1]]
    else:
        child_response = [relation_child]
    root_response: list[object] = [root]
    scripted_responses = [root_response, child_response]
    if role == 9 and child_case == "relation":
        scripted_responses.extend(
            (
                [rows["author_command"]],
                [rows["attempt_fence"]],
                [rows["author_effect_fence"]],
            )
        )

    def invoke(capability: object) -> object:
        if role == 3:
            return readers._read_development_program_head_and_current_version(
                capability,
                "program-1",
            )
        if role == 4:
            return readers._read_development_initialize_decision_and_resulting_version(
                capability,
                "program-1",
                "decision-1",
            )
        if role == 6:
            return readers._read_development_work_item_head_and_revision_by_exact_ref(
                capability,
                "program-1",
                "work-0000",
                "revision-0000",
            )
        if role == 7:
            return readers._read_development_paged_program_version_membership(
                capability,
                "program-1",
                "version-1",
                2,
            )
        if role == 9:
            return readers._read_development_attempt_fence_command_effect_aggregate(
                capability,
                "program-1",
                "attempt-1",
                "effect-1",
            )
        return readers._read_development_delivery_head(
            capability,
            "program-1",
            "effect-1",
        )

    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        scripted_responses,
        invoke,
    )
    assert result is None
    assert count == (5 if role == 9 and child_case == "relation" else 2)
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(
        error,
        "database_integrity_failure",
        prohibited=(root, child, relation_child, root_response, child_response),
    )


@pytest.mark.parametrize(
    ("case_name", "target", "field", "replacement"),
    ROLE_9_RELATION_CASES,
)
def test_role_nine_every_frozen_relation_fails_one_at_a_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_name: str,
    target: str,
    field: str,
    replacement: object,
) -> None:
    location, _ = _seed_database(tmp_path)
    (
        semantic,
        intent,
        command,
        attempt,
        current,
        author,
        command_inner,
        attempt_inner,
        current_inner,
        author_inner,
    ) = _role_nine_test_values()
    no_wider_call_to_fail: int | None = None
    if target == "semantic":
        selected = semantic
    elif target == "intent":
        selected = intent
    elif target == "command":
        selected = command
    elif target == "attempt":
        selected = attempt
    elif target == "current":
        selected = current
    elif target == "author":
        selected = author
    elif target == "command_inner":
        selected = command_inner
    elif target == "attempt_inner":
        selected = attempt_inner
    elif target == "current_inner":
        selected = current_inner
    elif target == "author_inner":
        selected = author_inner
    elif target == "ceilings":
        selected = None
        no_wider_call_to_fail = int(replacement)
    else:
        assert target == "special"
        selected = None

    smaller_values = dict(CEILINGS)
    smaller_values["max_changed_files"] = 2
    if replacement == "smaller":
        replacement = CeilingsV1.create(**smaller_values)
    if selected is not None:
        setattr(selected, field, replacement)

    author_shadow_fields = {
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "global_stop_ref",
        "global_stop_version",
    }
    if target == "command" and field in author_shadow_fields:
        author_field = (
            "parent_standing_grant_ref"
            if field == "standing_grant_ref"
            else "parent_standing_grant_digest"
            if field == "standing_grant_digest"
            else field
        )
        setattr(author, author_field, replacement)
    if case_name == "command_path":
        author_inner.path_ceiling = replacement
    if case_name == "current_allowed_effect":
        intent.effect_class = replacement
    if case_name == "author_candidate_same_fence":
        intent.effect_intent_ref = "effect-1"
        intent.effect_class = "author_candidate"
        current.effect_intent_ref = "effect-1"
        current.effect_class = "author_candidate"
        current.effect_fence_ref = "effect-fence-current-other"

    relation_call_count = 0

    def controlled_no_wider(child: object, parent: object) -> bool:
        nonlocal relation_call_count
        relation_call_count += 1
        if relation_call_count == no_wider_call_to_fail:
            return False
        return True

    root_token = (f"{PRIVATE_SENTINEL}-{case_name}-ROOT",)
    semantic_token = (f"{PRIVATE_SENTINEL}-{case_name}-SEMANTIC",)
    command_token = (f"{PRIVATE_SENTINEL}-{case_name}-COMMAND",)
    attempt_token = (f"{PRIVATE_SENTINEL}-{case_name}-ATTEMPT",)
    current_token = (f"{PRIVATE_SENTINEL}-{case_name}-CURRENT",)
    author_token = (f"{PRIVATE_SENTINEL}-{case_name}-AUTHOR",)

    def decode_fence(row: object) -> object:
        if row is current_token:
            return current
        assert row is author_token
        return author

    with monkeypatch.context() as scoped:
        scoped.setattr(
            readers,
            "development_effect_intent_row_value_from_row_tuple",
            lambda row: intent,
        )
        scoped.setattr(
            readers,
            "development_semantic_attempt_row_value_from_row_tuple",
            lambda row: semantic,
        )
        scoped.setattr(
            readers,
            "development_author_command_row_value_from_row_tuple",
            lambda row: command,
        )
        scoped.setattr(
            readers,
            "development_attempt_fence_row_value_from_row_tuple",
            lambda row: attempt,
        )
        scoped.setattr(
            readers,
            "development_effect_fence_row_value_from_row_tuple",
            decode_fence,
        )
        if no_wider_call_to_fail is not None:
            scoped.setattr(readers, "_ceilings_are_no_wider", controlled_no_wider)
        result, error, count = _scripted_probe(
            location,
            scoped,
            [
                [root_token],
                [semantic_token],
                [command_token],
                [attempt_token],
                [current_token],
                [author_token],
            ],
            lambda capability: readers._read_development_attempt_fence_command_effect_aggregate(
                capability,
                "program-1",
                "attempt-1",
                intent.effect_intent_ref,
            ),
        )
    assert count == 6
    assert result is None
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(
        error,
        "database_integrity_failure",
        prohibited=(
            semantic,
            intent,
            command,
            attempt,
            current,
            author,
            root_token,
            semantic_token,
            command_token,
            attempt_token,
            current_token,
            author_token,
        ),
        prohibited_text=(PRIVATE_SENTINEL,),
    )


@pytest.mark.parametrize(
    ("current_ref", "current_number"),
    (("revision-0000", 2), ("revision-other", 1)),
)
def test_both_one_sided_work_item_current_relations_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current_ref: str,
    current_number: int,
) -> None:
    location, rows = _seed_database(tmp_path)
    one_sided_head = _work_head_row(
        work_item_ref="work-0000",
        current_ref=current_ref,
        current_number=current_number,
    )
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [[one_sided_head], [rows["work_revision"]]],
        lambda capability: readers._read_development_work_item_head_and_revision_by_exact_ref(
            capability,
            "program-1",
            "work-0000",
            "revision-0000",
        ),
    )
    assert result is None and count == 2
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(error, "database_integrity_failure")


@pytest.mark.parametrize("membership_case", ("empty", "gap", "duplicate_pair", "duplicate_ordinal", "duplicate_work_ref"))
def test_membership_completion_counterfactuals_fail_without_partial_aggregate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    membership_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    first = rows["membership"]
    if membership_case == "empty":
        page: list[object] = []
    elif membership_case == "gap":
        page = [_membership_row(ordinal=1, work_item_ref="work-0000", work_item_revision_ref="revision-0000")]
    elif membership_case == "duplicate_pair":
        page = [first, first]
    elif membership_case == "duplicate_ordinal":
        page = [first, _membership_row(ordinal=0, work_item_ref="work-other", work_item_revision_ref="revision-other")]
    else:
        page = [first, _membership_row(ordinal=1, work_item_ref="work-0000", work_item_revision_ref="revision-other")]
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [[rows["program_version"]], page],
        lambda capability: readers._read_development_paged_program_version_membership(
            capability,
            "program-1",
            "version-1",
            10,
        ),
    )
    assert result is None and count == 2
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(error, "database_integrity_failure")


@pytest.mark.parametrize("continuation_case", ("overlap", "duplicate_work_ref"))
def test_membership_page_boundary_overlap_and_duplicate_work_ref_fail_before_child_sql(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    continuation_case: str,
) -> None:
    location, rows = _seed_database(tmp_path)
    first_page = [
        _membership_row(
            ordinal=index,
            work_item_ref=f"work-{index:04d}",
            work_item_revision_ref=f"revision-{index:04d}",
        )
        for index in range(257)
    ]
    if continuation_case == "overlap":
        continuation = [first_page[255]]
    else:
        duplicate_evidence = _membership_row(
            ordinal=256,
            work_item_ref="work-0000",
            work_item_revision_ref="revision-other",
        )
        first_page[256] = duplicate_evidence
        continuation = [duplicate_evidence]
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [[rows["program_version"]], first_page, continuation],
        lambda capability: readers._read_development_paged_program_version_membership(
            capability,
            "program-1",
            "version-1",
            300,
        ),
    )
    assert result is None and count == 3
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(error, "database_integrity_failure")


def test_missing_membership_child_returns_no_partial_aggregate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, rows = _seed_database(tmp_path)
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [[rows["program_version"]], [rows["membership"]], []],
        lambda capability: readers._read_development_paged_program_version_membership(
            capability,
            "program-1",
            "version-1",
            1,
        ),
    )
    assert result is None and count == 3
    assert type(error) is SQLiteMutationStoreError
    _assert_safe_error(error, "database_integrity_failure")


def test_role_seven_mid_traversal_expiry_leaks_no_partial_aggregate_or_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, _ = _seed_database(tmp_path)
    original_borrow = (
        transaction_module._SQLiteMutationReadCapability._borrow_connection_for_select
    )
    borrow_count = 0
    observed_errors: list[_MutationReadCapabilityError] = []

    def expire_on_child_borrow(capability: object) -> sqlite3.Connection:
        nonlocal borrow_count
        borrow_count += 1
        if borrow_count == 3:
            raise _MutationReadCapabilityError(
                _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED
            )
        return original_borrow(capability)

    def probe(capability: object) -> None:
        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            readers._read_development_paged_program_version_membership(
                capability,
                "program-1",
                "version-1",
                1,
            )
        observed_errors.append(exc_info.value)
        _assert_safe_capability_error(
            exc_info.value,
            _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED,
            prohibited=(capability,),
        )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            transaction_module._SQLiteMutationReadCapability,
            "_borrow_connection_for_select",
            expire_on_child_borrow,
        )
        _run_with_real_capability(location, scoped, probe)
    assert borrow_count == 3
    assert len(observed_errors) == 1


def test_delivery_does_not_infer_number_from_head_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location, rows = _seed_database(tmp_path)
    unusual_head = _row_with_digest(
        columns=effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
        identity={
            "schema_id": "governed-execution.nwp-development-delivery-head.v1",
            "effect_intent_ref": "effect-1",
            "program_ref": "program-1",
            "current_delivery_attempt_ref": "delivery-1",
            "head_revision": 99,
            "delivery_state": "planned",
            "updated_at": NOW,
        },
        digest_name="head_digest",
        domain="governed-execution.nwp-development-delivery-head.v1.identity",
    )
    result, error, count = _scripted_probe(
        location,
        monkeypatch,
        [[unusual_head], [rows["delivery_attempt"]]],
        lambda capability: readers._read_development_delivery_head(
            capability,
            "program-1",
            "effect-1",
        ),
    )
    assert error is None and count == 2
    assert result.delivery_head.head_revision == 99
    assert result.current_delivery_attempt.delivery_number == 1
