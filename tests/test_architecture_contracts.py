from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_docs_are_source_of_truth_and_pin_p1_scope() -> None:
    agents = _text("AGENTS.md")
    contract = _text(".docs/a2-p1-contract.md")
    assert "If `.docs/` exists, always treat `.docs/` as the source of truth." in agents
    for phrase in (
        "no production durable store",
        "cannot self-authorize",
        "Reports are projections only",
        "does not implement worker execution",
        "state-store protocol only",
    ):
        assert phrase in agents or phrase in contract


def test_repository_name_independence_is_documented() -> None:
    naming = _text(".docs/repository-naming.md")
    architecture = _text(".docs/architecture.md")
    assert "Current repository name: Governed Execution Coordinator." in architecture
    assert "schema, authority, or durable identifiers" in architecture
    assert "Schema ids and durable identities must remain independent of repo display" in naming


def test_schema_ids_do_not_embed_repository_display_name() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    assert "governed-execution.nwp-standing-lease.v1" in source
    assert "governed-execution.nwp-work-item-state.v1" in source
    assert "Governed Execution Coordinator" not in source


def test_docs_pin_authority_boundaries() -> None:
    text = _text(".docs/authority-boundaries.md")
    for phrase in (
        "Bridge remains worker/evidence adapter only",
        "Control Plane remains product workflow authority",
        "Execution Substrate remains product admission/runtime authority",
        "Maintenance Agent remains maintenance authority",
        "Infrastructure Manager remains readiness, provenance, profile, diagnostics",
        "does not create durable A2 state",
    ):
        assert phrase in text


def test_docs_pin_closed_schemas_fixed_p1_gates_and_typed_projections() -> None:
    contract = _text(".docs/a2-p1-contract.md")
    durable = _text(".docs/durable-state-model.md")
    architecture = _text(".docs/architecture.md")
    lease = _text(".docs/lease-identity-and-authorization.md")
    assert "Unknown fields, misspelled" in lease
    assert "before canonicalization and before digest comparison" in lease
    assert "P1 exposes no production API" in contract
    assert "stage_not_enabled" in durable
    assert "Report projections are closed typed models" in architecture
    assert "test-only fixture policy" not in contract
