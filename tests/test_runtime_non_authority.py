"""Finite C1/C2A1/C2B2 source and runtime non-authority evidence boundaries.
C2A1 adds one internal pure semantic-value module without changing schema,
migration, packaging, package-root bindings, or executable entry surfaces.
Future runtime behavior still requires a separately accepted source contract,
path scope, validation, provenance, and independent audit. Independent review,
not a generic static-effect analyzer in this module, evaluates source semantics
outside these finite contracts.
"""

import ast
import os
from pathlib import Path
import shutil
import stat
import symtable

import pytest
import tomllib

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PRODUCTION_PATHS = frozenset(
    {
        "schemas/sqlite/coordinator-state-v1.sql",
        "src/ge_nwp_coordinator/__init__.py",
        "src/ge_nwp_coordinator/_development_decision_row_values.py",
        "src/ge_nwp_coordinator/_development_effect_row_values.py",
        "src/ge_nwp_coordinator/_development_program_row_values.py",
        "src/ge_nwp_coordinator/_development_row_value_support.py",
        "src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py",
        "src/ge_nwp_coordinator/_sqlite_development_readers.py",
        "src/ge_nwp_coordinator/_worker_execution_semantic_values.py",
        "src/ge_nwp_coordinator/backlog.py",
        "src/ge_nwp_coordinator/canonicalization.py",
        "src/ge_nwp_coordinator/global_stop.py",
        "src/ge_nwp_coordinator/lease.py",
        "src/ge_nwp_coordinator/models.py",
        "src/ge_nwp_coordinator/persistence_contracts.py",
        "src/ge_nwp_coordinator/reports.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/sqlite_errors.py",
        "src/ge_nwp_coordinator/sqlite_global_stop_event_contracts.py",
        "src/ge_nwp_coordinator/sqlite_global_stop_preflight_contracts.py",
        "src/ge_nwp_coordinator/sqlite_global_stop_readers.py",
        "src/ge_nwp_coordinator/sqlite_global_stop_write_contracts.py",
        "src/ge_nwp_coordinator/sqlite_location.py",
        "src/ge_nwp_coordinator/sqlite_migration.py",
        "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql",
        "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql",
        "src/ge_nwp_coordinator/sqlite_migrations/__init__.py",
        "src/ge_nwp_coordinator/sqlite_mutation_transaction_contracts.py",
        "src/ge_nwp_coordinator/sqlite_security.py",
        "src/ge_nwp_coordinator/sqlite_transition_dry_run_contracts.py",
        "src/ge_nwp_coordinator/sqlite_transition_event_contracts.py",
        "src/ge_nwp_coordinator/sqlite_transition_event_readers.py",
        "src/ge_nwp_coordinator/sqlite_transition_read_scope.py",
        "src/ge_nwp_coordinator/sqlite_transition_select_support.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_transition_write_contracts.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
        "src/ge_nwp_coordinator/sqlite_writer_state.py",
        "src/ge_nwp_coordinator/state_authority_lock.py",
        "src/ge_nwp_coordinator/state_machine.py",
        "src/ge_nwp_coordinator/state_store.py",
    }
)

