from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_standard_library_only_runtime_dependencies() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    assert pyproject["project"]["dependencies"] == []
    assert "scripts" not in pyproject.get("project", {})


def test_no_prohibited_runtime_imports_or_execution_surfaces() -> None:
    source_files = list((ROOT / "src").rglob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    forbidden = (
        "import subprocess",
        "from subprocess",
        "import socket",
        "import requests",
        "import urllib",
        "import http.client",
        "import shelve",
        "import multiprocessing",
        "import threading",
        "asyncio",
        "GitPython",
        "git push",
        "git commit",
        "git worktree",
        "create_pull",
    )
    for token in forbidden:
        assert token not in source

    sqlite_importers = {
        path.relative_to(ROOT).as_posix()
        for path in source_files
        if "import sqlite3" in path.read_text(encoding="utf-8")
    }
    assert sqlite_importers == {
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/sqlite_migration.py",
    }


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


def test_b1_sqlite_modules_do_not_define_state_store_mutations_or_writer_acquisition() -> None:
    sqlite_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src" / "ge_nwp_coordinator").glob("sqlite_*.py")
    )
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
        assert token not in sqlite_sources


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
