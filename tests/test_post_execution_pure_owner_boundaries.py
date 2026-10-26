"""Import, authority, runtime, schema, and documentation non-widening guards."""

import ast
from pathlib import Path

import pytest

from test_post_execution_pure_owner_values import CLASS_BY_V, _TEST_RECORDS, _sample


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ge_nwp_coordinator"
MODULE_PATHS = ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
 'src/ge_nwp_coordinator/_post_execution_policy_values.py',
 'src/ge_nwp_coordinator/_finite_backlog_risk_source_adapter.py',
 'src/ge_nwp_coordinator/_section41_post_execution_proposal_family_projection.py',
 'src/ge_nwp_coordinator/_section41_post_execution_role_resolution.py',
 'src/ge_nwp_coordinator/_rw0_c_decision_input_values.py')
ALLOCATIONS = {'src/ge_nwp_coordinator/_post_execution_evidence_values.py': ('V01',
                                                               'V02',
                                                               'V03',
                                                               'V04',
                                                               'V05',
                                                               'V06',
                                                               'V07',
                                                               'V08',
                                                               'V09',
                                                               'V10',
                                                               'V11',
                                                               'V12',
                                                               'V13',
                                                               'V14',
                                                               'V15',
                                                               'V20',
                                                               'V21',
                                                               'V38',
                                                               'V39',
                                                               'V40',
                                                               'V40.n01'),
 'src/ge_nwp_coordinator/_post_execution_policy_values.py': ('V16',
                                                             'V17',
                                                             'V18',
                                                             'V41',
                                                             'V41.n01',
                                                             'V42',
                                                             'V42.n01',
                                                             'V43',
                                                             'V44'),
 'src/ge_nwp_coordinator/_finite_backlog_risk_source_adapter.py': ('V19',),
 'src/ge_nwp_coordinator/_section41_post_execution_proposal_family_projection.py': ('V22', 'V23'),
 'src/ge_nwp_coordinator/_section41_post_execution_role_resolution.py': ('V24',),
 'src/ge_nwp_coordinator/_rw0_c_decision_input_values.py': ('V25',
                                                            'V26',
                                                            'V27',
                                                            'V28',
                                                            'V29',
                                                            'V30',
                                                            'V31',
                                                            'V32',
                                                            'V33',
                                                            'V34')}
ALLOWED_EDGES = (('src/ge_nwp_coordinator/_finite_backlog_risk_source_adapter.py',
  'src/ge_nwp_coordinator/_post_execution_policy_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_cognitive_proposal_row_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_cognitive_proposal_semantic_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_development_author_effect_establishment_contracts.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_rw0_c1_mutation_contracts.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_rw0_c1_semantic_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_rw0_phase_entry_semantic_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py',
  'src/ge_nwp_coordinator/_worker_execution_semantic_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_evidence_values.py', 'src/ge_nwp_coordinator/global_stop.py'),
 ('src/ge_nwp_coordinator/_post_execution_policy_values.py',
  'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 ('src/ge_nwp_coordinator/_rw0_c_decision_input_values.py',
  'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 ('src/ge_nwp_coordinator/_rw0_c_decision_input_values.py',
  'src/ge_nwp_coordinator/_post_execution_policy_values.py'),
 ('src/ge_nwp_coordinator/_rw0_c_decision_input_values.py',
  'src/ge_nwp_coordinator/_section41_post_execution_proposal_family_projection.py'),
 ('src/ge_nwp_coordinator/_rw0_c_decision_input_values.py',
  'src/ge_nwp_coordinator/_section41_post_execution_role_resolution.py'),
 ('src/ge_nwp_coordinator/_section41_post_execution_proposal_family_projection.py',
  'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 ('src/ge_nwp_coordinator/_section41_post_execution_role_resolution.py',
  'src/ge_nwp_coordinator/_section41_post_execution_proposal_family_projection.py'))