EXPECTED_PUBLIC_BINDINGS = {
    "AuthorizationDecision": ("ge_nwp_coordinator.lease", "AuthorizationDecision"),
    "CommittedGlobalStopUpdate": ("ge_nwp_coordinator.state_store", "CommittedGlobalStopUpdate"),
    "CommittedTransition": ("ge_nwp_coordinator.state_store", "CommittedTransition"),
    "DependencyDecision": ("ge_nwp_coordinator.state_machine", "DependencyDecision"),
    "FiniteBacklog": ("ge_nwp_coordinator.backlog", "FiniteBacklog"),
    "GlobalStopApplyPreflightError": ("ge_nwp_coordinator.state_store", "GlobalStopApplyPreflightError"),
    "GlobalStopApplyPreflightFailureReason": ("ge_nwp_coordinator.state_store", "GlobalStopApplyPreflightFailureReason"),
    "GlobalStopConflict": ("ge_nwp_coordinator.state_store", "GlobalStopConflict"),
    "LEASE_SCHEMA_ID": ("ge_nwp_coordinator.lease", "LEASE_SCHEMA_ID"),
    "LeaseIdentityValidation": ("ge_nwp_coordinator.lease", "LeaseIdentityValidation"),
    "LeaseRuntimeDecision": ("ge_nwp_coordinator.lease", "LeaseRuntimeDecision"),
    "LeaseRuntimeStatus": ("ge_nwp_coordinator.lease", "LeaseRuntimeStatus"),
    "SafeWriterMetadata": ("ge_nwp_coordinator.state_store", "SafeWriterMetadata"),
    "StateStore": ("ge_nwp_coordinator.state_store", "StateStore"),
    "StandingLease": ("ge_nwp_coordinator.lease", "StandingLease"),
    "TransitionApplyPreflightError": ("ge_nwp_coordinator.state_store", "TransitionApplyPreflightError"),
    "TransitionApplyPreflightFailureReason": ("ge_nwp_coordinator.state_store", "TransitionApplyPreflightFailureReason"),
    "TransitionCommand": ("ge_nwp_coordinator.state_machine", "TransitionCommand"),
    "TransitionContext": ("ge_nwp_coordinator.state_machine", "TransitionContext"),
    "TransitionConflict": ("ge_nwp_coordinator.state_store", "TransitionConflict"),
    "TransitionEvaluation": ("ge_nwp_coordinator.state_machine", "TransitionEvaluation"),
    "TransitionEvent": ("ge_nwp_coordinator.state_machine", "TransitionEvent"),
    "TransitionEventOutcome": ("ge_nwp_coordinator.state_machine", "TransitionEventOutcome"),
    "UnsupportedAuthorizationProvider": ("ge_nwp_coordinator.lease", "UnsupportedAuthorizationProvider"),
    "WriterSession": ("ge_nwp_coordinator.state_store", "WriterSession"),
    "WriterSessionError": ("ge_nwp_coordinator.state_store", "WriterSessionError"),
    "WriterSessionFailureReason": ("ge_nwp_coordinator.state_store", "WriterSessionFailureReason"),
    "WorkItem": ("ge_nwp_coordinator.backlog", "WorkItem"),
    "WorkItemRecord": ("ge_nwp_coordinator.state_machine", "WorkItemRecord"),
    "WorkItemState": ("ge_nwp_coordinator.state_machine", "WorkItemState"),
    "derive_lease_runtime_decision": ("ge_nwp_coordinator.lease", "derive_lease_runtime_decision"),
    "evaluate_transition": ("ge_nwp_coordinator.state_machine", "evaluate_transition"),
    "transition": ("ge_nwp_coordinator.state_machine", "transition"),
    "validate_standing_lease": ("ge_nwp_coordinator.lease", "validate_standing_lease"),
}
EXPECTED_PUBLIC_EXPORTS = frozenset(EXPECTED_PUBLIC_BINDINGS)
EXPECTED_PACKAGE_DATA = {
    "ge_nwp_coordinator.sqlite_migrations": ["*.sql"],
}
NON_PRODUCTION_SOURCE_ROOTS = frozenset({".codex", ".docs", "tests"})
ALL_MUTATING_METHODS = frozenset(
    {"append", "clear", "extend", "insert", "pop", "remove", "reverse", "sort"}
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _assert_real_directory(path: Path) -> None:
    mode = path.lstat().st_mode
    assert stat.S_ISDIR(mode), path
    assert not stat.S_ISLNK(mode), path


def _production_surface_paths(root: Path) -> frozenset[str]:
    """Discover every regular file under the closed src/ and schemas/ roots."""
    paths: set[str] = set()

    def walk(directory: Path) -> None:
        _assert_real_directory(directory)
        with os.scandir(directory) as entries:
            ordered = sorted(entries, key=lambda entry: entry.name)
        for entry in ordered:
            path = Path(entry.path)
            mode = entry.stat(follow_symlinks=False).st_mode
            assert not stat.S_ISLNK(mode), path
            if stat.S_ISDIR(mode):
                walk(path)
            elif stat.S_ISREG(mode):
                paths.add(path.relative_to(root).as_posix())
            else:
                raise AssertionError(f"non-regular production path: {path}")

    for relative_root in ("src", "schemas"):
        walk(root / relative_root)
    return frozenset(paths)


def _assert_repository_execution_surface(root: Path) -> None:
    """Reject alternate ordinary Python source and packaging roots without Git."""
    _assert_real_directory(root)
    for required_root in ("src", "schemas", "tests"):
        _assert_real_directory(root / required_root)

    project = root / "pyproject.toml"
    project_mode = project.lstat().st_mode
    assert stat.S_ISREG(project_mode) and not stat.S_ISLNK(project_mode)
    assert not (root / "setup.py").exists()
    assert not (root / "setup.cfg").exists()

    allowed_python_roots = NON_PRODUCTION_SOURCE_ROOTS | {"src"}

    def walk(directory: Path, *, candidate_alternate_tree: bool = False) -> None:
        _assert_real_directory(directory)
        with os.scandir(directory) as entries:
            ordered = sorted(entries, key=lambda entry: entry.name)
        for entry in ordered:
            path = Path(entry.path)
            relative = path.relative_to(root)
            if relative.parts[0] == ".git":
                continue
            mode = entry.stat(follow_symlinks=False).st_mode
            source_bearing_name = (
                path.suffix == ".py"
                or path.name in {"pyproject.toml", "setup.py", "setup.cfg"}
            )
            schema_bearing_name = path.suffix == ".sql"
            if stat.S_ISLNK(mode):
                assert not source_bearing_name and not schema_bearing_name, path
                if len(relative.parts) == 1 or candidate_alternate_tree:
                    raise AssertionError(
                        f"symlinked alternate root or source path: "
                        f"{relative.as_posix()}"
                    )
                continue
            if stat.S_ISDIR(mode):
                walk(
                    path,
                    candidate_alternate_tree=candidate_alternate_tree
                    or (
                        len(relative.parts) == 1
                        and relative.parts[0]
                        not in allowed_python_roots | {"schemas"}
                    ),
                )
                continue
            if not stat.S_ISREG(mode):
                assert not source_bearing_name and not schema_bearing_name, path
                continue
            if path.name in {"setup.py", "setup.cfg"}:
                raise AssertionError(f"legacy packaging surface: {relative.as_posix()}")
            if path.name == "pyproject.toml":
                assert relative.as_posix() == "pyproject.toml", path
            if path.suffix == ".py":
                assert len(relative.parts) > 1, path
                assert relative.parts[0] in allowed_python_roots, path
            if path.suffix == ".sql":
                assert len(relative.parts) > 1, path
                assert relative.parts[0] in allowed_python_roots | {"schemas"}, path

    walk(root)


def _assert_packaging_contract(source: str) -> None:
    data = tomllib.loads(source)
    project = data["project"]
    assert project["dependencies"] == []
    for field in (
        "optional-dependencies",
        "dynamic",
        "scripts",
        "gui-scripts",
        "entry-points",
    ):
        assert field not in project
    assert "dependency-groups" not in data
    assert "build-system" not in data

    setuptools = data["tool"]["setuptools"]
    assert set(setuptools) == {"package-data"}
    assert setuptools["package-data"] == EXPECTED_PACKAGE_DATA


def _target_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return {name for item in target.elts for name in _target_names(item)}
    return set()


class _ModuleNamespaceCollector(ast.NodeVisitor):
    """Collect finite module-scope bindings while excluding nested namespaces."""

    def __init__(self) -> None:
        self.events: dict[str, list[tuple[str, str]]] = {}
        self.all_alias_escapes: list[int] = []
        self.all_mutations: list[int] = []
        self.dunder_name_loads: list[int] = []

    def _record(self, name: str, event: tuple[str, str]) -> None:
        self.events.setdefault(name, []).append(event)

    def _visit_function_signature(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
    ) -> None:
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default is not None:
                self.visit(default)
        arguments = (
            tuple(node.args.posonlyargs)
            + tuple(node.args.args)
            + tuple(node.args.kwonlyargs)
        )
        for argument in arguments:
            if argument.annotation is not None:
                self.visit(argument.annotation)
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            self.visit(node.args.kwarg.annotation)

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            bound = item.asname or item.name.split(".", 1)[0]
            self._record(bound, ("<module-import>", item.name))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        for item in node.names:
            assert item.name != "*"
            self._record(item.asname or item.name, (module, item.name))

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._record(node.id, ("<assignment>", "<assignment>"))
        elif isinstance(node.ctx, ast.Load) and node.id == "__name__":
            self.dunder_name_loads.append(node.lineno)

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Name) and node.value.id == "__all__":
            self.all_alias_escapes.append(node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if (
            isinstance(node.target, ast.Name)
            and node.value is not None
            and isinstance(node.value, ast.Name)
            and node.value.id == "__all__"
        ):
            self.all_alias_escapes.append(node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "__all__"
            and node.func.attr in ALL_MUTATING_METHODS
        ):
            self.all_mutations.append(node.lineno)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if (
            isinstance(node.ctx, (ast.Store, ast.Del))
            and isinstance(node.value, ast.Name)
            and node.value.id == "__all__"
        ):
            self.all_mutations.append(node.lineno)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record(node.name, ("<definition>", node.name))
        for decorator in node.decorator_list:
            self.visit(decorator)
        self._visit_function_signature(node)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._record(node.name, ("<definition>", node.name))
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_function_signature(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name is not None:
            self._record(node.name, ("<assignment>", "<assignment>"))
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        if node.name is not None:
            self._record(node.name, ("<assignment>", "<assignment>"))
        self.generic_visit(node)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        if node.name is not None:
            self._record(node.name, ("<assignment>", "<assignment>"))

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest is not None:
            self._record(node.rest, ("<assignment>", "<assignment>"))
        for pattern in node.patterns:
            self.visit(pattern)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        for name in _target_names(node.target):
            self._record(name, ("<assignment>", "<assignment>"))
        self.visit(node.value)

    def _visit_comprehension(
        self,
        generators: list[ast.comprehension],
        values: tuple[ast.AST, ...],
    ) -> None:
        for generator in generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        for value in values:
            self.visit(value)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._visit_comprehension(node.generators, (node.elt,))

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._visit_comprehension(node.generators, (node.elt,))

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._visit_comprehension(node.generators, (node.key, node.value))

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._visit_comprehension(node.generators, (node.elt,))


def _assert_public_export_contract(source: str) -> None:
    tree = ast.parse(source, filename="src/ge_nwp_coordinator/__init__.py")
    all_assignments: list[ast.AST] = []
    direct_imports: dict[str, list[tuple[str, str]]] = {}

    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom):
            for item in statement.names:
                assert item.name != "*"
                bound = item.asname or item.name
                if not bound.startswith("_"):
                    assert statement.module is not None and statement.level == 0
                    direct_imports.setdefault(bound, []).append(
                        (statement.module, item.name)
                    )
        elif isinstance(statement, ast.Import):
            for item in statement.names:
                bound = item.asname or item.name.split(".", 1)[0]
                if not bound.startswith("_"):
                    direct_imports.setdefault(bound, []).append(
                        ("<module-import>", item.name)
                    )
        elif isinstance(statement, ast.Assign):
            names = {name for target in statement.targets for name in _target_names(target)}
            if "__all__" in names:
                all_assignments.append(statement)
        elif isinstance(statement, ast.AnnAssign):
            names = _target_names(statement.target)
            if "__all__" in names:
                all_assignments.append(statement)
        elif isinstance(statement, ast.AugAssign):
            names = _target_names(statement.target)
            if "__all__" in names:
                all_assignments.append(statement)

    assert len(all_assignments) == 1
    assignment = all_assignments[0]
    assert isinstance(assignment, ast.Assign)
    assert len(assignment.targets) == 1
    assert isinstance(assignment.targets[0], ast.Name)
    assert assignment.targets[0].id == "__all__"
    assert isinstance(assignment.value, (ast.List, ast.Tuple))
    assert all(
        isinstance(item, ast.Constant) and type(item.value) is str
        for item in assignment.value.elts
    )
    export_values = tuple(item.value for item in assignment.value.elts)
    assert len(export_values) == len(set(export_values))
    assert frozenset(export_values) == EXPECTED_PUBLIC_EXPORTS

    assert direct_imports == {
        name: [binding] for name, binding in EXPECTED_PUBLIC_BINDINGS.items()
    }

    namespace = _ModuleNamespaceCollector()
    namespace.visit(tree)
    assert namespace.events.get("__all__") == [
        ("<assignment>", "<assignment>")
    ]
    assert namespace.all_alias_escapes == []
    assert namespace.all_mutations == []

    public_events = {
        name: events
        for name, events in namespace.events.items()
        if not name.startswith("_")
    }
    assert set(public_events) == EXPECTED_PUBLIC_EXPORTS
    for public_name, expected_binding in EXPECTED_PUBLIC_BINDINGS.items():
        assert public_events[public_name] == [expected_binding]

    module_symbols = symtable.symtable(
        source,
        "src/ge_nwp_coordinator/__init__.py",
        "exec",
    )
    public_symbols = {
        name
        for name in module_symbols.get_identifiers()
        if not name.startswith("_")
        and (
            module_symbols.lookup(name).is_assigned()
            or module_symbols.lookup(name).is_imported()
            or module_symbols.lookup(name).is_namespace()
        )
    }
    assert public_symbols == EXPECTED_PUBLIC_EXPORTS


def _has_module_scope_dunder_name_load(source: str, filename: str) -> bool:
    namespace = _ModuleNamespaceCollector()
    namespace.visit(ast.parse(source, filename=filename))
    return bool(namespace.dunder_name_loads)


def _assert_package_module_contract(source: str) -> None:
    _assert_public_export_contract(source)
    assert not _has_module_scope_dunder_name_load(
        source,
        "src/ge_nwp_coordinator/__init__.py",
    )


def test_runtime_packaging_and_public_exports_are_exact() -> None:
    _assert_repository_execution_surface(ROOT)
    _assert_packaging_contract(_read("pyproject.toml"))
    _assert_package_module_contract(_read("src/ge_nwp_coordinator/__init__.py"))


def test_repository_execution_surface_rejects_alternate_source_and_packaging(
    tmp_path: Path,
) -> None:
    def copied_root(name: str) -> Path:
        root = tmp_path / name
        root.mkdir()
        for directory in (".codex", ".docs", "src", "schemas", "tests"):
            (root / directory).mkdir()
        (root / "pyproject.toml").write_text(
            _read("pyproject.toml"),
            encoding="utf-8",
        )
        _assert_repository_execution_surface(root)
        return root

    root_setup_py = copied_root("root-setup-py")
    (root_setup_py / "setup.py").write_text("pass\n", encoding="utf-8")

    root_setup_cfg = copied_root("root-setup-cfg")
    (root_setup_cfg / "setup.cfg").write_text("[metadata]\n", encoding="utf-8")

    alternate_module = copied_root("alternate-module")
    (alternate_module / "alternate_module.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    alternate_source = copied_root("alternate-source")
    (alternate_source / "alternate_src").mkdir()
    (alternate_source / "alternate_src" / "runner.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    alternate_package = copied_root("alternate-package")
    package = alternate_package / "alternate_src" / "package"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")

    alternate_schema = copied_root("alternate-schema")
    (alternate_schema / "alternate_schemas").mkdir()
    (alternate_schema / "alternate_schemas" / "schema.sql").write_text(
        "SELECT 1;\n",
        encoding="utf-8",
    )

    nested_project = copied_root("nested-project")
    (nested_project / "alternate_src").mkdir()
    (nested_project / "alternate_src" / "pyproject.toml").write_text(
        "[project]\nname = 'alternate'\n",
        encoding="utf-8",
    )

    symlinked_source = copied_root("symlinked-source")
    (symlinked_source / "source-target").mkdir()
    (symlinked_source / "source-target" / "runner.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    (symlinked_source / "alternate_src").symlink_to(
        symlinked_source / "source-target",
        target_is_directory=True,
    )

    external_runtime = tmp_path / "external-runtime-tree"
    external_runtime.mkdir()
    (external_runtime / "runner.py").write_text("VALUE = 1\n", encoding="utf-8")
    external_package = external_runtime / "package"
    external_package.mkdir()
    (external_package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    nested_symlink_source = copied_root("nested-symlink-source")
    nested_candidate = nested_symlink_source / "tool-shed" / "inner-bay"
    nested_candidate.mkdir(parents=True)
    (nested_candidate / "linked-cache").symlink_to(
        external_runtime,
        target_is_directory=True,
    )

    nonregular_source = copied_root("nonregular-source")
    (nonregular_source / "alternate_src").mkdir()
    os.mkfifo(nonregular_source / "alternate_src" / "runner.py")

    nonregular_schema = copied_root("nonregular-schema")
    (nonregular_schema / "schema-cache").mkdir()
    os.mkfifo(nonregular_schema / "schema-cache" / "schema.sql")

    for mutation in (
        root_setup_py,
        root_setup_cfg,
        alternate_module,
        alternate_source,
        alternate_package,
        alternate_schema,
        nested_project,
        symlinked_source,
        nested_symlink_source,
        nonregular_source,
        nonregular_schema,
    ):
        with pytest.raises(AssertionError):
            _assert_repository_execution_surface(mutation)


def test_packaging_contract_rejects_alternate_execution_surfaces() -> None:
    source = _read("pyproject.toml")
    setuptools_heading = "[tool.setuptools.package-data]"
    package_data = '"ge_nwp_coordinator.sqlite_migrations" = ["*.sql"]'
    mutations = {
        "optional dependency": source
        + '\n[project.optional-dependencies]\nnetwork = ["requests"]\n',
        "dependency group": source
        + '\n[dependency-groups]\ndev = ["requests"]\n',
        "script": source + '\n[project.scripts]\ncoordinator = "pkg:main"\n',
        "GUI script": source
        + '\n[project.gui-scripts]\ncoordinator = "pkg:main"\n',
        "entry point": source
        + '\n[project.entry-points."ge.test"]\ncoordinator = "pkg:main"\n',
        "second package root": source.replace(
            setuptools_heading,
            '[tool.setuptools]\npackage-dir = {"" = "src", alternate = "alternate_src"}\n\n'
            + setuptools_heading,
            1,
        ),
        "second installable package": source
        + '\n[tool.setuptools.packages.find]\nwhere = ["src"]\n'
        + 'include = ["ge_nwp_coordinator*", "alternate*"]\n',
        "top-level module": source.replace(
            setuptools_heading,
            '[tool.setuptools]\npy-modules = ["alternate_runtime"]\n\n'
            + setuptools_heading,
            1,
        ),
        "alternate package-data executable": source.replace(
            package_data,
            package_data + '\n"ge_nwp_coordinator" = ["runner.py"]',
            1,
        ),
        "alternate build backend": source
        + '\n[build-system]\nrequires = ["setuptools"]\n'
        + 'build-backend = "setuptools.build_meta"\n',
    }
    for mutation in mutations.values():
        with pytest.raises((AssertionError, tomllib.TOMLDecodeError)):
            _assert_packaging_contract(mutation)


def test_public_export_contract_rejects_binding_and_namespace_mutations() -> None:
    source = _read("src/ge_nwp_coordinator/__init__.py")
    backlog_import = "from ge_nwp_coordinator.backlog import FiniteBacklog, WorkItem"
    mutations = {
        "__all__.append": source + '\n__all__.append("AlternateRuntime")\n',
        "__all__.extend": source + '\n__all__.extend(["AlternateRuntime"])\n',
        "__all__.insert": source + '\n__all__.insert(0, "AlternateRuntime")\n',
        "live __all__ alias": source
        + "\n_exports = __all__\n_exports.append('AlternateRuntime')\n",
        "annotated live __all__ alias": source
        + "\nfrom .backlog import FiniteBacklog as _PrivateBacklog\n"
        + "_alias: list[str] = __all__\n"
        + "_alias.append('_PrivateBacklog')\n",
        "second __all__ assignment": source + "\n__all__ = list(__all__)\n",
        "augmented __all__": source + "\n__all__ += ['AlternateRuntime']\n",
        "__all__ subscript assignment": source + "\n__all__[0] = 'AlternateRuntime'\n",
        "__all__ subscript deletion": source + "\ndel __all__[0]\n",
        "duplicate export": source.replace(
            '    "AuthorizationDecision",',
            '    "AuthorizationDecision",\n    "AuthorizationDecision",',
            1,
        ),
        "extra public assignment": source + "\nAlternateRuntime = object()\n",
        "extra public import": source + "\nimport os as AlternateRuntime\n",
        "extra public function": source + "\ndef AlternateRuntime():\n    pass\n",
        "extra public class": source + "\nclass AlternateRuntime:\n    pass\n",
        "match mapping binding": source
        + "\nmatch {}:\n    case {**AlternateRuntime}:\n        pass\n",
        "comprehension walrus binding": source
        + "\n_private = [(AlternateRuntime := item) for item in ()]\n",
        "expected import under false branch": source.replace(
            backlog_import,
            "if False:\n    " + backlog_import,
            1,
        ),
        "expected import under try": source.replace(
            backlog_import,
            "try:\n    " + backlog_import + "\nexcept ImportError:\n    pass",
            1,
        ),
        "expected import under match": source.replace(
            backlog_import,
            "match 0:\n    case 0:\n        " + backlog_import,
            1,
        ),
        "wrong export origin": source.replace(
            backlog_import,
            "from os import system as FiniteBacklog\n"
            "from ge_nwp_coordinator.backlog import WorkItem",
            1,
        ),
        "wrong source symbol": source.replace(
            backlog_import,
            "from ge_nwp_coordinator.backlog import WorkItem as FiniteBacklog, WorkItem",
            1,
        ),
        "swapped export bindings": source.replace(
            backlog_import,
            "from ge_nwp_coordinator.backlog import "
            "FiniteBacklog as WorkItem, WorkItem as FiniteBacklog",
            1,
        ),
        "expected export rebound": source
        + "\nfrom os import system as _system\nFiniteBacklog = _system\n",
        "boolean-short-circuit main dispatch": source
        + '\n(__name__ == "__main__") and _run()\n',
    }
    for mutation in mutations.values():
        with pytest.raises(AssertionError):
            _assert_package_module_contract(mutation)

    accepted_additions = (
        "\ndef _function_scope():\n    __all__ = ['local']\n",
        "\nclass _ClassScope:\n    __all__ = ['local']\n",
        "\nfrom .backlog import FiniteBacklog as _PrivateBacklog\n",
        "\n_exports_copy = __all__.copy()\n",
        "\n_exports_snapshot = tuple(__all__)\n",
        "\n_snapshot: tuple[str, ...] = tuple(__all__)\n",
        '\n_TEXT = "__all__.append(\\"AlternateRuntime\\") and __name__"\n'
        "# __all__.extend(['AlternateRuntime'])\n",
    )
    for addition in accepted_additions:
        _assert_package_module_contract(source + addition)


def test_c2a1_tranche_has_exact_production_and_schema_inventories() -> None:
    assert _production_surface_paths(ROOT) == EXPECTED_PRODUCTION_PATHS


def test_production_inventory_rejects_files_symlinks_and_missing_paths(tmp_path: Path) -> None:
    def copied_surface(name: str) -> Path:
        target = tmp_path / name
        target.mkdir()
        shutil.copytree(ROOT / "src", target / "src", symlinks=True)
        shutil.copytree(ROOT / "schemas", target / "schemas", symlinks=True)
        assert _production_surface_paths(target) == EXPECTED_PRODUCTION_PATHS
        return target

    unexpected_file = copied_surface("unexpected-file")
    (unexpected_file / "src" / "ge_nwp_coordinator" / "runtime.data").write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    alternate_module = copied_surface("alternate-module")
    (alternate_module / "src" / "alternate_runtime.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    alternate_schema = copied_surface("alternate-schema")
    (alternate_schema / "schemas" / "sqlite" / "alternate.sql").write_text(
        "SELECT 1;\n",
        encoding="utf-8",
    )

    missing_file = copied_surface("missing-file")
    (missing_file / "src" / "ge_nwp_coordinator" / "backlog.py").unlink()

    symlinked_file = copied_surface("symlinked-file")
    outside_file = symlinked_file / "outside.py"
    outside_file.write_text("VALUE = 1\n", encoding="utf-8")
    linked_file = symlinked_file / "src" / "ge_nwp_coordinator" / "backlog.py"
    linked_file.unlink()
    linked_file.symlink_to(outside_file)

    symlinked_directory = copied_surface("symlinked-directory")
    linked_directory = (
        symlinked_directory / "src" / "ge_nwp_coordinator" / "sqlite_migrations"
    )
    outside_directory = symlinked_directory / "outside-migrations"
    linked_directory.rename(outside_directory)
    linked_directory.symlink_to(outside_directory, target_is_directory=True)

    for mutation in (
        unexpected_file,
        alternate_module,
        alternate_schema,
        missing_file,
        symlinked_file,
        symlinked_directory,
    ):
        with pytest.raises(AssertionError):
            assert _production_surface_paths(mutation) == EXPECTED_PRODUCTION_PATHS


def test_production_python_has_no_module_scope_dunder_name_entry_surface() -> None:
    findings: list[str] = []
    for relative_path in sorted(EXPECTED_PRODUCTION_PATHS):
        if not relative_path.endswith(".py"):
            continue
        source = _read(relative_path)
        if _has_module_scope_dunder_name_load(source, relative_path):
            findings.append(relative_path)
    assert findings == []


def test_sqlite_import_surface_is_exact() -> None:
    source_files = [ROOT / path for path in EXPECTED_PRODUCTION_PATHS if path.endswith(".py")]
    sqlite_importers = {
        path.relative_to(ROOT).as_posix()
        for path in source_files
        if "import sqlite3" in path.read_text(encoding="utf-8")
    }
    assert sqlite_importers == {
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/sqlite_migration.py",
        "src/ge_nwp_coordinator/sqlite_transition_select_support.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
    }


def test_c2b2_private_readers_have_no_public_or_production_caller_surface() -> None:
    package_source = _read("src/ge_nwp_coordinator/__init__.py")
    state_source = _read("src/ge_nwp_coordinator/state_store.py")
    writer_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    production_paths = tuple(
        ROOT / path for path in EXPECTED_PRODUCTION_PATHS if path.endswith(".py")
    )
    importers = {
        path.relative_to(ROOT).as_posix()
        for path in production_paths
        if path.name != "_sqlite_development_readers.py"
        and "_sqlite_development_readers" in path.read_text(encoding="utf-8")
    }
    assert importers == set()
    for source in (package_source, state_source, writer_source):
        assert "read_development" not in source
        assert "DevelopmentProgramHeadAndCurrentVersionRead" not in source
    assert "_sqlite_development_reader_contracts" not in package_source


def test_state_store_and_writer_session_have_protocols_only_and_no_backend() -> None:
    text = _read("src/ge_nwp_coordinator/state_store.py")
    assert "class StateStore(Protocol)" in text
    assert "class WriterSession(Protocol)" in text
    assert "def apply_transition(" in text
    assert "def apply_global_stop_update(" in text
    assert "StateWriterToken" not in text
    assert "def current_writer" not in text
    assert "sqlite" not in text.lower()
    assert "journal" not in text.lower()
    assert "open(" not in text


def test_sqlite_modules_do_not_define_state_store_mutations_or_services() -> None:
    sqlite_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src" / "ge_nwp_coordinator").glob("sqlite_*.py")
        if path.name != "sqlite_writer_session.py"
    )
    writer_session_source = _read("src/ge_nwp_coordinator/sqlite_writer_session.py")
    forbidden = (
        "class SQLiteStateStore",
        "class SqliteStateStore",
        "def apply_transition(",
        "def apply_global_stop_update(",
        "fcntl",
        "msvcrt",
        "LOCK_EX",
        "writer_token",
        "current_writer",
        "Worker",
        "CoordinatorService",
        "while True",
        "subprocess",
        "socket",
    )
    for token in forbidden:
        checked_sources = (
            sqlite_sources.replace("stale_writer_token", "") if token == "writer_token" else sqlite_sources
        )
        assert token not in checked_sources
    assert "def apply_transition(" in writer_session_source
    assert "def apply_global_stop_update(" in writer_session_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in writer_session_source
    assert "class SQLiteStateStore" not in writer_session_source
    assert "class SqliteStateStore" not in writer_session_source


def test_old_aggregate_apply_and_receipt_lookup_surface_is_absent() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    forbidden = (
        "ApplyTransitionRequest",
        "ApplyTransitionResult",
        "TransitionReceipt",
        "append_transition_receipt",
        "compare_and_set_transition",
        "read_transition_receipt",
        "lookup_idempotency",
        "idempotency_status",
        "submit_operator_authorized_global_stop_update",
    )
    for token in forbidden:
        assert token not in source


def test_codex_agent_config_allowlist_and_hygiene() -> None:
    path = ROOT / ".codex" / "agents" / "nwp-coordinator-boundary-auditor.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert set(data) == {"name", "description", "developer_instructions"}
    serialized = repr(data).lower()
    forbidden = (
        "endpoint =",
        "base_url",
        "auth =",
        "auth_",
        "token" + " =",
        "credential" + " =",
        "hook =",
        "telemetry",
        "provider =",
        "provider_",
        "/" + "users" + "/",
        "workspace_id",
        "org_id",
    )
    for token in forbidden:
        assert token not in serialized


def test_test_only_in_memory_store_lives_outside_production() -> None:
    class InMemoryStateStore:
        pass

    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    assert "InMemoryStateStore" not in source
    assert InMemoryStateStore.__module__ == __name__


def test_no_production_stage_enable_policy_or_provider() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    forbidden = (
        "P1Policy",
        "worker_execution_enabled",
        "repair_enabled",
        "local_commit_enabled",
        "publication_enabled",
        "allow_stage",
        "enable_stage",
        "os.environ",
    )
    for token in forbidden:
        assert token not in source


def test_no_arbitrary_public_payload_sanitizer_model() -> None:
    text = _read("src/ge_nwp_coordinator/reports.py")
    assert "assert_safe_report_payload" not in text
    assert "FORBIDDEN_REPORT_FRAGMENTS" not in text
    assert "payload: Any" not in text
