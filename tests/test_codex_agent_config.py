from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_repo_scoped_auditor_uses_portable_role_definition_keys() -> None:
    path = ROOT / ".codex" / "agents" / "nwp-coordinator-boundary-auditor.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert set(data) == {"name", "description", "developer_instructions"}
    assert data["name"] == "nwp-coordinator-boundary-auditor"
    assert "Read-only" in data["description"]


def test_repo_scoped_auditor_is_read_only_and_non_enabling() -> None:
    text = (ROOT / ".codex" / "agents" / "nwp-coordinator-boundary-auditor.toml").read_text(
        encoding="utf-8"
    )
    assert "Operate read-only" in text
    forbidden = (
        "endpoint =",
        "base_url",
        "provider =",
        "provider_",
        "auth =",
        "auth_",
        "token" + " =",
        "credential" + " =",
        "hook =",
        "telemetry",
        "/" + "Users" + "/",
    )
    lowered = text.lower()
    for token in forbidden:
        assert token.lower() not in lowered