FORBIDDEN_EDGES = (('src/ge_nwp_coordinator/__init__.py', 'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 ('src/ge_nwp_coordinator/_post_execution_policy_values.py',
  'src/ge_nwp_coordinator/_finite_backlog_risk_source_adapter.py'),
 ('src/ge_nwp_coordinator/_sqlite_rw0_c1.py', 'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 ('src/ge_nwp_coordinator/_sqlite_rw0_c1.py', 'src/ge_nwp_coordinator/_post_execution_policy_values.py'),
 ('src/ge_nwp_coordinator/_sqlite_rw0_c1.py', 'src/ge_nwp_coordinator/_rw0_c_decision_input_values.py'),
 ('src/ge_nwp_coordinator/_worker_execution_semantic_values.py',
  'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 ('src/ge_nwp_coordinator/_worker_execution_semantic_values.py',
  'src/ge_nwp_coordinator/_post_execution_policy_values.py'),
 ('src/ge_nwp_coordinator/_worker_execution_semantic_values.py',
  'src/ge_nwp_coordinator/_rw0_c_decision_input_values.py'),
 (None, 'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 (None, 'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 (None, 'src/ge_nwp_coordinator/_post_execution_policy_values.py'),
 (None, 'src/ge_nwp_coordinator/_rw0_c_decision_input_values.py'),
 (None, 'src/ge_nwp_coordinator/_post_execution_evidence_values.py'),
 (None, 'src/ge_nwp_coordinator/_post_execution_policy_values.py'),
 (None, 'src/ge_nwp_coordinator/_rw0_c_decision_input_values.py'))
DOC_PATHS = ('.docs/autonomous-software-development-operating-model.md',
 '.docs/c2b-durable-development-state.md',
 '.docs/rw0-b1-pure-phase-values.md',
 '.docs/rw0-remote-worker-contact-phase-entry.md',
 '.docs/architecture.md',
 '.docs/c2a1-pure-semantic-values.md',
 '.docs/rw0-c1-durable-evidence.md')
CURRENT_D2_CONSUMERS = {
    "_post_execution_evidence_values.py": frozenset({
        "src/ge_nwp_coordinator/_rw0_d2a_evidence.py",
        "src/ge_nwp_coordinator/_rw0_d2a_handback.py",
        "src/ge_nwp_coordinator/_rw0_d2b_model_input.py",
        "src/ge_nwp_coordinator/_rw0_d2b_proposal.py",
        "src/ge_nwp_coordinator/_rw0_d2_handback.py",
        "src/ge_nwp_coordinator/_rw0_d2_post_execution_continuation.py",
        "src/ge_nwp_coordinator/_section41_post_execution_proposal_mutation_contracts.py",
        "src/ge_nwp_coordinator/_section41_post_execution_proposal_row_values.py",
        "src/ge_nwp_coordinator/_sqlite_section41_post_execution_proposal.py",
        "src/ge_nwp_coordinator/_rw0_c2_progression_contracts.py",
        "src/ge_nwp_coordinator/_sqlite_rw0_c2_progression.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
    }),
    "_post_execution_policy_values.py": frozenset({
        "src/ge_nwp_coordinator/_rw0_d2a_evidence.py",
        "src/ge_nwp_coordinator/_rw0_d2a_handback.py",
        "src/ge_nwp_coordinator/_rw0_c2_progression_contracts.py",
    }),
    "_finite_backlog_risk_source_adapter.py": frozenset({
        "src/ge_nwp_coordinator/_rw0_d2a_evidence.py",
        "src/ge_nwp_coordinator/_rw0_d2a_handback.py",
    }),
    "_section41_post_execution_proposal_family_projection.py": frozenset({
        "src/ge_nwp_coordinator/_rw0_d2_post_execution_continuation.py",
        "src/ge_nwp_coordinator/_rw0_c2_progression_contracts.py",
    }),
    "_section41_post_execution_role_resolution.py": frozenset(),
    "_rw0_c_decision_input_values.py": frozenset({
        "src/ge_nwp_coordinator/_rw0_c2_progression_contracts.py",
    }),
}
CURRENT_D2_SOURCE_FILES = frozenset({
    "_rw0_d2a_evidence.py", "_rw0_d2a_fake_reviewer.py",
    "_rw0_d2a_fake_validator.py", "_rw0_d2a_handback.py",
    "_rw0_d2a_offline.py", "_rw0_d2a_process_frames.py",
    "_rw0_d2a_workspace.py", "_rw0_d2b_model_input.py",
    "_rw0_d2b_model_frames.py", "_rw0_d2b_fake_review_model.py",
    "_rw0_d2b_proposal.py", "_rw0_d2_handback.py", "_rw0_d2_offline.py",
})


def _relative_import_targets(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    targets = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            targets.add(f"src/ge_nwp_coordinator/{node.module}.py")
        elif isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is None:
            targets.update(f"src/ge_nwp_coordinator/{alias.name}.py" for alias in node.names)
    return targets


def test_exact_six_module_allocation_and_private_surface() -> None:
    assert len(MODULE_PATHS) == 6
    assert sum(map(len, ALLOCATIONS.values())) == 44
    assert set(ALLOCATIONS) == set(MODULE_PATHS)
    package = (SOURCE / "__init__.py").read_text()
    for path in MODULE_PATHS:
        module = Path(path).stem
        assert f"{module} import" not in package
        assert f"import {module}" not in package


def test_exact_allowed_import_dag_and_all_forbidden_edges() -> None:
    observed = {
        (source, target)
        for source in MODULE_PATHS
        for target in _relative_import_targets(ROOT / source)
    }
    assert observed == set(ALLOWED_EDGES)
    for source, target in FORBIDDEN_EDGES:
        if source is None:
            continue
        path = ROOT / source
        if path.exists():
            assert target not in _relative_import_targets(path)


def test_no_io_sqlite_runtime_or_external_effect_imports() -> None:
    forbidden = {"sqlite3", "os", "pathlib", "subprocess", "socket", "urllib", "requests", "httpx", "asyncio"}
    for relative in MODULE_PATHS:
        tree = ast.parse((ROOT / relative).read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
        assert forbidden.isdisjoint(imported), relative
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        assert {"open", "exec", "eval", "compile"}.isdisjoint(calls), relative


def test_section41_0005_is_exact_with_separate_p0_and_p1_c2_suffixes() -> None:
    migrations = sorted(path.name for path in (SOURCE / "sqlite_migrations").glob("*.sql"))
    assert migrations == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
        "0004_rw0_c1_durable_evidence.sql",
        "0005_section41_post_execution_proposal_family.sql",
        "0006_rw0_c2_scope_admission.sql",
        "0007_rw0_c2_progression_decision.sql",
    ]
    assert not (SOURCE / "sqlite_state.py").exists()


def test_reserved_values_and_production_callers_remain_absent() -> None:
    assert set(CURRENT_D2_CONSUMERS) == {Path(path).name for path in MODULE_PATHS}
    for module, consumers in CURRENT_D2_CONSUMERS.items():
        assert frozenset(_production_importers(module)) == consumers
    combined = "\n".join((ROOT / path).read_text() for path in MODULE_PATHS)
    for reserved in ("V35", "V36", "V37", "V45"):
        assert reserved not in combined


def test_seven_docs_state_private_pure_status_and_all_nonclaims() -> None:
    required = (
        "no production caller", "no runtime", "no durable post-execution decision",
        "no migration", "no public export", "no external authority", "no C2B progression",
        "RW0-D/E", "Execution Substrate",
    )
    combined = "\n".join((ROOT / path).read_text() for path in DOC_PATHS)
    for phrase in required:
        assert phrase.lower() in combined.lower()


ALLOCATION_RECORD_IDS = tuple(
    record_id for record_id in _TEST_RECORDS
    if record_id.startswith("module-allocation.")
)
IMPORT_EDGE_RECORD_IDS = tuple(
    record_id for record_id in _TEST_RECORDS
    if record_id.startswith("import-edge.")
)
SEAM_RECORD_IDS = tuple(
    record_id for record_id in _TEST_RECORDS
    if record_id.startswith("remaining-seam.")
)


def _production_importers(module_filename: str) -> tuple[str, ...]:
    importers = []
    proposed = {Path(path).resolve() for path in (ROOT / item for item in MODULE_PATHS)}
    for path in SOURCE.rglob("*.py"):
        if path.resolve() in proposed:
            continue
        if f".{Path(module_filename).stem}" in path.read_text():
            importers.append(path.relative_to(ROOT).as_posix())
    return tuple(importers)


@pytest.mark.parametrize("record_id", ALLOCATION_RECORD_IDS)
def test_each_of_44_module_allocations_executes_private_owner_boundary(record_id: str) -> None:
    record = _TEST_RECORDS[record_id]
    v_number = record["v_number"]
    module_filename = record["owner_module"]
    owner_path = SOURCE / module_filename
    value_type = CLASS_BY_V[v_number]

    assert len(ALLOCATION_RECORD_IDS) == 44
    assert record_id == f"module-allocation.{v_number}"
    assert owner_path.is_file()
    assert value_type.__name__ == record["value_name"]
    assert value_type.__module__ == f"ge_nwp_coordinator.{owner_path.stem}"
    assert record["owner_status"] in {"private_proposed_owner", "nested_parent_bound"}
    assert record["package_root_export"] is False
    assert record["current_production_caller"] is False

    package_tree = ast.parse((SOURCE / "__init__.py").read_text())
    exported_names = {
        alias.name
        for node in ast.walk(package_tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert value_type.__name__ not in exported_names
    assert owner_path.stem not in exported_names
    assert frozenset(_production_importers(module_filename)) == CURRENT_D2_CONSUMERS[module_filename]


@pytest.mark.parametrize("record_id", IMPORT_EDGE_RECORD_IDS)
def test_each_of_31_import_edges_executes_its_exact_boundary(record_id: str) -> None:
    record = _TEST_RECORDS[record_id]
    source_name = record["source"]
    target_name = record["target"]
    assert len(IMPORT_EDGE_RECORD_IDS) == 31

    if source_name == "current_production_runtime":
        assert record["allowed"] is False
        assert frozenset(_production_importers(target_name)) == CURRENT_D2_CONSUMERS[target_name]
        return

    source_path = SOURCE / source_name
    if not source_path.exists():
        assert source_name in {"sqlite_bootstrap.py", "sqlite_state.py"}
        assert record["allowed"] is False
        return

    target = f"src/ge_nwp_coordinator/{target_name}"
    observed = target in _relative_import_targets(source_path)
    assert observed is record["allowed"], record_id


@pytest.mark.parametrize("record_id", SEAM_RECORD_IDS)
def test_each_of_8_remaining_seams_is_concretely_absent_and_non_authorizing(record_id: str) -> None:
    record = _TEST_RECORDS[record_id]
    seam_id = record["seam_id"]
    combined = "\n".join((ROOT / path).read_text() for path in MODULE_PATHS)
    package = (SOURCE / "__init__.py").read_text()
    assert len(SEAM_RECORD_IDS) == 8
    assert record_id == f"remaining-seam.{seam_id}"

    if seam_id == "S001":
        assert not (SOURCE / "sqlite_migrations/0005_post_execution.sql").exists()
        assert all(name not in CLASS_BY_V for name in ("V35", "V36", "V37"))
        assert all(name not in combined for name in ("V35", "V36", "V37"))
    elif seam_id == "S002":
        assert record["insufficiency_rule"] == "opaque_aggregate_digests_alone_are_insufficient"
        assert set(record["not_frozen"]) == {"schema", "ref", "digest", "module", "physical_table"}
        assert all(name not in CLASS_BY_V for name in ("V35", "V36", "V37"))
        assert "RW0CDecisionReceipt" not in combined
        assert "RW0CDecisionCommand" not in combined
    elif seam_id == "S003":
        for path in MODULE_PATHS:
            tree = ast.parse((ROOT / path).read_text())
            assert not any(
                isinstance(node, ast.Attribute) and node.attr in {"execute", "executemany", "commit"}
                for node in ast.walk(tree)
            )
        assert _production_importers("_rw0_c_decision_input_values.py") == (
            "src/ge_nwp_coordinator/_rw0_c2_progression_contracts.py",
        )
    elif seam_id == "S004":
        assert all(name not in CLASS_BY_V for name in ("V35", "V36", "V37"))
        assert "RW0CTerminal" not in combined
        assert {path.name for path in SOURCE.glob("_rw0_d1_*.py")} == {
            "_rw0_d1_process_frames.py", "_rw0_d1_process_supervisor.py",
            "_rw0_d1_fake_planner.py", "_rw0_d1_fake_worker.py",
            "_rw0_d1_workspace.py", "_rw0_d1_capsule.py",
            "_rw0_d1_pre_execution.py", "_rw0_d1_handback.py",
            "_rw0_d1_offline.py",
        }
        assert {path.name for path in SOURCE.glob("_rw0_d2*.py")} == (
            CURRENT_D2_SOURCE_FILES | {"_rw0_d2_post_execution_continuation.py"}
        )
        assert not tuple(SOURCE.glob("_rw0_e*.py"))
        assert "_rw0_d1_" not in combined
        assert "_rw0_d1_" not in (SOURCE / "__init__.py").read_text()
    elif seam_id == "S005":
        tree = ast.parse(combined)
        imported = {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
        }
        assert {"socket", "urllib", "requests", "httpx", "execution_substrate"}.isdisjoint(imported)
    elif seam_id == "S006":
        mapping = CLASS_BY_V["V40"].from_mapping(_sample("V40")).to_mapping()
        unsupported = {
            "identity_authenticated", "person_ref", "provider_ref", "account_ref",
            "credential_ref", "principal_ref", "source_authenticity",
        }
        assert unsupported.isdisjoint(mapping)
    elif seam_id == "S007":
        profile = CLASS_BY_V["V43"].from_mapping(_sample("V43"))
        assert profile.external_authority_claim is False
        for v_number in ("V41", "V42", "V43", "V44"):
            mapping = CLASS_BY_V[v_number].from_mapping(_sample(v_number)).to_mapping()
            assert "permission" not in mapping and "execution_authority" not in mapping
    else:
        assert seam_id == "S008"
        forbidden_artifacts = (
            "Canonical_Audit_Package", "Independent_Audit_Report",
            "Implementation_Report", "Boundary_Freeze",
        )
        assert all(name not in combined for name in forbidden_artifacts)
        assert all(
            frozenset(_production_importers(Path(path).name))
            == CURRENT_D2_CONSUMERS[Path(path).name]
            for path in MODULE_PATHS
        )
