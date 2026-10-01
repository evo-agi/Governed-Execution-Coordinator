"""Finite source-module boundary checks for C2A1, not a Python security analyzer."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import tomllib

import ge_nwp_coordinator
import ge_nwp_coordinator._worker_execution_semantic_values as semantic_values


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = (
    ROOT
    / "src"
    / "ge_nwp_coordinator"
    / "_worker_execution_semantic_values.py"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_max_pull_requests_is_declared_normally_without_dynamic_class_mutation() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    ceiling_fields = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_CEILING_FIELDS"
            for target in node.targets
        )
    )
    assert isinstance(ceiling_fields.value, ast.Tuple)
    assert "max_pull_requests" in tuple(
        element.value
        for element in ceiling_fields.value.elts
        if isinstance(element, ast.Constant)
    )

    ceilings_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "CeilingsV1"
    )
    slots = next(
        node
        for node in ceilings_class.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__slots__"
            for target in node.targets
        )
    )
    assert isinstance(slots.value, ast.Tuple)
    assert "_max_pull_requests" in tuple(
        element.value
        for element in slots.value.elts
        if isinstance(element, ast.Constant)
    )

    property_definition = next(
        node
        for node in ceilings_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "max_pull_requests"
    )
    assert [
        decorator.id
        for decorator in property_definition.decorator_list
        if isinstance(decorator, ast.Name)
    ] == ["property"]
    assert any(
        isinstance(node, ast.Attribute) and node.attr == "_max_pull_requests"
        for node in ast.walk(property_definition)
    )
    assert sum(
        isinstance(node, ast.Attribute) and node.attr == "max_pull_requests"
        for node in ast.walk(tree)
    ) >= 4


def test_semantic_values_module_contains_no_dynamic_field_injection() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert re.search(
        r"[\"']_?max_pull_requ[\"']\s*[\"']ests[\"']", source
    ) is None
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setattr"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "max_pull_requests"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "CeilingsV1"
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in tree.body
    )


def test_exact_one_c2a1_production_source_module_and_internal_export_posture() -> None:
    candidates = tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "src").rglob("*.py")
            if "worker_execution_semantic" in path.name
        )
    )
    assert candidates == (
        "src/ge_nwp_coordinator/_worker_execution_semantic_values.py",
    )
    assert semantic_values.__all__ == ()
    assert ge_nwp_coordinator.__all__ == [
        "AuthorizationDecision",
        "CommittedGlobalStopUpdate",
        "CommittedTransition",
        "DependencyDecision",
        "FiniteBacklog",
        "GlobalStopApplyPreflightError",
        "GlobalStopApplyPreflightFailureReason",
        "GlobalStopConflict",
        "LEASE_SCHEMA_ID",
        "LeaseIdentityValidation",
        "LeaseRuntimeDecision",
        "LeaseRuntimeStatus",
        "SafeWriterMetadata",
        "StateStore",
        "StandingLease",
        "TransitionApplyPreflightError",
        "TransitionApplyPreflightFailureReason",
        "TransitionCommand",
        "TransitionContext",
        "TransitionConflict",
        "TransitionEvaluation",
        "TransitionEvent",
        "TransitionEventOutcome",
        "UnsupportedAuthorizationProvider",
        "WriterSessionError",
        "WriterSessionFailureReason",
        "WriterSession",
        "WorkItem",
        "WorkItemRecord",
        "WorkItemState",
        "derive_lease_runtime_decision",
        "evaluate_transition",
        "transition",
        "validate_standing_lease",
    ]
    for name in (
        "CeilingsV1",
        "CapsuleEntryV1",
        "WorkSpecV1",
        "AttemptFenceV1",
        "EffectFenceV1",
        "WorkerCommandV1",
        "DeliveryEnvelopeV1",
        "WorkerObservationV1",
        "CandidateCapsuleManifestV1",
        "WorkerExecutionValueError",
        "create_author_command_and_effect_fence",
        "create_effect_fence",
        "validate_authoring_relation",
        "validate_effect_relation",
        "validate_delivery_relation",
        "validate_redelivery_relation",
        "validate_capsule_manifest_relation",
        "validate_observation_relation",
    ):
        assert hasattr(semantic_values, name)
        assert not hasattr(ge_nwp_coordinator, name)


def test_private_owner_reconstruction_has_closed_class_inventory_and_no_export() -> None:
    expected = (
        (semantic_values.CeilingsV1, 16),
        (semantic_values.CapsuleEntryV1, 8),
        (semantic_values.WorkSpecV1, 86),
        (semantic_values.AttemptFenceV1, 46),
        (semantic_values.EffectFenceV1, 51),
        (semantic_values.WorkerCommandV1, 58),
        (semantic_values.DeliveryEnvelopeV1, 16),
        (semantic_values.CandidateCapsuleManifestV1, 49),
    )
    assert semantic_values._EXACT_WORKER_EXECUTION_RECONSTRUCTION_GRAPHS == expected
    assert all(
        name not in ge_nwp_coordinator.__dict__
        for name in (
            "_WorkerExecutionReconstructionBudget",
            "_exact_worker_execution_reconstruction_work",
            "_reconstruct_exact_worker_execution_value",
        )
    )
    assert all(
        value_type is not semantic_values.WorkerObservationV1
        for value_type, _work in expected
    )


def test_source_specific_import_and_ast_boundary_is_finite() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    assert imports == {"__future__", "datetime", "hashlib", "json", "re", "typing"}
    assert not imports & {
        "http",
        "importlib",
        "logging",
        "multiprocessing",
        "os",
        "pathlib",
        "random",
        "shutil",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "urllib",
        "uuid",
    }
    assert not any(
        module.startswith("ge_nwp_coordinator") or module.startswith("tests")
        for module in imports
    )

    direct_calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not direct_calls & {
        "__import__",
        "compile",
        "eval",
        "exec",
        "input",
        "open",
        "print",
    }
    attribute_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not attribute_calls & {
        "load",
        "loads",
        "now",
        "today",
        "utcnow",
    }
    assert not any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(tree))


def test_source_has_no_mutable_module_registry_cache_or_logging() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    mutable_nodes = (ast.Dict, ast.DictComp, ast.List, ast.ListComp, ast.Set, ast.SetComp)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        assert not isinstance(value, mutable_nodes)
    assigned_names = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert not any("registry" in name.lower() or "cache" in name.lower() for name in assigned_names)
    assert "logging" not in SOURCE_PATH.read_text(encoding="utf-8")


def test_source_has_no_authority_execution_storage_or_wire_api() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not function_names & {
        "accept",
        "authorize",
        "deserialize",
        "dispatch",
        "execute",
        "from_json",
        "ingest",
        "launch",
        "persist",
        "reconcile",
        "retrieve",
        "serialize",
        "store",
        "submit",
        "to_json",
        "verify_authority",
    }
    assert not any(isinstance(node, (ast.With, ast.AsyncWith)) for node in ast.walk(tree))
    assert "c2a_contract_support" not in SOURCE_PATH.read_text(encoding="utf-8")


def test_no_production_module_imports_test_support() -> None:
    for path in (ROOT / "src").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "c2a_contract_support" not in source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name == "tests" or alias.name.startswith("tests.") for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "tests"
                assert not (node.module or "").startswith("tests.")


def test_package_root_pyproject_schema_and_migration_bytes_remain_exact() -> None:
    assert _sha256(ROOT / "src/ge_nwp_coordinator/__init__.py") == (
        "60230ae31032071ab52b16c3537a1b2b398e06a4b1f4ec926485471927b2f2b5"
    )
    assert _sha256(ROOT / "pyproject.toml") == (
        "c59ff8c0005b063636ff161002f1b1c45a81227b4ed30a988412f01a474e0ac9"
    )
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == []
    assert "scripts" not in project["project"]
    assert "entry-points" not in project["project"]

    schema_paths = tuple(
        sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "schemas").rglob("*.*"))
    )
    migration_paths = tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "src/ge_nwp_coordinator/sqlite_migrations").rglob("*.sql")
        )
    )
    assert schema_paths == ("schemas/sqlite/coordinator-state-v1.sql",)
    assert migration_paths == (
        "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql",
        "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql",
        "src/ge_nwp_coordinator/sqlite_migrations/0003_cognitive_proposal_and_selection_state.sql",
        "src/ge_nwp_coordinator/sqlite_migrations/0004_rw0_c1_durable_evidence.sql",
    )
    assert _sha256(ROOT / schema_paths[0]) == (
        "e51902dd7e151f32a82b32cef7bbe535489f1558ce78fed63e0207df828f9e73"
    )
    assert _sha256(ROOT / migration_paths[0]) == (
        "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
    )
