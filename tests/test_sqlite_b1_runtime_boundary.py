from __future__ import annotations

import ast
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _production_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))


def _production_source_except_state_store() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src").rglob("*.py")
        if path.name != "state_store.py"
    )


def test_no_sqlite_state_store_or_product_mutation_backend() -> None:
    source = _production_source_except_state_store()
    assert "class StateStore(Protocol)" in (ROOT / "src/ge_nwp_coordinator/state_store.py").read_text(encoding="utf-8")
    forbidden = (
        "class SQLiteStateStore",
        "class SqliteStateStore",
        "implements StateStore",
        "def read_current(self",
        "def apply_transition(self",
        "def read_global_stop(self",
        "def apply_global_stop_update(self",
    )
    for token in forbidden:
        assert token not in source


def test_no_writer_acquisition_worker_scheduler_or_service_surface() -> None:
    source = _production_source()
    source_without_lock = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src").rglob("*.py")
        if path.name != "state_authority_lock.py"
    )
    lock_source = (ROOT / "src/ge_nwp_coordinator/state_authority_lock.py").read_text(encoding="utf-8")
    forbidden = (
        "msvcrt",
        "acquire_writer",
        "writer_lock",
        "CoordinatorService",
        "Scheduler",
        "QueueConsumer",
        "while True",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "argparse",
        "click",
    )
    for token in forbidden:
        assert token not in source
    for token in ("fcntl", "LOCK_EX", "LOCK_NB"):
        assert token not in source_without_lock
        assert token in lock_source


def test_no_cli_mcp_bridge_codex_or_network_execution_surface() -> None:
    source = _production_source().lower()
    forbidden = (
        "bridge a1",
        "invoke_bridge",
        "invoke_codex",
        "codex worker",
        "mcp",
        "entry_points",
        "scripts",
        "http.client",
    )
    for token in forbidden:
        assert token not in source


def test_migration_resources_are_declared_as_package_data() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]
    assert package_data["ge_nwp_coordinator.sqlite_migrations"] == ["*.sql"]


def test_create_capable_sqlite_helpers_are_internal_and_initialize_only() -> None:
    package_root = (ROOT / "src/ge_nwp_coordinator/__init__.py").read_text(encoding="utf-8")
    connection_source = (ROOT / "src/ge_nwp_coordinator/sqlite_connection.py").read_text(encoding="utf-8")
    migration_source = (ROOT / "src/ge_nwp_coordinator/sqlite_migration.py").read_text(encoding="utf-8")

    assert "open_sqlite_connection" not in package_root
    assert "database_path_for_connection" not in package_root
    assert "def open_sqlite_connection" not in connection_source
    assert "def database_path_for_connection" not in connection_source
    assert "def _open_sqlite_connection" in connection_source
    assert "_open_sqlite_connection(location)" in migration_source

    call_sites: list[tuple[str, str]] = []
    for path in (ROOT / "src/ge_nwp_coordinator").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name == "_open_sqlite_connection":
                call_sites.append((path.relative_to(ROOT).as_posix(), name))

    assert call_sites == [("src/ge_nwp_coordinator/sqlite_migration.py", "_open_sqlite_connection")]
