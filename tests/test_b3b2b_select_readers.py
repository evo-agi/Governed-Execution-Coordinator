from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
import dis
import json
from pathlib import Path
import sqlite3
import traceback
from types import CodeType
from typing import Any

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator import StateStore
from ge_nwp_coordinator.backlog import BACKLOG_SCHEMA_ID, FiniteBacklog, WorkItem
from ge_nwp_coordinator.canonicalization import canonical_json_bytes, canonical_sha256
from ge_nwp_coordinator.global_stop import GLOBAL_STOP_SCHEMA_ID
from ge_nwp_coordinator.lease import (
    AUTHORIZATION_DECISION_SCHEMA_ID,
    CANONICALIZATION_ID,
    LEASE_SCHEMA_ID,
    LeaseRevocationState,
    Permission,
    StandingLease,
    UnsupportedAuthorizationProvider,
)
from ge_nwp_coordinator.persistence_contracts import (
    AdmittedBacklogRecordEnvelope,
    AuthorizationReceiptEnvelope,
    DependencyReceiptEnvelope,
    GlobalStopCurrentRecordEnvelope,
    LeaseIdentityRecordEnvelope,
    WorkItemRecordEnvelope,
    encode_sqlite_boolean,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_read_scope import (
    _ADMITTED_BACKLOG_SELECT,
    _AUTHORIZATION_RECEIPT_SELECT,
    _CURRENT_WORK_ITEM_SELECT,
    _DEPENDENCY_RECEIPT_SELECT,
    _GLOBAL_STOP_CURRENT_SELECT,
    _LEASE_IDENTITY_SELECT,
    _SelectQuerySpec,
    _read_admitted_backlog,
    _read_authorization_receipt,
    _read_current_work_item,
    _read_dependency_receipt,
    _read_global_stop_current,
    _read_lease_identity_record,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
)
from ge_nwp_coordinator import sqlite_transition_read_scope as read_scope
from ge_nwp_coordinator.state_machine import (
    DEPENDENCY_DECISION_SCHEMA_ID,
    WORK_ITEM_STATE_SCHEMA_ID,
    DependencyDecision,
    WorkItemRecord,
    WorkItemState,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
READ_SCOPE_PATH = PACKAGE_DIR / "sqlite_transition_read_scope.py"
SELECT_SUPPORT_PATH = PACKAGE_DIR / "sqlite_transition_select_support.py"
CANONICAL_TIMESTAMP = "2026-07-14T00:00:03Z"
PRIVATE_SQLITE_SENTINEL = "PRIVATE-SQLITE-SENTINEL-DO-NOT-LEAK-314159"
PRIVATE_CAPABILITY_SENTINEL = "PRIVATE-CAPABILITY-SENTINEL-DO-NOT-LEAK-271828"


class _RecordingConnection(sqlite3.Connection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.execute_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.close_count = 0
        self.scripted_cursor: _ScriptedCursor | None = None
        self.scripted_execute_error: sqlite3.Error | None = None

    def execute(self, sql: str, parameters: Any = (), /) -> Any:
        parameter_tuple = tuple(parameters) if parameters is not None else ()
        self.execute_calls.append((sql, parameter_tuple))
        if self.scripted_execute_error is not None:
            raise self.scripted_execute_error
        if self.scripted_cursor is not None:
            return self.scripted_cursor
        return super().execute(sql, parameters)

    def close(self) -> None:
        self.close_count += 1
        super().close()


class _ScriptedCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        fetch_error: sqlite3.Error | None = None,
        close_error: sqlite3.Error | None = None,
    ) -> None:
        self._rows = rows
        self._fetch_error = fetch_error
        self._close_error = close_error
        self.fetchmany_sizes: list[int] = []
        self.close_count = 0

    def fetchmany(self, size: int) -> list[Any]:
        self.fetchmany_sizes.append(size)
        if self._fetch_error is not None:
            raise self._fetch_error
        return list(self._rows[:size])

    def close(self) -> None:
        self.close_count += 1
        if self._close_error is not None:
            raise self._close_error


class _CustomSequence:
    def __init__(self, values: tuple[Any, ...]) -> None:
        self._values = values

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Any:
        return iter(self._values)

    def __getitem__(self, index: int) -> Any:
        return self._values[index]


class _SyntheticSQLiteError(sqlite3.DatabaseError):
    def __init__(self, sqlite_errorcode: int | None) -> None:
        super().__init__(PRIVATE_SQLITE_SENTINEL)
        if sqlite_errorcode is not None:
            self.sqlite_errorcode = sqlite_errorcode


class _TestsOnlyTransitionReadCapabilityEpoch:
    """Tests-only structural capability epoch, not production authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._generation = 0
        self._active = False

    def start_for_test(self) -> "_TestsOnlyTransitionReadCapability":
        self._generation += 1
        self._active = True
        return _TestsOnlyTransitionReadCapability(self, self._generation)

    def end_for_test(self) -> None:
        self._active = False

    def _connection_for_generation(self, generation: int) -> sqlite3.Connection:
        if not self._active or generation != self._generation:
            raise _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        return self._connection


class _TestsOnlyTransitionReadCapability:
    """Clearly test-only structural stand-in for the future B3c capability."""

    def __init__(self, epoch: _TestsOnlyTransitionReadCapabilityEpoch, generation: int) -> None:
        self._epoch = epoch
        self._generation = generation
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        self.borrow_count += 1
        return self._epoch._connection_for_generation(self._generation)


class _WrongConnectionCapability:
    def _borrow_connection_for_select(self) -> object:
        return object()


class _UnknownExceptionCapability:
    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        try:
            raise ValueError(PRIVATE_CAPABILITY_SENTINEL)
        except ValueError as cause:
            error = RuntimeError(PRIVATE_CAPABILITY_SENTINEL)
            error.add_note(PRIVATE_CAPABILITY_SENTINEL)
            raise error from cause


@dataclass(frozen=True)
class _ReaderCase:
    reader_name: str
    spec: _SelectQuerySpec
    lookup_value: str | None
    row_factory: Callable[[], dict[str, object]]
    envelope_type: type[object]
    adapter_name: str


def _item(
    work_item_id: str = "wi-1",
    *,
    dependencies: tuple[str, ...] = (),
    api_calls: int = 1,
    compute_seconds: int = 10,
) -> WorkItem:
    return WorkItem(
        work_item_id=work_item_id,
        objective_label=f"{work_item_id} objective",
        opaque_private_assignment_ref=f"assignment-{work_item_id}",
        repo="coordinator-local",
        branches=("trunk_dev",),
        allowed_paths=("src", "tests"),
        task_class="code",
        risk_lane="low",
        required_validation_profile="unit-tests",
        budget_allocation={"api_calls": api_calls, "compute_seconds": compute_seconds},
        dependencies=dependencies,
        stop_conditions=("global-stop",),
    )


def _backlog(**overrides: object) -> FiniteBacklog:
    fields = {
        "schema_id": BACKLOG_SCHEMA_ID,
        "schema_version": 1,
        "backlog_id": "backlog-a2-p1",
        "lease_reference": "lease-a2-p1",
        "work_items": (_item(), _item("wi-2", dependencies=("wi-1",), api_calls=2, compute_seconds=20)),
        "content_digest": "0" * 64,
    }
    fields.update(overrides)
    return FiniteBacklog(**fields).with_digest()


def _lease(backlog: FiniteBacklog | None = None, **overrides: object) -> StandingLease:
    backlog = backlog or _backlog()
    fields = {
        "schema_id": LEASE_SCHEMA_ID,
        "schema_version": 1,
        "lease_id": "lease-a2-p1",
        "issuer_label": "operator-policy",
        "issued_at": "2026-07-14T00:00:00Z",
        "valid_from": "2026-07-14T00:00:01Z",
        "expires_at": "2026-07-15T00:00:00Z",
        "revocation_state": LeaseRevocationState.NOT_REVOKED,
        "revocation_reference": None,
        "subject": "nwp-coordinator-p1",
        "repo_identity": {"component": "nwp-coordinator", "repo_label": "coordinator-local"},
        "branch_policy": {"base": "trunk_dev", "mode": "operator-approved"},
        "allowed_paths": ("src", "tests"),
        "forbidden_path_policy_identity": "governed-execution.nwp-forbidden-paths.v1",
        "task_classes": ("docs", "code"),
        "risk_lanes": ("low",),
        "finite_backlog_reference": backlog.backlog_id,
        "finite_backlog_digest": backlog.content_digest,
        "max_work_items": 3,
        "max_concurrency": 1,
        "max_attempts": 2,
        "max_repairs": 1,
        "compute_api_budget": {"api_calls": 3, "compute_seconds": 30},
        "wall_clock_budget_seconds": 3600,
        "validation_requirements": ("unit-tests",),
        "audit_requirements": ("boundary-audit",),
        "local_commit_permission": Permission.FORBIDDEN,
        "publication_permission": Permission.FORBIDDEN,
        "cross_repo_permission": Permission.FORBIDDEN,
        "maintenance_permission": Permission.FORBIDDEN,
        "cleanup_requirements": ("no-worker-artifacts",),
        "reporting_cadence": "on-transition",
        "retention_policy": "safe-projections-only",
        "global_stop_reference": "operator-global-stop",
        "canonical_digest_metadata": {"algorithm": "sha256", "canonicalization": CANONICALIZATION_ID},
        "authorization_mechanism": {"kind": "unsupported", "descriptor": "p1-fail-closed"},
    }
    fields.update(overrides)
    return StandingLease(**fields).with_digest()


def _record(**overrides: object) -> WorkItemRecord:
    fields = {
        "schema_id": WORK_ITEM_STATE_SCHEMA_ID,
        "work_item_id": "wi-1",
        "lease_id": "lease-a2-p1",
        "backlog_id": "backlog-a2-p1",
        "state": WorkItemState.LEASE_ADMITTED,
        "version": 3,
        "attempt_count": 1,
        "repair_count": 0,
        "budget_consumed": 0,
        "budget_limit": 0,
        "max_attempts": 2,
        "max_repairs": 1,
        "cleanup_required": False,
    }
    fields.update(overrides)
    return WorkItemRecord(**fields)


def _lease_identity_row() -> dict[str, object]:
    lease = _lease()
    validation = lease.validate_identity()
    return {
        "decision_ref": validation.decision_ref,
        "lease_ref": validation.lease_ref,
        "identity_valid": encode_sqlite_boolean(validation.identity_valid, "lease_identity_record.identity_valid"),
        "lease_digest": validation.digest,
        "schema_id": LEASE_SCHEMA_ID,
        "canonical_json": canonical_json_bytes(lease.to_dict()).decode("utf-8"),
        "canonical_digest": canonical_sha256(lease.to_dict()),
        "created_at": CANONICAL_TIMESTAMP,
    }


def _authorization_row() -> dict[str, object]:
    decision = UnsupportedAuthorizationProvider().authorize(_lease())
    return {
        "decision_ref": decision.decision_ref,
        "lease_ref": decision.lease_ref,
        "lease_identity_decision_ref": decision.lease_identity_decision_ref,
        "lease_identity_valid": encode_sqlite_boolean(
            decision.lease_identity_valid,
            "authorization_receipt.lease_identity_valid",
        ),
        "authorization_model": decision.authorization_model.value,
        "authorized": encode_sqlite_boolean(decision.authorized, "authorization_receipt.authorized"),
        "executable": encode_sqlite_boolean(decision.executable, "authorization_receipt.executable"),
        "reason": decision.reason,
        "schema_id": AUTHORIZATION_DECISION_SCHEMA_ID,
        "canonical_json": decision.canonical_json(),
        "canonical_digest": decision.canonical_digest(),
        "created_at": CANONICAL_TIMESTAMP,
    }


def _dependency_row() -> dict[str, object]:
    decision = DependencyDecision(decision_ref="deps-ready", work_item_id="wi-1")
    return {
        "decision_ref": decision.decision_ref,
        "work_item_id": decision.work_item_id,
        "dependencies_satisfied": encode_sqlite_boolean(
            decision.dependencies_satisfied,
            "dependency_receipt.dependencies_satisfied",
        ),
        "reason": decision.reason,
        "schema_id": DEPENDENCY_DECISION_SCHEMA_ID,
        "canonical_json": decision.canonical_json(),
        "canonical_digest": decision.canonical_digest(),
        "created_at": CANONICAL_TIMESTAMP,
    }


def _work_item_row() -> dict[str, object]:
    record = _record()
    row = {**record.to_dict(), "updated_at": CANONICAL_TIMESTAMP}
    row["state"] = record.state.value
    row["cleanup_required"] = encode_sqlite_boolean(record.cleanup_required, "work_item_row.cleanup_required")
    return row


def _admitted_backlog_row() -> dict[str, object]:
    backlog = _backlog()
    return {
        "backlog_id": backlog.backlog_id,
        "lease_ref": backlog.lease_reference,
        "schema_id": backlog.schema_id,
        "schema_version": backlog.schema_version,
        "content_digest": backlog.content_digest,
        "canonical_json": canonical_json_bytes(backlog.to_dict()).decode("utf-8"),
        "admitted_at": CANONICAL_TIMESTAMP,
    }


def _global_stop_clear_row() -> dict[str, object]:
    return {
        "singleton_id": 1,
        "schema_id": GLOBAL_STOP_SCHEMA_ID,
        "version": 0,
        "active": 0,
        "stop_id": None,
        "reason_class": None,
        "issuer_ref": None,
        "issued_at": None,
        "operator_decision_ref": None,
        "updated_at": "1970-01-01T00:00:00Z",
    }


READER_CASES = (
    _ReaderCase(
        "_read_current_work_item",
        _CURRENT_WORK_ITEM_SELECT,
        "wi-1",
        _work_item_row,
        WorkItemRecordEnvelope,
        "work_item_record_envelope_from_row",
    ),
    _ReaderCase(
        "_read_lease_identity_record",
        _LEASE_IDENTITY_SELECT,
        "lease-identity-lease-a2-p1",
        _lease_identity_row,
        LeaseIdentityRecordEnvelope,
        "lease_identity_record_envelope_from_row",
    ),
    _ReaderCase(
        "_read_authorization_receipt",
        _AUTHORIZATION_RECEIPT_SELECT,
        "authz-lease-a2-p1",
        _authorization_row,
        AuthorizationReceiptEnvelope,
        "authorization_receipt_envelope_from_row",
    ),
    _ReaderCase(
        "_read_dependency_receipt",
        _DEPENDENCY_RECEIPT_SELECT,
        "deps-ready",
        _dependency_row,
        DependencyReceiptEnvelope,
        "dependency_receipt_envelope_from_row",
    ),
    _ReaderCase(
        "_read_admitted_backlog",
        _ADMITTED_BACKLOG_SELECT,
        "backlog-a2-p1",
        _admitted_backlog_row,
        AdmittedBacklogRecordEnvelope,
        "admitted_backlog_record_envelope_from_row",
    ),
    _ReaderCase(
        "_read_global_stop_current",
        _GLOBAL_STOP_CURRENT_SELECT,
        None,
        _global_stop_clear_row,
        GlobalStopCurrentRecordEnvelope,
        "global_stop_current_envelope_from_row",
    ),
)
OPTIONAL_READER_CASES = tuple(case for case in READER_CASES if case.lookup_value is not None)
TRANSITION_READ_SCOPE_ADAPTER_CASES = tuple(
    case for case in READER_CASES if case.reader_name != "_read_global_stop_current"
)
READER_NAMES = frozenset(case.reader_name for case in READER_CASES)
READER_FACADE_MODULE = "ge_nwp_coordinator.sqlite_transition_read_scope"
READER_FACADE_PATH = "src/ge_nwp_coordinator/sqlite_transition_read_scope.py"
CANONICAL_READER_PROVENANCE = {
    "_read_admitted_backlog": (
        READER_FACADE_MODULE,
        READER_FACADE_PATH,
    ),
    "_read_authorization_receipt": (
        READER_FACADE_MODULE,
        READER_FACADE_PATH,
    ),
    "_read_current_work_item": (
        READER_FACADE_MODULE,
        READER_FACADE_PATH,
    ),
    "_read_dependency_receipt": (
        READER_FACADE_MODULE,
        READER_FACADE_PATH,
    ),
    "_read_global_stop_current": (
        "ge_nwp_coordinator.sqlite_global_stop_readers",
        "src/ge_nwp_coordinator/sqlite_global_stop_readers.py",
    ),
    "_read_lease_identity_record": (
        READER_FACADE_MODULE,
        READER_FACADE_PATH,
    ),
}
APPROVED_READER_FACADE_REEXPORTS = {
    "_read_global_stop_current": "ge_nwp_coordinator.sqlite_global_stop_readers",
}
CANONICAL_READER_MODULES = frozenset(
    {READER_FACADE_MODULE}
    | {module_name for module_name, _ in CANONICAL_READER_PROVENANCE.values()}
)
EXPECTED_CANONICAL_READER_DEFINITIONS = tuple(
    sorted(
        (source_path, module_name, reader_name)
        for reader_name, (module_name, source_path) in CANONICAL_READER_PROVENANCE.items()
    )
)
EXPECTED_APPROVED_READER_REEXPORTS = (
    (
        READER_FACADE_PATH,
        0,
        "ge_nwp_coordinator.sqlite_global_stop_readers",
        "_read_global_stop_current",
        "_read_global_stop_current",
    ),
)
EXPECTED_PRODUCTION_READER_IMPORTS = (
    (
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        1,
        "sqlite_transition_read_scope",
        ("_read_global_stop_current",),
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        0,
        READER_FACADE_MODULE,
        (
            "_read_admitted_backlog",
            "_read_authorization_receipt",
            "_read_current_work_item",
            "_read_dependency_receipt",
            "_read_global_stop_current",
            "_read_lease_identity_record",
        ),
    ),
)
EXPECTED_PRODUCTION_READER_EDGES = (
    (
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        "_resolve_development_program_initialization_apply_after_fencing",
        "_read_global_stop_current",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_global_stop_resolution",
        "_read_global_stop_current",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_transition_resolution",
        "_read_admitted_backlog",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_transition_resolution",
        "_read_authorization_receipt",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_transition_resolution",
        "_read_current_work_item",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_transition_resolution",
        "_read_dependency_receipt",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_transition_resolution",
        "_read_global_stop_current",
        1,
    ),
    (
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "_CoordinatorMutationTransactionController._run_until_transition_resolution",
        "_read_lease_identity_record",
        1,
    ),
)

_INITIALIZER_CONSUMER_PATH = (
    "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py"
)
_INITIALIZER_OWNER_NAME = (
    "_resolve_development_program_initialization_apply_after_fencing"
)
_TRANSACTION_CONSUMER_PATH = (
    "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
)
_CONTROLLER_OWNER_NAME = "_CoordinatorMutationTransactionController"
_CONTROLLER_GLOBAL_STOP_OWNER_NAME = (
    "_CoordinatorMutationTransactionController._run_until_global_stop_resolution"
)
_CONTROLLER_TRANSITION_OWNER_NAME = (
    "_CoordinatorMutationTransactionController._run_until_transition_resolution"
)
_CONTROLLER_GLOBAL_STOP_METHOD_NAME = "_run_until_global_stop_resolution"
_CONTROLLER_TRANSITION_METHOD_NAME = "_run_until_transition_resolution"
_PRIVATE_READER_OWNER_NOT_LIVE = "PRIVATE_READER_OWNER_NOT_LIVE"

_EXPECTED_INITIALIZER_OWNER_HEADER_SHAPE = (
    (),
    (),
    "arguments(kwonlyargs=[arg(arg='capability', annotation=Name(id='object', "
    "ctx=Load())), arg(arg='command', annotation=Name(id='object', "
    "ctx=Load()))], kw_defaults=[None, None])",
    "BinOp(left=BinOp(left=Name(id='DevelopmentProgramInitializationResultV1', "
    "ctx=Load()), op=BitOr(), "
    "right=Name(id='DevelopmentProgramInitializationConflictV1', ctx=Load())), "
    "op=BitOr(), right=Name(id='_FreshDevelopmentProgramInitialization', "
    "ctx=Load()))",
    None,
)
_EXPECTED_CONTROLLER_OWNER_HEADER_SHAPE = ((), (), (), ())
_EXPECTED_CONTROLLER_GLOBAL_STOP_METHOD_HEADER_SHAPE = (
    (),
    (),
    "arguments(args=[arg(arg='self'), arg(arg='command', "
    "annotation=Name(id='GlobalStopCommand', ctx=Load())), "
    "arg(arg='typed_operator_decision', "
    "annotation=Name(id='GlobalStopOperatorDecision', ctx=Load()))])",
    "BinOp(left=BinOp(left=Name(id='CommittedGlobalStopUpdate', ctx=Load()), "
    "op=BitOr(), right=Name(id='GlobalStopConflict', ctx=Load())), op=BitOr(), "
    "right=Name(id='_FreshGlobalStopEvaluation', ctx=Load()))",
    None,
)
_EXPECTED_CONTROLLER_TRANSITION_METHOD_HEADER_SHAPE = (
    (),
    (),
    "arguments(args=[arg(arg='self'), arg(arg='command', "
    "annotation=Name(id='TransitionCommand', ctx=Load()))])",
    "BinOp(left=BinOp(left=Name(id='CommittedTransition', ctx=Load()), "
    "op=BitOr(), right=Name(id='TransitionConflict', ctx=Load())), op=BitOr(), "
    "right=Name(id='_FreshTransitionEvaluation', ctx=Load()))",
    None,
)

_PRIVATE_READER_LIVE_OWNER_EXCLUSIONS = (
    "dynamic imports",
    "exec, eval, or generated code",
    "runtime monkey-patching",
    "computed attribute access",
    "setattr or delattr",
    "reflective namespace mutation",
    "nested-function global mutation plus call-flow analysis",
    "aliases to the controller class followed by attribute mutation",
    "arbitrary interprocedural value flow",
)


def _function_owner_header_shape(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[tuple[str, ...], tuple[str, ...], str, str | None, str | None]:
    return (
        tuple(ast.dump(item, include_attributes=False) for item in node.decorator_list),
        tuple(
            ast.dump(item, include_attributes=False)
            for item in getattr(node, "type_params", ())
        ),
        ast.dump(node.args, include_attributes=False),
        None
        if node.returns is None
        else ast.dump(node.returns, include_attributes=False),
        node.type_comment,
    )


def _class_owner_header_shape(
    node: ast.ClassDef,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[tuple[str | None, str], ...],
    tuple[str, ...],
]:
    return (
        tuple(ast.dump(item, include_attributes=False) for item in node.decorator_list),
        tuple(ast.dump(item, include_attributes=False) for item in node.bases),
        tuple(
            (item.arg, ast.dump(item.value, include_attributes=False))
            for item in node.keywords
        ),
        tuple(
            ast.dump(item, include_attributes=False)
            for item in getattr(node, "type_params", ())
        ),
    )


def _require_direct_definition(
    statements: list[ast.stmt],
    *,
    name: str,
    expected_type: type[ast.FunctionDef] | type[ast.ClassDef],
) -> ast.FunctionDef | ast.ClassDef:
    candidates = tuple(
        node
        for node in statements
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == name
    )
    if len(candidates) != 1 or type(candidates[0]) is not expected_type:
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)
    return candidates[0]  # type: ignore[return-value]


def _namespace_binding_operations(
    code: CodeType,
    name: str,
) -> tuple[str, ...]:
    namespace_operations = frozenset(
        {"STORE_NAME", "DELETE_NAME", "STORE_GLOBAL", "DELETE_GLOBAL"}
    )
    return tuple(
        instruction.opname
        for instruction in dis.get_instructions(code)
        if instruction.argval == name
        and instruction.opname in namespace_operations
    )


def _require_single_namespace_definition_binding(
    code: CodeType,
    name: str,
) -> None:
    if _namespace_binding_operations(code, name) != ("STORE_NAME",):
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)


def _require_selected_code_object(
    parent_code: CodeType,
    selected_node: ast.FunctionDef | ast.ClassDef,
) -> CodeType:
    matches = tuple(
        item
        for item in parent_code.co_consts
        if type(item) is CodeType
        and item.co_name == selected_node.name
        and item.co_firstlineno == selected_node.lineno
    )
    if len(matches) != 1:
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)
    return matches[0]


def _has_deferred_callable_ancestor(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    parent = parents.get(node)
    while parent is not None:
        if type(parent) in (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda):
            return True
        parent = parents.get(parent)
    return False


def _is_module_initialization_protected_method_target(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    return bool(
        type(node) is ast.Attribute
        and type(node.ctx) in (ast.Store, ast.Del)
        and type(node.value) is ast.Name
        and node.value.id == _CONTROLLER_OWNER_NAME
        and node.attr
        in {
            _CONTROLLER_GLOBAL_STOP_METHOD_NAME,
            _CONTROLLER_TRANSITION_METHOD_NAME,
        }
        and not _has_deferred_callable_ancestor(node, parents)
    )


def _reject_direct_protected_method_overwrite(
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> None:
    for node in ast.walk(tree):
        if _is_module_initialization_protected_method_target(node, parents):
            raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)


def _require_exact_live_authorized_reader_owners(
    *,
    relative_path: str,
    source: str,
    tree: ast.Module,
    parents: dict[ast.AST, ast.AST],
) -> dict[str, ast.AST]:
    if relative_path not in {
        _INITIALIZER_CONSUMER_PATH,
        _TRANSACTION_CONSUMER_PATH,
    }:
        return {}
    try:
        module_code = compile(source, relative_path, "exec")
    except (SyntaxError, TypeError, ValueError):
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE) from None
    if type(module_code) is not CodeType:
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)

    if relative_path == _INITIALIZER_CONSUMER_PATH:
        selected_owner = _require_direct_definition(
            tree.body,
            name=_INITIALIZER_OWNER_NAME,
            expected_type=ast.FunctionDef,
        )
        if (
            type(selected_owner) is not ast.FunctionDef
            or _function_owner_header_shape(selected_owner)
            != _EXPECTED_INITIALIZER_OWNER_HEADER_SHAPE
        ):
            raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)
        _require_selected_code_object(module_code, selected_owner)
        _require_single_namespace_definition_binding(
            module_code,
            _INITIALIZER_OWNER_NAME,
        )
        return {_INITIALIZER_OWNER_NAME: selected_owner}

    selected_controller = _require_direct_definition(
        tree.body,
        name=_CONTROLLER_OWNER_NAME,
        expected_type=ast.ClassDef,
    )
    if (
        type(selected_controller) is not ast.ClassDef
        or _class_owner_header_shape(selected_controller)
        != _EXPECTED_CONTROLLER_OWNER_HEADER_SHAPE
    ):
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)
    selected_global_stop_method = _require_direct_definition(
        selected_controller.body,
        name=_CONTROLLER_GLOBAL_STOP_METHOD_NAME,
        expected_type=ast.FunctionDef,
    )
    selected_transition_method = _require_direct_definition(
        selected_controller.body,
        name=_CONTROLLER_TRANSITION_METHOD_NAME,
        expected_type=ast.FunctionDef,
    )
    if (
        type(selected_global_stop_method) is not ast.FunctionDef
        or _function_owner_header_shape(selected_global_stop_method)
        != _EXPECTED_CONTROLLER_GLOBAL_STOP_METHOD_HEADER_SHAPE
        or type(selected_transition_method) is not ast.FunctionDef
        or _function_owner_header_shape(selected_transition_method)
        != _EXPECTED_CONTROLLER_TRANSITION_METHOD_HEADER_SHAPE
    ):
        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)

    _require_single_namespace_definition_binding(module_code, _CONTROLLER_OWNER_NAME)
    controller_code = _require_selected_code_object(
        module_code,
        selected_controller,
    )
    _require_selected_code_object(controller_code, selected_global_stop_method)
    _require_selected_code_object(controller_code, selected_transition_method)
    _require_single_namespace_definition_binding(
        controller_code,
        _CONTROLLER_GLOBAL_STOP_METHOD_NAME,
    )
    _require_single_namespace_definition_binding(
        controller_code,
        _CONTROLLER_TRANSITION_METHOD_NAME,
    )
    _reject_direct_protected_method_overwrite(tree, parents)
    return {
        _CONTROLLER_GLOBAL_STOP_OWNER_NAME: selected_global_stop_method,
        _CONTROLLER_TRANSITION_OWNER_NAME: selected_transition_method,
    }


def _scan_private_reader_bindings(
    sources: dict[str, str],
) -> tuple[
    tuple[tuple[str, int, str | None, tuple[str, ...]], ...],
    tuple[tuple[str, str, str], ...],
    tuple[tuple[str, int, str, str, str], ...],
    tuple[tuple[str, str, str, int], ...],
]:
    observed_imports: list[tuple[str, int, str | None, tuple[str, ...]]] = []
    observed_definitions: list[tuple[str, str, str]] = []
    observed_reexports: list[tuple[str, int, str, str, str]] = []
    observed_edges: Counter[tuple[str, str, str]] = Counter()
    approved_consumer_imports = {
        relative_path: (level, module_name, imported_names)
        for relative_path, level, module_name, imported_names in (
            EXPECTED_PRODUCTION_READER_IMPORTS
        )
    }
    authorized_owners_by_path: dict[str, set[str]] = {}
    for relative_path, owner_name, _reader_name, _count in (
        EXPECTED_PRODUCTION_READER_EDGES
    ):
        authorized_owners_by_path.setdefault(relative_path, set()).add(owner_name)
    type_parameter_node_types = tuple(
        node_type
        for node_type in (
            getattr(ast, "TypeVar", None),
            getattr(ast, "ParamSpec", None),
            getattr(ast, "TypeVarTuple", None),
        )
        if node_type is not None
    )

    def source_module_identity(relative_path: str) -> tuple[str, str]:
        path = Path(relative_path)
        parts = path.parts
        if (
            len(parts) < 3
            or parts[:2] != ("src", "ge_nwp_coordinator")
            or path.suffix != ".py"
        ):
            raise AssertionError("PRIVATE_READER_SOURCE_PATH_UNRESOLVED")
        module_parts = list(path.with_suffix("").parts[1:])
        is_package = module_parts[-1] == "__init__"
        if is_package:
            module_parts.pop()
        module_name = ".".join(module_parts)
        package_name = module_name if is_package else module_name.rpartition(".")[0]
        if not module_name or not package_name:
            raise AssertionError("PRIVATE_READER_SOURCE_PATH_UNRESOLVED")
        return module_name, package_name

    def resolve_import_from_module(
        node: ast.ImportFrom,
        *,
        source_package: str,
    ) -> str:
        if node.level == 0:
            return node.module or ""
        package_parts = source_package.split(".")
        parents_to_remove = node.level - 1
        if parents_to_remove >= len(package_parts):
            raise AssertionError("PRIVATE_READER_RELATIVE_IMPORT_UNRESOLVED")
        resolved_parts = package_parts[: len(package_parts) - parents_to_remove]
        if node.module:
            resolved_parts.extend(node.module.split("."))
        return ".".join(resolved_parts)

    for relative_path, source in sorted(sources.items()):
        source_module, source_package = source_module_identity(relative_path)
        tree = ast.parse(source, filename=relative_path)
        direct_module_statement_nodes = {id(node) for node in tree.body}
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        function_bindings: dict[str, str] = {}
        module_bindings: dict[str, str] = {}
        canonical_binding_nodes: set[int] = set()
        canonical_definition_nodes: set[int] = set()
        wildcard_imports: list[tuple[ast.ImportFrom, str]] = []

        def register_function_binding(
            binding_name: str,
            reader_name: str,
            binding_node: ast.AST,
        ) -> None:
            if binding_name in function_bindings or binding_name in module_bindings:
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            function_bindings[binding_name] = reader_name
            canonical_binding_nodes.add(id(binding_node))

        def register_module_binding(
            binding_name: str,
            module_name: str,
            binding_node: ast.alias,
        ) -> None:
            if binding_name in function_bindings or binding_name in module_bindings:
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            module_bindings[binding_name] = module_name
            canonical_binding_nodes.add(id(binding_node))

        def require_approved_module_scope(node: ast.AST) -> None:
            if id(node) not in direct_module_statement_nodes:
                raise AssertionError(
                    "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE"
                )

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            provenance = CANONICAL_READER_PROVENANCE.get(node.name)
            if provenance != (source_module, relative_path):
                continue
            observed_definitions.append((relative_path, source_module, node.name))
            canonical_definition_nodes.add(id(node))
            register_function_binding(node.name, node.name, node)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                resolved_module = resolve_import_from_module(
                    node,
                    source_package=source_package,
                )
                if any(alias.name == "*" for alias in node.names):
                    if resolved_module in CANONICAL_READER_MODULES:
                        raise AssertionError("PRIVATE_READER_WILDCARD_IMPORT")
                    wildcard_imports.append((node, resolved_module))
                    continue

                reader_aliases = tuple(
                    alias for alias in node.names if alias.name in READER_NAMES
                )
                if reader_aliases:
                    require_approved_module_scope(node)
                    is_exact_reexport = (
                        source_module == READER_FACADE_MODULE
                        and relative_path == READER_FACADE_PATH
                        and len(node.names) == 1
                        and reader_aliases[0].name == "_read_global_stop_current"
                        and reader_aliases[0].asname is None
                        and resolved_module
                        == APPROVED_READER_FACADE_REEXPORTS[
                            "_read_global_stop_current"
                        ]
                    )
                    if is_exact_reexport:
                        alias = reader_aliases[0]
                        observed_reexports.append(
                            (
                                relative_path,
                                node.level,
                                node.module or "",
                                alias.name,
                                alias.name,
                            )
                        )
                        register_function_binding(alias.name, alias.name, alias)
                        continue
                    if resolved_module != READER_FACADE_MODULE:
                        raise AssertionError(
                            "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE"
                        )
                    approved = approved_consumer_imports.get(relative_path)
                    imported_names = tuple(sorted(alias.name for alias in node.names))
                    if approved is None or (
                        node.level,
                        node.module,
                        imported_names,
                    ) != approved:
                        raise AssertionError(
                            "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE"
                        )
                    for alias in node.names:
                        register_function_binding(
                            alias.asname or alias.name,
                            alias.name,
                            alias,
                        )
                    observed_imports.append(
                        (
                            relative_path,
                            node.level,
                            node.module,
                            imported_names,
                        )
                    )
                    continue

                canonical_module_aliases: list[tuple[ast.alias, str]] = []
                for alias in node.names:
                    imported_module = ".".join(
                        part for part in (resolved_module, alias.name) if part
                    )
                    if imported_module in CANONICAL_READER_MODULES:
                        canonical_module_aliases.append((alias, imported_module))
                if canonical_module_aliases:
                    require_approved_module_scope(node)
                    if any(
                        module_name != READER_FACADE_MODULE
                        for _alias, module_name in canonical_module_aliases
                    ):
                        raise AssertionError(
                            "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE"
                        )
                    if (
                        relative_path not in approved_consumer_imports
                        or len(node.names) != 1
                        or len(canonical_module_aliases) != 1
                    ):
                        raise AssertionError(
                            "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE"
                        )
                    alias, imported_module = canonical_module_aliases[0]
                    binding_name = alias.asname or alias.name
                    register_module_binding(binding_name, imported_module, alias)
                    observed_imports.append(
                        (
                            relative_path,
                            node.level,
                            node.module,
                            (alias.name,),
                        )
                    )
                    continue

            if isinstance(node, ast.Import):
                canonical_aliases = tuple(
                    alias
                    for alias in node.names
                    if alias.name in CANONICAL_READER_MODULES
                )
                if not canonical_aliases:
                    continue
                require_approved_module_scope(node)
                if any(
                    alias.name != READER_FACADE_MODULE
                    for alias in canonical_aliases
                ):
                    raise AssertionError(
                        "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE"
                    )
                if (
                    relative_path not in approved_consumer_imports
                    or len(node.names) != 1
                    or len(canonical_aliases) != 1
                ):
                    raise AssertionError(
                        "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE"
                    )
                alias = canonical_aliases[0]
                if alias.asname is None:
                    raise AssertionError("PRIVATE_READER_MODULE_ALIAS_REQUIRED")
                register_module_binding(alias.asname, alias.name, alias)
                observed_imports.append((relative_path, 0, alias.name, ()))

        definition_nodes: dict[str, list[ast.AST]] = {}

        class _OwnerDefinitionCollector(ast.NodeVisitor):
            def __init__(self) -> None:
                self._owners = ["<module>"]

            def _qualified_owner(self, name: str) -> str:
                current = self._owners[-1]
                return name if current == "<module>" else f"{current}.{name}"

            def _visit_definition(
                self,
                node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
            ) -> None:
                qualified = self._qualified_owner(node.name)
                definition_nodes.setdefault(qualified, []).append(node)
                self._owners.append(qualified)
                try:
                    for statement in node.body:
                        self.visit(statement)
                finally:
                    self._owners.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._visit_definition(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._visit_definition(node)

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self._visit_definition(node)

        _OwnerDefinitionCollector().visit(tree)
        for owner_name in sorted(authorized_owners_by_path.get(relative_path, ())):
            owner_nodes = definition_nodes.get(owner_name, ())
            if len(owner_nodes) != 1 or not isinstance(
                owner_nodes[0],
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                raise AssertionError("PRIVATE_READER_OWNER_COLLISION")
            owner_parts = owner_name.split(".")
            for part_count in range(1, len(owner_parts)):
                container_name = ".".join(owner_parts[:part_count])
                container_nodes = definition_nodes.get(container_name, ())
                if len(container_nodes) != 1 or not isinstance(
                    container_nodes[0], ast.ClassDef
                ):
                    raise AssertionError("PRIVATE_READER_OWNER_COLLISION")

        protected_bindings = set(function_bindings) | set(module_bindings)
        for _node, resolved_module in wildcard_imports:
            if resolved_module in CANONICAL_READER_MODULES:
                raise AssertionError("PRIVATE_READER_WILDCARD_IMPORT")
            if protected_bindings:
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")

        for node in ast.walk(tree):
            if isinstance(node, ast.alias):
                if id(node) in canonical_binding_nodes:
                    continue
                parent = parents.get(node)
                if isinstance(parent, ast.Import):
                    binding_name = node.asname or node.name.partition(".")[0]
                else:
                    binding_name = node.asname or node.name
                if binding_name in protected_bindings:
                    raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and node.id in protected_bindings
            ):
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if isinstance(node, ast.arg) and node.arg in protected_bindings:
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name in protected_bindings
                and id(node) not in canonical_definition_nodes
            ):
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if (
                isinstance(node, ast.ExceptHandler)
                and node.name in protected_bindings
            ):
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if isinstance(node, (ast.MatchAs, ast.MatchStar)) and (
                node.name in protected_bindings
            ):
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if isinstance(node, ast.MatchMapping) and (
                node.rest in protected_bindings
            ):
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")
            if type_parameter_node_types and isinstance(
                node, type_parameter_node_types
            ) and node.name in protected_bindings:
                raise AssertionError("PRIVATE_READER_BINDING_REBOUND")

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                parent = parents.get(node)
                if node.id in function_bindings and not (
                    isinstance(parent, ast.Call) and parent.func is node
                ):
                    raise AssertionError("PRIVATE_READER_INDIRECT_USE")
                if node.id in module_bindings:
                    reader_attribute = parent
                    call = parents.get(reader_attribute)
                    if not (
                        isinstance(reader_attribute, ast.Attribute)
                        and reader_attribute.value is node
                        and reader_attribute.attr in READER_NAMES
                        and isinstance(call, ast.Call)
                        and call.func is reader_attribute
                    ):
                        raise AssertionError("PRIVATE_READER_INDIRECT_USE")
                    if module_bindings[node.id] != READER_FACADE_MODULE:
                        raise AssertionError(
                            "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE"
                        )
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in module_bindings
            ):
                parent = parents.get(node)
                if not (
                    node.attr in READER_NAMES
                    and isinstance(parent, ast.Call)
                    and parent.func is node
                ):
                    raise AssertionError("PRIVATE_READER_INDIRECT_USE")
                if module_bindings[node.value.id] != READER_FACADE_MODULE:
                    raise AssertionError(
                        "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE"
                    )

        selected_authorized_owner_nodes = (
            _require_exact_live_authorized_reader_owners(
                relative_path=relative_path,
                source=source,
                tree=tree,
                parents=parents,
            )
        )

        class _ReaderEdgeVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self._owners = ["<module>"]
                self._owner_nodes: list[ast.AST] = [tree]

            def _qualified_owner(self, name: str) -> str:
                current = self._owners[-1]
                return name if current == "<module>" else f"{current}.{name}"

            def _visit_argument_annotations(self, arguments: ast.arguments) -> None:
                positional = (*arguments.posonlyargs, *arguments.args)
                for argument in (*positional, *arguments.kwonlyargs):
                    if argument.annotation is not None:
                        self.visit(argument.annotation)
                if arguments.vararg is not None and arguments.vararg.annotation is not None:
                    self.visit(arguments.vararg.annotation)
                if arguments.kwarg is not None and arguments.kwarg.annotation is not None:
                    self.visit(arguments.kwarg.annotation)

            def _visit_function_header(
                self,
                node: ast.FunctionDef | ast.AsyncFunctionDef,
            ) -> None:
                for decorator in node.decorator_list:
                    self.visit(decorator)
                for default in node.args.defaults:
                    self.visit(default)
                for default in node.args.kw_defaults:
                    if default is not None:
                        self.visit(default)
                self._visit_argument_annotations(node.args)
                if node.returns is not None:
                    self.visit(node.returns)
                for type_parameter in getattr(node, "type_params", ()):
                    self.visit(type_parameter)

            def _visit_function_body(
                self,
                node: ast.FunctionDef | ast.AsyncFunctionDef,
            ) -> None:
                self._visit_function_header(node)
                self._owners.append(self._qualified_owner(node.name))
                self._owner_nodes.append(node)
                try:
                    for statement in node.body:
                        self.visit(statement)
                finally:
                    self._owner_nodes.pop()
                    self._owners.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._visit_function_body(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._visit_function_body(node)

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                for decorator in node.decorator_list:
                    self.visit(decorator)
                for base in node.bases:
                    self.visit(base)
                for keyword in node.keywords:
                    self.visit(keyword.value)
                for type_parameter in getattr(node, "type_params", ()):
                    self.visit(type_parameter)
                self._owners.append(self._qualified_owner(node.name))
                self._owner_nodes.append(node)
                try:
                    for statement in node.body:
                        self.visit(statement)
                finally:
                    self._owner_nodes.pop()
                    self._owners.pop()

            def visit_Lambda(self, node: ast.Lambda) -> None:
                for default in node.args.defaults:
                    self.visit(default)
                for default in node.args.kw_defaults:
                    if default is not None:
                        self.visit(default)
                self._visit_argument_annotations(node.args)
                lambda_name = f"<lambda@{node.lineno}:{node.col_offset}>"
                self._owners.append(self._qualified_owner(lambda_name))
                self._owner_nodes.append(node)
                try:
                    self.visit(node.body)
                finally:
                    self._owner_nodes.pop()
                    self._owners.pop()

            def visit_Call(self, node: ast.Call) -> None:
                if isinstance(node.func, ast.Name):
                    reader_name = function_bindings.get(node.func.id)
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and module_bindings.get(node.func.value.id)
                    == READER_FACADE_MODULE
                    and node.func.attr in READER_NAMES
                ):
                    reader_name = node.func.attr
                else:
                    reader_name = None
                if reader_name is not None:
                    owner_name = self._owners[-1]
                    if owner_name in authorized_owners_by_path.get(
                        relative_path, ()
                    ) and (
                        selected_authorized_owner_nodes.get(owner_name)
                        is not self._owner_nodes[-1]
                    ):
                        raise AssertionError(_PRIVATE_READER_OWNER_NOT_LIVE)
                    observed_edges[
                        (relative_path, owner_name, reader_name)
                    ] += 1
                self.generic_visit(node)

        _ReaderEdgeVisitor().visit(tree)

    return (
        tuple(sorted(observed_imports)),
        tuple(sorted(observed_definitions)),
        tuple(sorted(observed_reexports)),
        tuple(sorted((*edge, count) for edge, count in observed_edges.items())),
    )


def _connect() -> _RecordingConnection:
    return sqlite3.connect(":memory:", factory=_RecordingConnection)


def _scripted_connection(
    *,
    rows: tuple[Any, ...] = (),
    execute_error: sqlite3.Error | None = None,
    fetch_error: sqlite3.Error | None = None,
    close_error: sqlite3.Error | None = None,
) -> tuple[_RecordingConnection, _ScriptedCursor | None]:
    connection = _connect()
    if execute_error is not None:
        connection.scripted_execute_error = execute_error
        return connection, None
    cursor = _ScriptedCursor(rows, fetch_error=fetch_error, close_error=close_error)
    connection.scripted_cursor = cursor
    return connection, cursor


def _capability_for(connection: sqlite3.Connection) -> tuple[_TestsOnlyTransitionReadCapabilityEpoch, _TestsOnlyTransitionReadCapability]:
    epoch = _TestsOnlyTransitionReadCapabilityEpoch(connection)
    return epoch, epoch.start_for_test()


def _create_table(connection: sqlite3.Connection, spec: _SelectQuerySpec) -> None:
    columns_sql = ", ".join(spec.columns)
    connection.execute(f"CREATE TABLE {spec.table_name} ({columns_sql})")


def _insert_row(connection: sqlite3.Connection, spec: _SelectQuerySpec, row: dict[str, object]) -> None:
    placeholders = ", ".join("?" for _ in spec.columns)
    columns_sql = ", ".join(spec.columns)
    values = tuple(row[column] for column in spec.columns)
    connection.execute(f"INSERT INTO {spec.table_name} ({columns_sql}) VALUES ({placeholders})", values)


def _prepare_table_with_rows(case: _ReaderCase, count: int) -> _RecordingConnection:
    connection = _connect()
    _create_table(connection, case.spec)
    row = case.row_factory()
    for _ in range(count):
        _insert_row(connection, case.spec, row)
    connection.execute_calls.clear()
    return connection


def _invoke(case: _ReaderCase, capability: object, lookup_override: str | None = None) -> object:
    reader = getattr(read_scope, case.reader_name)
    if case.lookup_value is None:
        return reader(capability)
    lookup_value = case.lookup_value if lookup_override is None else lookup_override
    return reader(capability, lookup_value)


def _tuple_for(case: _ReaderCase, row: dict[str, object] | None = None) -> tuple[object, ...]:
    row = row or case.row_factory()
    return tuple(row[column] for column in case.spec.columns)


def _assert_safe_mutation_error(exc: SQLiteMutationStoreError, error_class: str) -> None:
    assert exc.error_class == error_class
    assert str(exc) == error_class
    assert exc.args == (error_class,)
    assert exc.internal_detail is None
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert exc.error_class != "commit_outcome_unknown"
    rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert PRIVATE_SQLITE_SENTINEL not in rendered
    for forbidden in (PRIVATE_SQLITE_SENTINEL, ":memory:", "Connection", "SELECT "):
        assert forbidden not in rendered
        assert forbidden not in repr(exc)
        assert forbidden not in repr(exc.args)


def _assert_raises_sqlite_mutation_error(call: Callable[[], object], error_class: str) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        call()
    _assert_safe_mutation_error(exc_info.value, error_class)
    return exc_info.value


def _render_exception_graph(exc: BaseException) -> str:
    rendered: list[str] = []
    pending = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        rendered.extend(
            (
                type(current).__name__,
                str(current),
                repr(current),
                repr(current.args),
                repr(getattr(current, "__notes__", None)),
                "".join(traceback.format_exception(type(current), current, current.__traceback__)),
            )
        )
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return "\n".join(rendered)


def _sqlite_error_code(name: str, fallback: int) -> int:
    code = getattr(sqlite3, name, fallback)
    assert type(code) is int
    return code


def _sqlite_row_object() -> sqlite3.Row:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("CREATE TABLE row_shape_probe (value)")
        connection.execute("INSERT INTO row_shape_probe (value) VALUES (1)")
        row = connection.execute("SELECT value FROM row_shape_probe").fetchone()
        assert isinstance(row, sqlite3.Row)
        return row
    finally:
        connection.close()


@pytest.mark.parametrize("case", OPTIONAL_READER_CASES, ids=[case.reader_name for case in OPTIONAL_READER_CASES])
def test_lookup_ref_validation_runs_before_capability_borrow_or_sql(case: _ReaderCase) -> None:
    connection = _connect()
    _, capability = _capability_for(connection)
    try:
        with pytest.raises(ValueError) as exc_info:
            _invoke(case, capability, lookup_override="malformed ref")

        assert capability.borrow_count == 0
        assert connection.execute_calls == []
        assert not isinstance(exc_info.value, SQLiteMutationStoreError)
        rendered = f"{exc_info.value!r} {exc_info.value.args!r} {exc_info.value}"
        assert "malformed ref" not in rendered
    finally:
        connection.close()


@pytest.mark.parametrize("case", OPTIONAL_READER_CASES, ids=[case.reader_name for case in OPTIONAL_READER_CASES])
def test_valid_lookup_uses_one_bound_parameter_and_no_interpolation(case: _ReaderCase) -> None:
    connection = _prepare_table_with_rows(case, 0)
    _, capability = _capability_for(connection)
    try:
        assert _invoke(case, capability) is None

        assert capability.borrow_count == 1
        assert connection.execute_calls == [(case.spec.sql, (case.lookup_value,))]
        assert case.lookup_value not in case.spec.sql
        assert case.spec.sql.count("?") == 1
    finally:
        connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_reader_cardinality_zero_one_two_and_more_than_two(case: _ReaderCase) -> None:
    zero_connection = _prepare_table_with_rows(case, 0)
    _, zero_capability = _capability_for(zero_connection)
    try:
        if case.lookup_value is None:
            _assert_raises_sqlite_mutation_error(lambda: _invoke(case, zero_capability), "database_integrity_failure")
        else:
            assert _invoke(case, zero_capability) is None
    finally:
        zero_connection.close()

    one_connection = _prepare_table_with_rows(case, 1)
    _, one_capability = _capability_for(one_connection)
    try:
        envelope = _invoke(case, one_capability)
        assert isinstance(envelope, case.envelope_type)
        assert one_connection.execute_calls == [
            (case.spec.sql, (1,) if case.lookup_value is None else (case.lookup_value,))
        ]
    finally:
        one_connection.close()

    for count in (2, 3):
        duplicate_connection = _prepare_table_with_rows(case, count)
        _, duplicate_capability = _capability_for(duplicate_connection)
        try:
            _assert_raises_sqlite_mutation_error(
                lambda: _invoke(case, duplicate_capability),
                "database_integrity_failure",
            )
        finally:
            duplicate_connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_fetchmany_is_bounded_to_two_for_each_reader(case: _ReaderCase) -> None:
    row = _tuple_for(case)
    connection, cursor = _scripted_connection(rows=(row, row, row))
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _invoke(case, capability), "database_integrity_failure")
        assert cursor.fetchmany_sizes == [2]
        assert cursor.close_count == 1
    finally:
        connection.close()


@pytest.mark.parametrize(
    "case",
    TRANSITION_READ_SCOPE_ADAPTER_CASES,
    ids=[case.reader_name for case in TRANSITION_READ_SCOPE_ADAPTER_CASES],
)
def test_column_order_mapping_uses_exact_bound_adapter_and_no_raw_tuple(case: _ReaderCase, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_tuple = tuple(f"value-{index}" for index, _ in enumerate(case.spec.columns))
    connection, _ = _scripted_connection(rows=(raw_tuple,))
    _, capability = _capability_for(connection)
    marker = object()
    captured: dict[str, object] = {}

    def adapter(payload: object) -> object:
        captured["payload"] = payload
        return marker

    monkeypatch.setattr(read_scope, case.adapter_name, adapter)
    try:
        assert _invoke(case, capability) is marker
        payload = captured["payload"]
        assert type(payload) is dict
        assert payload is not raw_tuple
        assert tuple(payload.keys()) == case.spec.columns  # type: ignore[union-attr]
        assert tuple(payload.values()) == raw_tuple  # type: ignore[union-attr]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "case",
    TRANSITION_READ_SCOPE_ADAPTER_CASES,
    ids=[case.reader_name for case in TRANSITION_READ_SCOPE_ADAPTER_CASES],
)
def test_non_exact_tuple_rows_are_rejected_before_adapter(case: _ReaderCase, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_adapter(payload: object) -> object:
        raise AssertionError(f"adapter should not receive {payload!r}")

    monkeypatch.setattr(read_scope, case.adapter_name, forbidden_adapter)
    row = _tuple_for(case)
    malformed_rows = (
        row[:-1],
        list(row),
        {column: value for column, value in zip(case.spec.columns, row, strict=True)},
        _CustomSequence(row),
        _sqlite_row_object(),
    )
    for malformed_row in malformed_rows:
        connection, _ = _scripted_connection(rows=(malformed_row,))
        _, capability = _capability_for(connection)
        try:
            _assert_raises_sqlite_mutation_error(lambda: _invoke(case, capability), "database_integrity_failure")
        finally:
            connection.close()


def test_global_stop_reader_binds_singleton_one_internally_and_exposes_no_argument() -> None:
    signature = __import__("inspect").signature(_read_global_stop_current)
    assert list(signature.parameters) == ["capability"]

    connection = _prepare_table_with_rows(READER_CASES[-1], 1)
    _, capability = _capability_for(connection)
    try:
        envelope = _read_global_stop_current(capability)
        assert isinstance(envelope, GlobalStopCurrentRecordEnvelope)
        assert connection.execute_calls == [(_GLOBAL_STOP_CURRENT_SELECT.sql, (1,))]
    finally:
        connection.close()


def test_capability_errors_are_preserved_and_wrong_return_type_is_safe() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    epoch, capability = _capability_for(connection)
    epoch.end_for_test()
    try:
        with pytest.raises(_MutationReadCapabilityError) as expired:
            _read_current_work_item(capability, "wi-1")
        assert expired.value.reason is _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED
        assert expired.value.__cause__ is None
        assert expired.value.__context__ is None

        with pytest.raises(_MutationReadCapabilityError) as wrong_type:
            _read_current_work_item(_WrongConnectionCapability(), "wi-1")
        assert wrong_type.value.reason is _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
        assert str(wrong_type.value) == "mutation_read_capability_unavailable"
    finally:
        connection.close()


def test_unknown_capability_exception_is_sanitized_outside_raw_exception_context() -> None:
    capability = _UnknownExceptionCapability()

    with pytest.raises(_MutationReadCapabilityError) as exc_info:
        _read_current_work_item(capability, "wi-1")

    exc = exc_info.value
    assert exc.reason is _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
    assert str(exc) == "mutation_read_capability_unavailable"
    assert exc.args == ("mutation_read_capability_unavailable",)
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert getattr(exc, "__notes__", None) is None

    rendered = _render_exception_graph(exc)
    for forbidden in (
        PRIVATE_CAPABILITY_SENTINEL,
        "_UnknownExceptionCapability",
        "RuntimeError",
        "ValueError",
        "Connection",
        ":memory:",
    ):
        assert forbidden not in rendered


def test_test_only_old_transaction_fake_rejects_after_new_generation_starts() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    epoch = _TestsOnlyTransitionReadCapabilityEpoch(connection)
    capability_a = epoch.start_for_test()
    try:
        assert _read_current_work_item(capability_a, "wi-1") is None

        epoch.end_for_test()
        capability_b = epoch.start_for_test()

        with pytest.raises(_MutationReadCapabilityError) as old_capability:
            _read_current_work_item(capability_a, "wi-1")
        assert old_capability.value.reason is _MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED
        assert _read_current_work_item(capability_b, "wi-1") is None
    finally:
        connection.close()


@pytest.mark.parametrize("case", READER_CASES, ids=[case.reader_name for case in READER_CASES])
def test_missing_table_schema_query_errors_are_integrity_failures(case: _ReaderCase) -> None:
    connection = _connect()
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _invoke(case, capability), "database_integrity_failure")
    finally:
        connection.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_ERROR", 1),
        _sqlite_error_code("SQLITE_SCHEMA", 17),
        _sqlite_error_code("SQLITE_CORRUPT", 11),
        _sqlite_error_code("SQLITE_NOTADB", 26),
        _sqlite_error_code("SQLITE_MISMATCH", 20),
        _sqlite_error_code("SQLITE_CONSTRAINT", 19),
        _sqlite_error_code("SQLITE_CONSTRAINT_CHECK", 275),
    ),
)
def test_schema_query_database_contradiction_sqlite_codes_are_integrity(sqlite_errorcode: int) -> None:
    error = _SyntheticSQLiteError(sqlite_errorcode)
    connection, _ = _scripted_connection(execute_error=error)
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(
            lambda: _read_current_work_item(capability, "wi-1"),
            "database_integrity_failure",
        )
    finally:
        connection.close()


@pytest.mark.parametrize(
    "sqlite_errorcode",
    (
        _sqlite_error_code("SQLITE_BUSY", 5),
        _sqlite_error_code("SQLITE_LOCKED", 6),
        _sqlite_error_code("SQLITE_IOERR", 10),
        _sqlite_error_code("SQLITE_FULL", 13),
        _sqlite_error_code("SQLITE_INTERRUPT", 9),
        123456,
        None,
    ),
)
def test_operational_sqlite_codes_are_mutation_failed(sqlite_errorcode: int | None) -> None:
    error = _SyntheticSQLiteError(sqlite_errorcode)
    connection, _ = _scripted_connection(execute_error=error)
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
    finally:
        connection.close()


def test_closed_connection_is_mutation_failed_and_redacted() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    _, capability = _capability_for(connection)
    connection.close()

    _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")


def test_cursor_cleanup_after_success_fetch_failure_and_close_failure() -> None:
    connection, cursor = _scripted_connection(rows=())
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        assert _read_current_work_item(capability, "wi-1") is None
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection, cursor = _scripted_connection(fetch_error=fetch_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_LOCKED", 6))
    connection, cursor = _scripted_connection(rows=(), close_error=close_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    close_error = sqlite3.IntegrityError(PRIVATE_SQLITE_SENTINEL)
    connection, cursor = _scripted_connection(rows=(), close_error=close_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(lambda: _read_current_work_item(capability, "wi-1"), "mutation_failed")
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()

    fetch_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_SCHEMA", 17))
    close_error = _SyntheticSQLiteError(_sqlite_error_code("SQLITE_BUSY", 5))
    connection, cursor = _scripted_connection(fetch_error=fetch_error, close_error=close_error)
    assert cursor is not None
    _, capability = _capability_for(connection)
    try:
        _assert_raises_sqlite_mutation_error(
            lambda: _read_current_work_item(capability, "wi-1"),
            "database_integrity_failure",
        )
        assert cursor.close_count == 1
        assert connection.close_count == 0
    finally:
        connection.close()


def test_reader_does_not_close_connection() -> None:
    connection = _prepare_table_with_rows(READER_CASES[0], 0)
    _, capability = _capability_for(connection)
    try:
        assert _read_current_work_item(capability, "wi-1") is None
        assert connection.close_count == 0
        assert connection.execute("SELECT 1").fetchone() == (1,)
    finally:
        connection.close()


def test_private_readers_have_no_production_call_sites_or_public_exports() -> None:
    assert _PRIVATE_READER_LIVE_OWNER_EXCLUSIONS == (
        "dynamic imports",
        "exec, eval, or generated code",
        "runtime monkey-patching",
        "computed attribute access",
        "setattr or delattr",
        "reflective namespace mutation",
        "nested-function global mutation plus call-flow analysis",
        "aliases to the controller class followed by attribute mutation",
        "arbitrary interprocedural value flow",
    )
    for name in READER_NAMES:
        assert name not in ge_nwp_coordinator.__all__
        assert not hasattr(ge_nwp_coordinator, name)

    assert READER_NAMES == frozenset(CANONICAL_READER_PROVENANCE)
    production_sources = {
        source_path.relative_to(ROOT).as_posix(): source_path.read_text(
            encoding="utf-8"
        )
        for source_path in PACKAGE_DIR.rglob("*.py")
    }
    assert READER_FACADE_PATH in production_sources
    assert {
        source_path for _, source_path in CANONICAL_READER_PROVENANCE.values()
    } <= set(production_sources)
    (
        observed_imports,
        observed_definitions,
        observed_reexports,
        observed_edges,
    ) = _scan_private_reader_bindings(production_sources)
    assert observed_imports == EXPECTED_PRODUCTION_READER_IMPORTS
    assert observed_definitions == EXPECTED_CANONICAL_READER_DEFINITIONS
    assert observed_reexports == EXPECTED_APPROVED_READER_REEXPORTS
    assert observed_edges == EXPECTED_PRODUCTION_READER_EDGES

    def assert_scan_rejected(
        challenge_sources: dict[str, str],
        reason: str,
    ) -> None:
        for relative_path, source in challenge_sources.items():
            ast.parse(source, filename=relative_path)
            compile(source, relative_path, "exec")
        with pytest.raises(AssertionError, match=f"^{reason}$") as raised:
            _scan_private_reader_bindings(challenge_sources)
        assert raised.value.args == (reason,)

    def replace_once(source: str, old: str, new: str) -> str:
        assert source.count(old) == 1
        return source.replace(old, new, 1)

    def move_direct_definition_under_false(source: str, name: str) -> str:
        tree = ast.parse(source)
        candidates = tuple(
            node
            for node in tree.body
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            )
            and node.name == name
        )
        assert len(candidates) == 1
        selected = candidates[0]
        assert selected.end_lineno is not None
        lines = source.splitlines(keepends=True)
        definition_lines = lines[selected.lineno - 1 : selected.end_lineno]
        lines[selected.lineno - 1 : selected.end_lineno] = [
            "if False:\n",
            *(f"    {line}" if line.strip() else line for line in definition_lines),
        ]
        return "".join(lines)

    def append_direct_class_body_statement(
        source: str,
        class_name: str,
        statement: str,
    ) -> str:
        tree = ast.parse(source)
        candidates = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )
        assert len(candidates) == 1
        selected = candidates[0]
        assert selected.end_lineno is not None
        lines = source.splitlines(keepends=True)
        lines.insert(selected.end_lineno, f"    {statement}\n")
        return "".join(lines)

    initialization_path = (
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py"
    )
    transaction_path = "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
    initialization_import = (
        "from .sqlite_transition_read_scope import _read_global_stop_current\n"
    )
    direct_call = "    stop_envelope = _read_global_stop_current(capability)\n"
    initialization_source = production_sources[initialization_path]
    transaction_source = production_sources[transaction_path]
    assert initialization_source.count(initialization_import) == 1
    assert initialization_source.count(direct_call) == 1
    expected_initialization_imports = tuple(
        record
        for record in EXPECTED_PRODUCTION_READER_IMPORTS
        if record[0] == initialization_path
    )
    expected_initialization_edges = tuple(
        edge
        for edge in EXPECTED_PRODUCTION_READER_EDGES
        if edge[0] == initialization_path
    )
    assert _scan_private_reader_bindings(
        {initialization_path: initialization_source}
    ) == (
        expected_initialization_imports,
        (),
        (),
        expected_initialization_edges,
    )

    direct_duplicate_source = replace_once(
        initialization_source,
        direct_call,
        direct_call + "    _read_global_stop_current(capability)\n",
    )
    (
        direct_duplicate_imports,
        direct_duplicate_definitions,
        direct_duplicate_reexports,
        direct_duplicate_edges,
    ) = _scan_private_reader_bindings(
        {initialization_path: direct_duplicate_source}
    )
    assert direct_duplicate_imports == expected_initialization_imports
    assert direct_duplicate_definitions == ()
    assert direct_duplicate_reexports == ()
    assert next(
        edge[3]
        for edge in direct_duplicate_edges
        if edge[:3]
        == (
            initialization_path,
            "_resolve_development_program_initialization_apply_after_fencing",
            "_read_global_stop_current",
        )
    ) == 2
    assert direct_duplicate_edges != expected_initialization_edges

    reader_module = READER_FACADE_MODULE
    reader_name = "_read_global_stop_current"
    aliased_import = (
        "from .sqlite_transition_read_scope import "
        "_read_global_stop_current as read_stop\n"
    )
    aliased_call = "    stop_envelope = read_stop(capability)\n"
    import_alias_source = replace_once(
        replace_once(
            initialization_source,
            initialization_import,
            aliased_import,
        ),
        direct_call,
        aliased_call,
    )
    (
        import_alias_imports,
        import_alias_definitions,
        import_alias_reexports,
        import_alias_edges,
    ) = _scan_private_reader_bindings(
        {initialization_path: import_alias_source}
    )
    assert import_alias_imports == expected_initialization_imports
    assert import_alias_definitions == ()
    assert import_alias_reexports == ()
    assert import_alias_edges == expected_initialization_edges

    module_alias_import = (
        "from . import sqlite_transition_read_scope as readers\n"
    )
    module_alias_call = (
        "    stop_envelope = readers._read_global_stop_current(capability)\n"
    )
    module_alias_source = replace_once(
        replace_once(
            initialization_source,
            initialization_import,
            module_alias_import,
        ),
        direct_call,
        module_alias_call,
    )
    (
        module_alias_imports,
        module_alias_definitions,
        module_alias_reexports,
        module_alias_edges,
    ) = _scan_private_reader_bindings(
        {initialization_path: module_alias_source}
    )
    assert module_alias_imports == (
        (
            initialization_path,
            1,
            None,
            ("sqlite_transition_read_scope",),
        ),
    )
    assert module_alias_definitions == ()
    assert module_alias_reexports == ()
    assert module_alias_edges == expected_initialization_edges
    assert module_alias_imports != expected_initialization_imports

    defining_module, defining_path = CANONICAL_READER_PROVENANCE[reader_name]
    defining_direct_path = (
        "src/ge_nwp_coordinator/_reader_defining_direct_challenge.py"
    )
    defining_direct_source = (
        f"from {defining_module} import {reader_name} as read_stop\n\n"
        "def consumer(capability):\n"
        "    return read_stop(capability)\n"
    )
    assert_scan_rejected(
        {defining_direct_path: defining_direct_source},
        "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE",
    )

    defining_alias_path = "src/ge_nwp_coordinator/_reader_defining_alias_challenge.py"
    defining_alias_source = (
        f"import {defining_module} as readers\n\n"
        "def consumer(capability):\n"
        f"    return readers.{reader_name}(capability)\n"
    )
    assert_scan_rejected(
        {defining_alias_path: defining_alias_source},
        "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE",
    )

    unapproved_consumer_path = (
        "src/ge_nwp_coordinator/_reader_unapproved_consumer.py"
    )
    assert_scan_rejected(
        {
            unapproved_consumer_path: (
                f"from {reader_module} import {reader_name}\n"
                f"{reader_name}(capability)\n"
            )
        },
        "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE",
    )

    local_import_source = (
        initialization_source.replace(initialization_import, "", 1)
        + "\n\ndef _scanner_unrelated_import_holder():\n"
        + "    from .sqlite_transition_read_scope import "
        + "_read_global_stop_current\n"
        + "    return None\n"
    )
    assert_scan_rejected(
        {initialization_path: local_import_source},
        "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE",
    )

    nested_owner_import_source = replace_once(
        initialization_source.replace(initialization_import, "", 1),
        direct_call,
        "    from .sqlite_transition_read_scope import "
        "_read_global_stop_current\n"
        + direct_call,
    )
    assert_scan_rejected(
        {initialization_path: nested_owner_import_source},
        "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE",
    )

    conditional_import_source = replace_once(
        initialization_source,
        initialization_import,
        "if True:\n"
        "    from .sqlite_transition_read_scope import "
        "_read_global_stop_current\n",
    )
    assert_scan_rejected(
        {initialization_path: conditional_import_source},
        "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE",
    )

    facade_source = production_sources[READER_FACADE_PATH]
    exact_reexport = (
        "from ge_nwp_coordinator.sqlite_global_stop_readers import "
        "_read_global_stop_current\n"
    )
    assert facade_source.count(exact_reexport) == 1
    nested_reexport_source = (
        facade_source.replace(exact_reexport, "", 1)
        + "\n\ndef _scanner_nested_reexport_holder():\n"
        + "    from ge_nwp_coordinator.sqlite_global_stop_readers import "
        + "_read_global_stop_current\n"
        + "    return None\n"
    )
    assert_scan_rejected(
        {READER_FACADE_PATH: nested_reexport_source},
        "PRIVATE_READER_IMPORT_NOT_APPROVED_MODULE_SCOPE",
    )
    assert_scan_rejected(
        {READER_FACADE_PATH: facade_source + "\n" + exact_reexport},
        "PRIVATE_READER_BINDING_REBOUND",
    )
    assert_scan_rejected(
        {
            READER_FACADE_PATH: replace_once(
                facade_source,
                exact_reexport,
                exact_reexport.rstrip("\n") + " as read_stop\n",
            )
        },
        "PRIVATE_READER_UNAUTHORIZED_IMPORT_SOURCE",
    )

    import_alias_duplicate_source = replace_once(
        import_alias_source,
        aliased_call,
        "    read_stop(capability)\n" + aliased_call,
    )
    (
        duplicate_alias_imports,
        duplicate_alias_definitions,
        duplicate_alias_reexports,
        duplicate_alias_edges,
    ) = _scan_private_reader_bindings(
        {initialization_path: import_alias_duplicate_source}
    )
    assert duplicate_alias_imports == import_alias_imports
    assert duplicate_alias_definitions == ()
    assert duplicate_alias_reexports == ()
    assert duplicate_alias_edges == tuple(
        (*edge[:3], 2) for edge in expected_initialization_edges
    )
    assert duplicate_alias_edges != import_alias_edges

    indirect_injections = (
        (
            "local_alias",
            "    extra_reader = read_stop\n",
        ),
        (
            "passed",
            "    sink(read_stop)\n",
        ),
        (
            "returned",
            "    returned_reader = read_stop\n",
        ),
        ("tuple", "    stored_tuple = (read_stop,)\n"),
        ("list", "    stored_list = [read_stop]\n"),
        ("dict", "    stored_dict = {'reader': read_stop}\n"),
        ("set", "    stored_set = {read_stop}\n"),
        ("attribute", "    holder.reader = read_stop\n"),
        (
            "closure",
            "    captured_reader = read_stop\n"
            "    def inner(capability):\n"
            "        return captured_reader(capability)\n",
        ),
        (
            "positional_default_capture",
            "    def captured(reader=read_stop):\n"
            "        return reader\n",
        ),
        (
            "keyword_default_capture",
            "    def captured(*, reader=read_stop):\n"
            "        return reader\n",
        ),
    )
    for challenge_name, injection in indirect_injections:
        challenge_source = replace_once(
            import_alias_source,
            aliased_call,
            injection + aliased_call,
        )
        assert_scan_rejected(
            {initialization_path: challenge_source},
            "PRIVATE_READER_INDIRECT_USE",
        )

    module_attribute_source = replace_once(
        module_alias_source,
        module_alias_call,
        "    stored_reader = readers._read_global_stop_current\n"
        + module_alias_call,
    )
    assert_scan_rejected(
        {initialization_path: module_attribute_source},
        "PRIVATE_READER_INDIRECT_USE",
    )

    getattr_source = replace_once(
        module_alias_source,
        module_alias_call,
        "    getattr(readers, '_read_global_stop_current')(capability)\n"
        + module_alias_call,
    )
    assert_scan_rejected(
        {initialization_path: getattr_source},
        "PRIVATE_READER_INDIRECT_USE",
    )

    shadow_injections = (
        ("reassigned", "    read_stop = replacement\n"),
        ("deleted", "    del read_stop\n"),
        (
            "parameter",
            "    def nested(read_stop):\n"
            "        return None\n",
        ),
        (
            "nested_assignment",
            "    def nested():\n"
            "        read_stop = replacement\n"
            "        return read_stop\n",
        ),
        (
            "exception",
            "    try:\n"
            "        pass\n"
            "    except Exception as read_stop:\n"
            "        pass\n",
        ),
        (
            "pattern",
            "    match value:\n"
            "        case read_stop:\n"
            "            pass\n",
        ),
        (
            "function",
            "    def read_stop():\n"
            "        return None\n",
        ),
        (
            "class",
            "    class read_stop:\n"
            "        pass\n",
        ),
        ("import", "    import os as read_stop\n"),
        (
            "comprehension",
            "    values = [read_stop for read_stop in items]\n",
        ),
    )
    for challenge_name, injection in shadow_injections:
        challenge_source = replace_once(
            import_alias_source,
            aliased_call,
            injection + aliased_call,
        )
        assert_scan_rejected(
            {initialization_path: challenge_source},
            "PRIVATE_READER_BINDING_REBOUND",
        )

    module_shadow_source = replace_once(
        module_alias_source,
        module_alias_call,
        "    readers = replacement\n" + module_alias_call,
    )
    assert_scan_rejected(
        {initialization_path: module_shadow_source},
        "PRIVATE_READER_BINDING_REBOUND",
    )

    facade_wildcard_source = f"from {reader_module} import *\n"
    assert_scan_rejected(
        {"src/ge_nwp_coordinator/_reader_facade_wildcard.py": facade_wildcard_source},
        "PRIVATE_READER_WILDCARD_IMPORT",
    )
    defining_wildcard_source = f"from {defining_module} import *\n"
    assert_scan_rejected(
        {"src/ge_nwp_coordinator/_reader_defining_wildcard.py": defining_wildcard_source},
        "PRIVATE_READER_WILDCARD_IMPORT",
    )
    unrelated_wildcard_source = (
        import_alias_source + "\nfrom ge_nwp_coordinator.unrelated import *\n"
    )
    assert_scan_rejected(
        {initialization_path: unrelated_wildcard_source},
        "PRIVATE_READER_BINDING_REBOUND",
    )

    same_spelling_path = "src/ge_nwp_coordinator/_same_spelling_challenge.py"
    same_spelling_source = (
        f"def {reader_name}(capability):\n"
        "    return None\n\n"
        "def consumer(capability):\n"
        f"    return {reader_name}(capability)\n"
    )
    assert _scan_private_reader_bindings(
        {same_spelling_path: same_spelling_source}
    ) == ((), (), (), ())

    scope_source = (
        exact_reexport
        + "\n@decorate(_read_global_stop_current(capability))\n"
        + "def outer(\n"
        + "    value: _read_global_stop_current(capability) = "
        + "_read_global_stop_current(capability),\n"
        + "    *,\n"
        + "    option=_read_global_stop_current(capability),\n"
        + ") -> _read_global_stop_current(capability):\n"
        + "    def inner():\n"
        + "        return _read_global_stop_current(capability)\n"
        + "    return inner\n\n"
        + "def generic[T: _read_global_stop_current(capability)]():\n"
        + "    return None\n\n"
        + "@decorate(_read_global_stop_current(capability))\n"
        + "class Consumer(base(_read_global_stop_current(capability)), "
        + "metaclass=meta(_read_global_stop_current(capability))):\n"
        + "    value = _read_global_stop_current(capability)\n"
        + "    def method(self):\n"
        + "        return _read_global_stop_current(capability)\n\n"
        + "consumer_lambda = lambda capability: "
        + "_read_global_stop_current(capability)\n"
    )
    scope_imports, _, scope_reexports, scope_edges = (
        _scan_private_reader_bindings({READER_FACADE_PATH: scope_source})
    )
    assert scope_imports == ()
    assert scope_reexports == EXPECTED_APPROVED_READER_REEXPORTS
    scope_tree = ast.parse(scope_source, filename=READER_FACADE_PATH)
    lambda_node = next(
        node for node in ast.walk(scope_tree) if isinstance(node, ast.Lambda)
    )
    lambda_owner = f"<lambda@{lambda_node.lineno}:{lambda_node.col_offset}>"
    assert {
        (owner_name, canonical_reader): count
        for _, owner_name, canonical_reader, count in scope_edges
    } == {
        ("<module>", reader_name): 9,
        ("outer.inner", reader_name): 1,
        ("Consumer", reader_name): 1,
        ("Consumer.method", reader_name): 1,
        (lambda_owner, reader_name): 1,
    }

    facade_internal_source = (
        facade_source
        + "\n\ndef _scanner_internal_facade_challenge(capability):\n"
        + f"    return {reader_name}(capability)\n"
    )
    (
        facade_internal_imports,
        facade_internal_definitions,
        facade_internal_reexports,
        facade_internal_edges,
    ) = _scan_private_reader_bindings(
        {READER_FACADE_PATH: facade_internal_source}
    )
    assert facade_internal_imports == ()
    assert facade_internal_definitions == tuple(
        definition
        for definition in EXPECTED_CANONICAL_READER_DEFINITIONS
        if definition[0] == READER_FACADE_PATH
    )
    assert facade_internal_reexports == EXPECTED_APPROVED_READER_REEXPORTS
    assert facade_internal_edges == (
        (
            READER_FACADE_PATH,
            "_scanner_internal_facade_challenge",
            reader_name,
            1,
        ),
    )
    assert facade_internal_edges != EXPECTED_PRODUCTION_READER_EDGES

    defining_source = production_sources[defining_path]
    defining_internal_source = (
        defining_source
        + "\n\ndef _scanner_internal_definition_challenge(capability):\n"
        + f"    return {reader_name}(capability)\n"
    )
    (
        defining_internal_imports,
        defining_internal_definitions,
        defining_internal_reexports,
        defining_internal_edges,
    ) = _scan_private_reader_bindings({defining_path: defining_internal_source})
    assert defining_internal_imports == ()
    assert defining_internal_definitions == (
        (defining_path, defining_module, reader_name),
    )
    assert defining_internal_reexports == ()
    assert defining_internal_edges == (
        (
            defining_path,
            "_scanner_internal_definition_challenge",
            reader_name,
            1,
        ),
    )
    assert defining_internal_edges != EXPECTED_PRODUCTION_READER_EDGES

    function_header = (
        "def _resolve_development_program_initialization_apply_after_fencing("
    )
    function_typevar_source = replace_once(
        initialization_source,
        function_header,
        "def _resolve_development_program_initialization_apply_after_fencing"
        "[_read_global_stop_current](",
    )
    function_typevar_tree = ast.parse(
        function_typevar_source,
        filename=initialization_path,
    )
    function_typevar_owner = next(
        node
        for node in function_typevar_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        == "_resolve_development_program_initialization_apply_after_fencing"
    )
    assert len(function_typevar_owner.type_params) == 1
    assert type(function_typevar_owner.type_params[0]) is ast.TypeVar
    assert_scan_rejected(
        {initialization_path: function_typevar_source},
        "PRIVATE_READER_BINDING_REBOUND",
    )

    async_paramspec_source = replace_once(
        initialization_source,
        function_header,
        "async def _resolve_development_program_initialization_apply_after_fencing"
        "[**_read_global_stop_current](",
    )
    async_paramspec_tree = ast.parse(
        async_paramspec_source,
        filename=initialization_path,
    )
    async_paramspec_owner = next(
        node
        for node in async_paramspec_tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        == "_resolve_development_program_initialization_apply_after_fencing"
    )
    assert len(async_paramspec_owner.type_params) == 1
    assert type(async_paramspec_owner.type_params[0]) is ast.ParamSpec
    assert_scan_rejected(
        {initialization_path: async_paramspec_source},
        "PRIVATE_READER_BINDING_REBOUND",
    )

    controller_header = "class _CoordinatorMutationTransactionController:\n"
    class_typevartuple_source = replace_once(
        transaction_source,
        controller_header,
        "class _CoordinatorMutationTransactionController"
        "[*_read_global_stop_current]:\n",
    )
    class_typevartuple_tree = ast.parse(
        class_typevartuple_source,
        filename=transaction_path,
    )
    class_typevartuple_owner = next(
        node
        for node in class_typevartuple_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "_CoordinatorMutationTransactionController"
    )
    assert len(class_typevartuple_owner.type_params) == 1
    assert type(class_typevartuple_owner.type_params[0]) is ast.TypeVarTuple
    assert_scan_rejected(
        {transaction_path: class_typevartuple_source},
        "PRIVATE_READER_BINDING_REBOUND",
    )

    type_alias_source = replace_once(
        initialization_source,
        direct_call,
        "    type _ReaderAlias[_read_global_stop_current] = int\n"
        + direct_call,
    )
    type_alias_tree = ast.parse(type_alias_source, filename=initialization_path)
    type_alias_node = next(
        node for node in ast.walk(type_alias_tree) if isinstance(node, ast.TypeAlias)
    )
    assert len(type_alias_node.type_params) == 1
    assert type(type_alias_node.type_params[0]) is ast.TypeVar
    assert_scan_rejected(
        {initialization_path: type_alias_source},
        "PRIVATE_READER_BINDING_REBOUND",
    )

    duplicate_top_level_owner_source = (
        initialization_source
        + "\n\ndef _resolve_development_program_initialization_apply_after_fencing"
        + "(*args, **kwargs):\n"
        + "    return None\n"
    )
    assert_scan_rejected(
        {initialization_path: duplicate_top_level_owner_source},
        "PRIVATE_READER_OWNER_COLLISION",
    )

    transition_method_header = "    def _run_until_transition_resolution(\n"
    duplicate_method_source = replace_once(
        transaction_source,
        transition_method_header,
        "    def _run_until_transition_resolution(self, *args, **kwargs):\n"
        "        return None\n\n"
        + transition_method_header,
    )
    assert_scan_rejected(
        {transaction_path: duplicate_method_source},
        "PRIVATE_READER_OWNER_COLLISION",
    )

    duplicate_class_source = (
        transaction_source
        + "\n\nclass _CoordinatorMutationTransactionController:\n"
        + "    pass\n"
    )
    assert_scan_rejected(
        {transaction_path: duplicate_class_source},
        "PRIVATE_READER_OWNER_COLLISION",
    )

    conditional_owner_source = (
        initialization_source
        + "\n\nif condition:\n"
        + "    def _resolve_development_program_initialization_apply_after_fencing"
        + "(*args, **kwargs):\n"
        + "        return None\n"
    )
    assert_scan_rejected(
        {initialization_path: conditional_owner_source},
        "PRIVATE_READER_OWNER_COLLISION",
    )

    live_owner_challenges = (
        (
            initialization_path,
            initialization_source
            + f"\n{_INITIALIZER_OWNER_NAME} = lambda: None\n",
        ),
        (
            initialization_path,
            initialization_source + f"\ndel {_INITIALIZER_OWNER_NAME}\n",
        ),
        (
            transaction_path,
            transaction_source + f"\n{_CONTROLLER_OWNER_NAME} = object\n",
        ),
        (
            transaction_path,
            transaction_source + f"\ndel {_CONTROLLER_OWNER_NAME}\n",
        ),
        (
            initialization_path,
            move_direct_definition_under_false(
                initialization_source,
                _INITIALIZER_OWNER_NAME,
            ),
        ),
        (
            transaction_path,
            move_direct_definition_under_false(
                transaction_source,
                _CONTROLLER_OWNER_NAME,
            ),
        ),
        (
            transaction_path,
            append_direct_class_body_statement(
                transaction_source,
                _CONTROLLER_OWNER_NAME,
                f"{_CONTROLLER_GLOBAL_STOP_METHOD_NAME} = replacement",
            ),
        ),
        (
            transaction_path,
            append_direct_class_body_statement(
                transaction_source,
                _CONTROLLER_OWNER_NAME,
                f"del {_CONTROLLER_TRANSITION_METHOD_NAME}",
            ),
        ),
        (
            transaction_path,
            transaction_source
            + f"\n{_CONTROLLER_GLOBAL_STOP_OWNER_NAME} = replacement\n",
        ),
        (
            transaction_path,
            transaction_source + f"\ndel {_CONTROLLER_TRANSITION_OWNER_NAME}\n",
        ),
        (
            initialization_path,
            replace_once(
                initialization_source,
                function_header,
                "@audit_decorator\n" + function_header,
            ),
        ),
        (
            transaction_path,
            replace_once(
                transaction_source,
                controller_header,
                "@audit_decorator\n" + controller_header,
            ),
        ),
        (
            transaction_path,
            transaction_source
            + f"\n{_CONTROLLER_GLOBAL_STOP_OWNER_NAME}: object = replacement\n",
        ),
        (
            transaction_path,
            transaction_source
            + f"\n{_CONTROLLER_TRANSITION_OWNER_NAME} += replacement\n",
        ),
    )
    for challenge_path, challenge_source in live_owner_challenges:
        assert_scan_rejected(
            {challenge_path: challenge_source},
            _PRIVATE_READER_OWNER_NOT_LIVE,
        )

    def exact_protected_method_targets(tree: ast.Module) -> tuple[ast.Attribute, ...]:
        return tuple(
            node
            for node in ast.walk(tree)
            if type(node) is ast.Attribute
            and type(node.ctx) in (ast.Store, ast.Del)
            and type(node.value) is ast.Name
            and node.value.id == _CONTROLLER_OWNER_NAME
            and node.attr
            in {
                _CONTROLLER_GLOBAL_STOP_METHOD_NAME,
                _CONTROLLER_TRANSITION_METHOD_NAME,
            }
        )

    def assert_module_initialization_target_rejected(
        appendix: str,
        expected_context: type[ast.Store] | type[ast.Del],
    ) -> None:
        assert all(reader_name not in appendix for reader_name in READER_NAMES)
        challenge_source = transaction_source + appendix
        tree = ast.parse(challenge_source, filename=transaction_path)
        compile(challenge_source, transaction_path, "exec")
        targets = exact_protected_method_targets(tree)
        assert len(targets) == 1
        assert type(targets[0].ctx) is expected_context
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        assert _is_module_initialization_protected_method_target(
            targets[0],
            parents,
        )
        assert_scan_rejected(
            {transaction_path: challenge_source},
            _PRIVATE_READER_OWNER_NOT_LIVE,
        )

    module_initialization_target_challenges = (
        (
            ast.Store,
            "\n\nclass _ScannerClassBodyAssignChallenge:\n"
            "    _CoordinatorMutationTransactionController."
            "_run_until_global_stop_resolution = None\n",
        ),
        (
            ast.Store,
            "\n\nclass _ScannerClassBodyAnnAssignChallenge:\n"
            "    _CoordinatorMutationTransactionController."
            "_run_until_transition_resolution: object = None\n",
        ),
        (
            ast.Store,
            "\n\nclass _ScannerClassBodyAugAssignChallenge:\n"
            "    _CoordinatorMutationTransactionController."
            "_run_until_global_stop_resolution += replacement\n",
        ),
        (
            ast.Del,
            "\n\nclass _ScannerClassBodyDeleteChallenge:\n"
            "    del _CoordinatorMutationTransactionController."
            "_run_until_transition_resolution\n",
        ),
        (
            ast.Store,
            "\n\nif True:\n"
            "    class _ScannerConditionalClassBodyChallenge:\n"
            "        _CoordinatorMutationTransactionController."
            "_run_until_global_stop_resolution = None\n",
        ),
        (
            ast.Store,
            "\n\nclass _ScannerOuterClassBodyChallenge:\n"
            "    class _ScannerNestedClassBodyChallenge:\n"
            "        _CoordinatorMutationTransactionController."
            "_run_until_transition_resolution = None\n",
        ),
        (
            ast.Store,
            "\n\nclass _ScannerTupleTargetChallenge:\n"
            "    (_CoordinatorMutationTransactionController."
            "_run_until_global_stop_resolution, _scanner_other_target) = "
            "(None, None)\n",
        ),
        (
            ast.Store,
            "\n\nclass _ScannerForTargetChallenge:\n"
            "    for _CoordinatorMutationTransactionController."
            "_run_until_transition_resolution in (None,):\n"
            "        pass\n",
        ),
    )
    for expected_context, appendix in module_initialization_target_challenges:
        assert_module_initialization_target_rejected(
            appendix,
            expected_context,
        )

    deferred_callable_sources = (
        (
            ast.FunctionDef,
            "def _scanner_deferred_function():\n"
            "    _CoordinatorMutationTransactionController."
            "_run_until_global_stop_resolution = None\n",
        ),
        (
            ast.AsyncFunctionDef,
            "async def _scanner_deferred_async_function():\n"
            "    del _CoordinatorMutationTransactionController."
            "_run_until_transition_resolution\n",
        ),
    )
    for expected_boundary, deferred_source in deferred_callable_sources:
        deferred_tree = ast.parse(deferred_source)
        compile(deferred_source, "<deferred-callable-boundary>", "exec")
        deferred_targets = exact_protected_method_targets(deferred_tree)
        assert len(deferred_targets) == 1
        deferred_parents = {
            child: parent
            for parent in ast.walk(deferred_tree)
            for child in ast.iter_child_nodes(parent)
        }
        assert any(
            type(parent) is expected_boundary
            for parent in ast.walk(deferred_tree)
        )
        assert not _is_module_initialization_protected_method_target(
            deferred_targets[0],
            deferred_parents,
        )

    lambda_tree = ast.parse("_scanner_deferred_lambda = lambda: None")
    lambda_boundary = next(
        node for node in ast.walk(lambda_tree) if type(node) is ast.Lambda
    )
    synthetic_lambda_target = ast.Attribute(
        value=ast.Name(id=_CONTROLLER_OWNER_NAME, ctx=ast.Load()),
        attr=_CONTROLLER_GLOBAL_STOP_METHOD_NAME,
        ctx=ast.Store(),
    )
    assert not _is_module_initialization_protected_method_target(
        synthetic_lambda_target,
        {synthetic_lambda_target: lambda_boundary},
    )

    assert list(__import__("inspect").signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(__import__("inspect").signature(StateStore.read_global_stop).parameters) == ["self"]
    writer_session_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")
    report_source = (PACKAGE_DIR / "reports.py").read_text(encoding="utf-8")
    for name in READER_NAMES:
        assert name not in writer_session_source
        assert name not in report_source


def test_reader_source_has_no_production_capability_factory_transaction_or_mutation_sql() -> None:
    source = READ_SCOPE_PATH.read_text(encoding="utf-8")
    support_source = SELECT_SUPPORT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    support_tree = ast.parse(support_source)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    support_class_names = {node.name for node in ast.walk(support_tree) if isinstance(node, ast.ClassDef)}
    assert "_MutationReadCapability" not in class_names
    assert "_MutationReadCapability" in support_class_names
    assert not any(name.endswith("Capability") for name in class_names)
    assert not any(name.endswith("Capability") and name != "_MutationReadCapability" for name in support_class_names)

    for forbidden in (
        "sqlite3.connect",
        "connection.close",
        "StateStore",
        "WriterSession",
        "TransitionContext",
        "TransitionConflict",
        "validate_b3_work_item_authority_binding",
        "transition_events",
        "global_stop_events",
        "writer_ownership",
        "schema_migrations",
        "operator_decision_history",
    ):
        assert forbidden not in source

    forbidden_calls = {"executemany", "executescript", "commit", "rollback"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_calls


def test_tests_only_schema_setup_is_not_a_fixture_or_production_capability_program() -> None:
    assert not (PACKAGE_DIR / "sqlite_transition_fixtures.py").exists()
    assert not (PACKAGE_DIR / "sqlite_transition_readers.py").exists()
    assert sorted(path.name for path in (PACKAGE_DIR / "sqlite_migrations").glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
    ]
    assert json.loads(json.dumps({"capability": "tests-only"})) == {"capability": "tests-only"}


def test_b3b2b_docs_pin_private_unintegrated_reader_scope() -> None:
    docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            ".docs/b3b2b-select-readers.md",
            ".docs/b3-transition-persistence-contract.md",
            ".docs/durable-state-model.md",
            ".docs/writer-session-authority.md",
            "README.md",
            "AGENTS.md",
        )
    )
    normalized = " ".join(docs.split())
    for phrase in (
        "private SELECT readers implemented and test-executed; no production integration",
        "No production module calls them",
        "lookup-ref validation before capability borrowing",
        "fetchmany(2)",
        "exact built-in tuple",
        "delegating to the B3b1 single-row adapter",
        "`global_stop_current` absence raises `database_integrity_failure` directly",
        "`commit_outcome_unknown` is never produced by B3b2b",
        "The tests-only capability does not prove production transaction authority",
        "B3c1b now implements the nominal concrete capability only inside its private rollback-only writer-fencing controller",
        "Production integration for B3b2 current/context readers waits for a later B3c slice",
        "No `StateStore` mutation backend, integrated production typed SQLite reader",
    ):
        assert phrase in normalized
