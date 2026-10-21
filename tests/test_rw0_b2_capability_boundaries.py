from __future__ import annotations

import ast
import hashlib
import importlib.util
import stat
import sys
import types
from pathlib import Path

import pytest

import ge_nwp_coordinator._rw0_worker_mechanism_capability_values as capability
from ge_nwp_coordinator._rw0_worker_mechanism_capability_values import (
    RW0WorkerMechanismCapabilityDeclarationV1,
    RW0WorkerMechanismCapabilityError,
    RW0WorkerMechanismCapabilityObservationV1,
    RW0WorkerMechanismCapabilityQualificationV1,
    validate_worker_mechanism_capability_qualification,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ge_nwp_coordinator/_rw0_worker_mechanism_capability_values.py"
PACKAGE = ROOT / "src/ge_nwp_coordinator"
OWNER = ROOT / ".docs/rw0-b2-capability.md"
OWNER_BEGIN = "<!-- RW0_B2_CAPABILITY_OWNER_BEGIN -->"
OWNER_END = "<!-- RW0_B2_CAPABILITY_OWNER_END -->"
STATUS_BEGIN = "<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_BEGIN -->"
STATUS_END = "<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_END -->"
STATUS_PATHS = (
    ROOT / ".docs/rw0-remote-worker-contact-phase-entry.md",
    ROOT / ".docs/authority-boundaries.md",
    ROOT / ".docs/autonomous-software-development-operating-model.md",
    ROOT / ".docs/durable-state-model.md",
    ROOT / ".docs/worker-execution-boundary.md",
)
EXPECTED_STATUS = """RW0-B2-Capability implements private, pure, no-I/O worker-mechanism capability
declaration, independently authored supplied observation, and Coordinator
qualification values plus one pure qualification relation. It binds the fixed
RW0-B2-Wire profile `rw0-wire-nwpf-v1` with digest
`470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454`
and consumes one private B1 host-validation snapshot seam after B1 reconstructs
the complete applicable B1, C2A, and lineage graph through protected owners.
It authenticates no source, proves no physical process
behavior, grants no permission or semantic acceptance, persists no fact,
contacts no worker/provider/host, and selects no CLI, App Server, credential,
provider-session, transport, or runtime mechanism. `.docs/rw0-b2-capability.md`
is the sole detailed Capability owner. RW0-B1, RW0-B2-Wire, and
RW0-B2-Capability private semantics are current implemented contracts. RW0-C1
durable phase/evidence mechanics are implemented separately behind private
mutation authority; RW0-D1 artificial offline planner/worker process and capsule mechanics are
implemented separately under the D1 owner. RW0-D2 now has a bounded private
offline source candidate: two guarded validation/review bound effects, checked
C1 evidence, separate fake validator/reviewer/model processes, nine-role input,
and a typed transient preadmission handback. External-copy validation and
independent audit are separate gates; this status grants neither. RW0-C2 physical decision persistence,
live provider/credential/custody, and RW0-E runtime mechanics remain future.
Execution Substrate retains admission and runtime authority."""

REQUIRED_CANDIDATE_ROWS = (
    ('R01', '.docs/authority-boundaries.md', 0o644,
     ('authority_non_effect',), 'authority policy'),
    ('R02', '.docs/autonomous-software-development-operating-model.md', 0o644,
     ('authority_non_effect',), 'composition authority'),
    ('R03', '.docs/c2a-first-slice-semantic-protocol-contract.md', 0o644,
     ('authority_non_effect',), 'C2A protocol and effect boundary'),
    ('R04', '.docs/c2a1-pure-semantic-values.md', 0o644,
     ('authority_non_effect',), 'C2A1 pure semantic boundary'),
    ('R05', '.docs/durable-state-model.md', 0o644,
     ('state_store_writer_session',), 'durable state ownership'),
    ('R06', '.docs/rw0-b1-pure-phase-values.md', 0o644,
     ('authority_non_effect',), 'B1 owner'),
    ('R07', '.docs/rw0-b2-capability.md', 0o644,
     ('private_module_export',), 'Capability owner'),
    ('R08', '.docs/rw0-b2-wire-protocol.md', 0o644,
     ('authority_non_effect',), 'Wire owner'),
    ('R09', '.docs/rw0-remote-worker-contact-phase-entry.md', 0o644,
     ('authority_non_effect',), 'RW0 phase and status integration'),
    ('R10', '.docs/worker-execution-boundary.md', 0o644,
     ('authority_non_effect',), 'worker and ES ownership'),
    ('R11', 'src/ge_nwp_coordinator/_development_pre_execution_plan_disposition_contracts.py', 0o644,
     ('authority_non_effect',), 'pre-execution disposition seam'),
    ('R12', 'src/ge_nwp_coordinator/_rw0_phase_entry_semantic_values.py', 0o644,
     ('authority_non_effect',), 'B1 snapshot seam'),
    ('R13', 'src/ge_nwp_coordinator/_rw0_worker_mechanism_capability_values.py', 0o644,
     ('private_module_export', 'production_importer_caller'), 'Capability implementation'),
    ('R14', 'src/ge_nwp_coordinator/_worker_execution_semantic_values.py', 0o644,
     ('authority_non_effect',), 'EffectFence semantic dependency'),
    ('R15', 'tests/test_architecture_contracts.py', 0o644,
     ('authority_non_effect',), 'architecture controls'),
    ('R16', 'tests/test_c2a_nonimplementation.py', 0o644,
     ('authority_non_effect',), 'C2A non-widening'),
    ('R17', 'tests/test_runtime_non_authority.py', 0o644,
     ('authority_non_effect',), 'runtime non-authority'),
    ('R18', 'tests/test_rw0_b1_boundaries.py', 0o644,
     ('authority_non_effect',), 'B1 boundary controls'),
    ('R19', 'tests/test_rw0_b1_phase_values.py', 0o644,
     ('authority_non_effect',), 'B1 value controls'),
    ('R20', 'tests/test_rw0_b1_relations.py', 0o644,
     ('authority_non_effect',), 'B1 relation controls'),
    ('R21', 'tests/test_rw0_b2_capability_boundaries.py', 0o644,
     (), 'Capability boundary oracle'),
    ('R22', 'tests/test_rw0_b2_capability_relations.py', 0o644,
     ('private_module_export',), 'Capability relation controls'),
    ('R23', 'tests/test_rw0_b2_capability_values.py', 0o644,
     ('private_module_export',), 'Capability value controls'),
    ('R24', 'tests/test_rw0_b2_capability_vectors.py', 0o644,
     ('private_module_export',), 'Capability vector controls'),
    ('R25', 'tests/test_rw0_b2_wire_boundaries.py', 0o644,
     ('authority_non_effect',), 'Wire boundary controls'),
    ('R26', 'tests/test_rw0_remote_contact_phase_entry_contract.py', 0o644,
     ('authority_non_effect',), 'remote-entry contract'),
    ('R27', 'tests/test_section41_pre_execution_plan_disposition_contracts.py', 0o644,
     ('authority_non_effect',), 'disposition boundary'),
    ('R28', 'tests/test_software_development_progression_boundary.py', 0o644,
     ('state_store_writer_session',), 'progression ownership boundary'),
    ('R29', 'tests/test_worker_execution_semantic_boundaries.py', 0o644,
     ('authority_non_effect',), 'worker semantic boundary'),
    ('R30', 'tests/test_worker_execution_semantic_values.py', 0o644,
     ('authority_non_effect',), 'worker semantic values'),
)

PROTECTED_CONTENT_ROWS = (
    ('P01', 'src/ge_nwp_coordinator/_rw0_wire_protocol_values.py', 126092, 'fdb97043f4f93620ecf5be43e78ebda0553e2792a219ab846789ad586790c776',
     ('authority_non_effect',), 'protected Wire implementation'),
    ('P02', 'src/ge_nwp_coordinator/_development_author_effect_establishment_contracts.py', 63518, 'f6938024436a765a69e9a44d20d834a85075ba10b821e61e3e91bfb09cf17af0',
     ('authority_non_effect',), 'protected author-effect authority'),
    ('P03', 'src/ge_nwp_coordinator/_development_decision_row_values.py', 53230, '9e0e9c0695adb9f0ad72d9d92c6859c995c2c5ade154a5546f0a1efc347db8ae',
     ('dependency_schema_migration',), 'protected decision row seam'),
    ('P04', 'src/ge_nwp_coordinator/_development_effect_row_values.py', 64606, 'bbe52faf7ad69e2e643a404808cb0e68d4f7c76a668426d58029a7c108cfa158',
     ('dependency_schema_migration',), 'protected effect row seam'),
    ('P05', 'src/ge_nwp_coordinator/_development_program_row_values.py', 60276, 'd8557eac3f4956c6fdedaf851b9f230f871d0d41eb381fdb09cdecece8df6422',
     ('dependency_schema_migration',), 'protected program row seam'),
    ('P06', 'src/ge_nwp_coordinator/__init__.py', 2385, '60230ae31032071ab52b16c3537a1b2b398e06a4b1f4ec926485471927b2f2b5',
     ('private_module_export',), 'protected package exports'),
    ('P07', 'pyproject.toml', 330, 'c59ff8c0005b063636ff161002f1b1c45a81227b4ed30a988412f01a474e0ac9',
     ('dependency_schema_migration',), 'protected dependency metadata'),
    ('P08', 'tests/c2a_contract_support.py', 154372, '58be92ddffae6f4b901ae3632521481ab8d9ce0e02a819ef9421408d08eedd85',
     ('authority_non_effect',), 'protected C2A support'),
    ('P09', 'tests/test_c2b2_development_row_value_boundaries.py', 17972, 'f2a7089748f39dc8c40a932ac770edd3ffa7f8ea581b053af101dfda8100c830',
     ('dependency_schema_migration',), 'protected C2B2 schema controls'),
    ('P10', 'tests/test_codex_agent_config.py', 1082, '0691c90c0178632a793a93595ba344169fb9b9669de155939fb4873db2f0d3ee',
     ('authority_non_effect',), 'protected Codex configuration'),
    ('P11', 'AGENTS.md', 64142, 'ddf5485d88fc4604429a2b553643e3a8a80828002d17f7cfcb10cb935d018166',
     ('authority_non_effect',), 'protected repository governance'),
    ('P12', 'README.md', 47694, 'f48f2439d282350e36b5d8374864cb5dfe19eb417672737e820500c3a68224f3',
     ('authority_non_effect',), 'protected public claims'),
    ('P13', '.docs/software-development-progression-boundary.md', 28654, 'b8761655ee42512c0e77ab8c774c2b2d3d8f9ac36a9bd0c74872ad4bf2994419',
     ('state_store_writer_session',), 'protected progression authority'),
)


def _assert_single_literal_protected_rows_source(source: str) -> tuple:
    tree = ast.parse(source)
    bindings: list[ast.AST] = []

    def visit_module_execution(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Lambda)):
            return
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign,
                             ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            if any(isinstance(name, ast.Name) and name.id == "PROTECTED_CONTENT_ROWS"
                   and isinstance(name.ctx, ast.Store)
                   for target in targets for name in ast.walk(target)):
                bindings.append(node)
        for child in ast.iter_child_nodes(node):
            visit_module_execution(child)

    visit_module_execution(tree)
    if len(bindings) != 1:
        raise AssertionError("protected_rows:single_literal_binding")
    initializer = bindings[0]
    if (not isinstance(initializer, ast.Assign) or len(initializer.targets) != 1
            or not isinstance(initializer.targets[0], ast.Name)
            or initializer.targets[0].id != "PROTECTED_CONTENT_ROWS"):
        raise AssertionError("protected_rows:single_literal_binding")
    try:
        rows = ast.literal_eval(initializer.value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise AssertionError("protected_rows:single_literal_binding") from None
    if type(rows) is not tuple or len(rows) != 13 or rows != PROTECTED_CONTENT_ROWS:
        raise AssertionError("protected_rows:literal_identity")
    for pid, reference in CAPABILITY_REPLACEMENT_EXPECTED.items():
        matches = [row for row in rows if type(row) is tuple and row[0] == pid]
        if len(matches) != 1:
            raise AssertionError("protected_rows:literal_identity")
        row = matches[0]
        if (len(row) != 6 or (row[1], (row[2], row[3]), row[4], row[5]) != (
                reference["path"], reference["replacement_identity"],
                reference["contract_classes"], reference["purpose"],
        )):
            raise AssertionError("protected_rows:literal_identity")
    return rows

def _assert_regular_mode_0644(row_id: str, relative_path: str) -> None:
    try:
        metadata = (ROOT / relative_path).lstat()
    except OSError:
        raise AssertionError(f"{row_id}:required_path") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise AssertionError(f"{row_id}:regular_file")
    if stat.S_IMODE(metadata.st_mode) != 0o644:
        raise AssertionError(f"{row_id}:mode_0644")


def _assert_exact_content_identity(
    row_id: str,
    relative_path: str,
    expected_size: int,
    expected_sha256: str,
) -> None:
    path = ROOT / relative_path
    try:
        metadata = path.lstat()
    except OSError:
        raise AssertionError(f"{row_id}:required_path") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise AssertionError(f"{row_id}:regular_file")
    try:
        payload = path.read_bytes()
    except OSError:
        raise AssertionError(f"{row_id}:required_path") from None
    if len(payload) != expected_size:
        raise AssertionError(f"{row_id}:protected_size")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise AssertionError(f"{row_id}:protected_sha256")

def normalize(body: str) -> str:
    return " ".join(body.split())


def extract_visible_block(text: str, begin: str, end: str) -> str:
    assert text.count(begin) == text.count(end) == 1
    start = text.index(begin)
    finish = text.index(end)
    assert start < finish
    before = text[:start]
    assert before.count("```") % 2 == 0
    return text[start + len(begin):finish].strip()


def assert_owner_layout(text: str) -> None:
    body = extract_visible_block(text, OWNER_BEGIN, OWNER_END)
    assert text.splitlines().count("# RW0-B2-Capability") == 1
    assert "## Current implemented contract" in text[:text.index(OWNER_BEGIN)]
    assert "RW0-B2-Capability" in body
    assert "validate_worker_mechanism_capability_qualification" in body
    assert text[text.index(OWNER_END) + len(OWNER_END):].strip() == ""
    assert "<!-- RW0_B2_CAPABILITY_OWNER_" not in body

def test_exact_private_import_direction_exports_and_public_surface() -> None:
    assert capability.__all__ == ()
    import ge_nwp_coordinator
    for name in (
        "RW0WorkerMechanismCapabilityDeclarationV1",
        "RW0WorkerMechanismCapabilityObservationV1",
        "RW0WorkerMechanismCapabilityQualificationV1",
        "RW0WorkerMechanismCapabilityError",
        "validate_worker_mechanism_capability_qualification",
    ):
        assert name not in ge_nwp_coordinator.__dict__

    source_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    allowed_standard = {"datetime", "hashlib", "json", "re", "typing", "weakref"}
    exact_private = {
        "_worker_execution_semantic_values": {"EffectFenceV1"},
        "_rw0_phase_entry_semantic_values": {
            "RW0PhaseEntryBasisV1",
            "RW0AuthorityVerificationObservationV1",
            "RW0RemoteHostReadinessObservationV1",
            "RW0EffectHostQualificationV1",
            "_validate_host_qualification_with_snapshots",
        },
        "_rw0_wire_protocol_values": {"wire_profile_mapping"},
    }
    seen_private: dict[str, set[str]] = {}
    for node in ast.walk(source_tree):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed_standard for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                assert node.level == 0 and {alias.name for alias in node.names} == {"annotations"}
            else:
                assert node.level == 1 and node.module in exact_private
                seen_private[node.module] = {alias.name for alias in node.names}
    assert seen_private == exact_private

    c1_values_path = PACKAGE / "_rw0_c1_semantic_values.py"
    c1_runtime_path = PACKAGE / "_sqlite_rw0_c1.py"
    importers: list[Path] = []
    for path in PACKAGE.rglob("*.py"):
        if path == SOURCE:
            continue
        source = path.read_text(encoding="utf-8")
        if "_rw0_worker_mechanism_capability_values" not in source:
            continue
        importers.append(path)
        imports = [
            node for node in ast.parse(source).body
            if isinstance(node, ast.ImportFrom) and node.level == 1
        ]
        if path == c1_values_path:
            owner_imports = [
                node for node in imports
                if node.module == "_rw0_worker_mechanism_capability_values"
            ]
            assert len(owner_imports) == 1
            assert {alias.name for alias in owner_imports[0].names} == {
                "RW0WorkerMechanismCapabilityDeclarationV1",
                "RW0WorkerMechanismCapabilityObservationV1",
                "RW0WorkerMechanismCapabilityQualificationV1",
            }
        else:
            assert path == c1_runtime_path
            owner_imports = [
                node for node in imports
                if node.module is None
                and [(alias.name, alias.asname) for alias in node.names]
                == [("_rw0_worker_mechanism_capability_values", "_capability_values")]
            ]
            assert len(owner_imports) == 1
    assert set(importers) == {c1_values_path, c1_runtime_path}
    assert "_rw0_worker_mechanism_capability_values" not in (
        ROOT / "src/ge_nwp_coordinator/__init__.py").read_text(encoding="utf-8")

def test_source_is_pure_static_and_has_no_runtime_or_storage_mechanism() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    forbidden_calls = {
        "eval", "exec", "compile", "__import__", "open", "getattr", "setattr",
    }
    forbidden_attributes = {
        "open", "connect", "run", "Popen", "system", "getenv", "environ",
        "import_module", "now", "utcnow", "time", "monotonic", "sleep",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attributes
    source = SOURCE.read_text(encoding="utf-8").lower()
    for forbidden in (
        "sqlite", "subprocess", "socket", "requests", "urllib", "pathlib",
        "codex", "app_server", "app-server", "oauth", "api_key", "bearer_value",
        "migration", "sqlalchemy",
    ):
        assert forbidden not in source


def test_wire_owner_is_loaded_once_fixed_and_manifest_is_not_retained(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "_capture_wire_owner_pair"
    ]
    assert len(calls) == 1
    assert len(calls[0].args) == 1
    assert isinstance(calls[0].args[0], ast.Name)
    assert calls[0].args[0].id == "_wire_profile_mapping_owner"
    assert calls[0].keywords == []
    assert capability._WIRE_PROFILE_REF == "rw0-wire-nwpf-v1"
    assert capability._WIRE_PROFILE_DIGEST == (
        "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454")
    assert not any(
        type(value) is dict and "manifest" in value
        for value in capability.__dict__.values()
    )
    retained = (capability._WIRE_PROFILE_REF, capability._WIRE_PROFILE_DIGEST)
    assert capability._capture_wire_owner_pair(
        lambda: {
            "schema_id": "governed-execution.nwp-rw0-wire-protocol-profile.v1",
            "profile_ref": retained[0],
            "manifest": {},
            "profile_digest": retained[1],
        }
    ) == ("valid", retained)
    invariant_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "_raise_wire_owner_invariant"
    ]
    assert len(invariant_calls) == 1
    assert invariant_calls[0].args == [] and invariant_calls[0].keywords == []


def test_wire_owner_callable_is_deleted_after_the_single_import_time_load() -> None:
    assert "wire_profile_mapping" not in capability.__dict__
    assert "_wire_profile_mapping_owner" not in capability.__dict__
    assert not any(
        callable(value)
        and getattr(value, "__module__", "")
        == "ge_nwp_coordinator._rw0_wire_protocol_values"
        for value in capability.__dict__.values()
    )


def test_hostile_wire_owner_key_is_sanitized_without_foreign_equality() -> None:
    class HostileKey:
        def __hash__(self) -> int:
            return hash("schema_id")

        def __eq__(self, other: object) -> bool:
            raise LookupError("SENTINEL-HOSTILE-WIRE-KEY")

    def owner() -> dict[object, object]:
        return {
            HostileKey(): "governed-execution.nwp-rw0-wire-protocol-profile.v1",
            "profile_ref": "rw0-wire-nwpf-v1",
            "manifest": {},
            "profile_digest": (
                "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
            ),
        }

    assert capability._capture_wire_owner_pair(owner) == ("invalid", None)
    with pytest.raises(RuntimeError) as caught:
        capability._raise_wire_owner_invariant()
    assert caught.value.args == (
        "RW0WorkerMechanismCapabilityWireOwnerInvariant",
    )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_wire_owner_loader_sanitizes_every_malformed_shape() -> None:
    valid = {
        "schema_id": "governed-execution.nwp-rw0-wire-protocol-profile.v1",
        "profile_ref": "rw0-wire-nwpf-v1",
        "manifest": {},
        "profile_digest": "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454",
    }

    class DictSubclass(dict):
        pass

    malformed = [
        None,
        DictSubclass(valid),
        {"profile_ref": valid["profile_ref"], "schema_id": valid["schema_id"],
         "manifest": {}, "profile_digest": valid["profile_digest"]},
        {**valid, "schema_id": "wrong"},
        {**valid, "profile_ref": "wrong"},
        {**valid, "manifest": DictSubclass()},
        {**valid, "profile_digest": "0" * 64},
        {**valid, "extra": "wrong"},
    ]
    for value in malformed:
        assert capability._capture_wire_owner_pair(
            lambda value=value: value
        ) == ("invalid", None)
        with pytest.raises(RuntimeError) as caught:
            capability._raise_wire_owner_invariant()
        assert caught.value.args == ("RW0WorkerMechanismCapabilityWireOwnerInvariant",)
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None

    def foreign() -> dict[str, object]:
        raise ValueError("SENTINEL-WIRE-FOREIGN")

    assert capability._capture_wire_owner_pair(foreign) == ("invalid", None)
    with pytest.raises(RuntimeError) as caught:
        capability._raise_wire_owner_invariant()
    assert str(caught.value) == "RW0WorkerMechanismCapabilityWireOwnerInvariant"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def _owned_capability_frame(frame) -> bool:
    return Path(frame.f_code.co_filename).resolve() == SOURCE.resolve()


def _contains_hostile_identity(
    value: object,
    hostile_ids: set[int],
    seen: set[int] | None = None,
) -> bool:
    if id(value) in hostile_ids:
        return True
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    if type(value) is dict:
        return any(
            _contains_hostile_identity(key, hostile_ids, seen)
            or _contains_hostile_identity(member, hostile_ids, seen)
            for key, member in value.items()
        )
    if type(value) in (tuple, list, set, frozenset):
        return any(_contains_hostile_identity(member, hostile_ids, seen) for member in value)
    if isinstance(value, types.FunctionType):
        defaults = value.__defaults__ or ()
        keywords = value.__kwdefaults__ or {}
        closure = tuple(cell.cell_contents for cell in (value.__closure__ or ()))
        return any(
            _contains_hostile_identity(member, hostile_ids, seen)
            for member in (defaults, keywords, closure)
        )
    return False


def _failed_isolated_capability_import(
    owner_call,
) -> tuple[RuntimeError, types.ModuleType]:
    wire_name = "ge_nwp_coordinator._rw0_wire_protocol_values"
    previous = sys.modules[wire_name]
    fake_wire = types.ModuleType(wire_name)
    fake_wire.wire_profile_mapping = owner_call
    probe_name = "ge_nwp_coordinator._rw0_capability_retention_probe"
    spec = importlib.util.spec_from_file_location(probe_name, SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[wire_name] = fake_wire
    sys.modules[probe_name] = module
    try:
        with pytest.raises(RuntimeError) as caught:
            spec.loader.exec_module(module)
        return caught.value, module
    finally:
        sys.modules[wire_name] = previous
        sys.modules.pop(probe_name, None)
        fake_wire.wire_profile_mapping = None
        owner_call = None


@pytest.mark.parametrize("failure_mode", ("key", "value", "mapping", "manifest", "exception"))
def test_failed_wire_import_retains_no_hostile_owner_graph(failure_mode: str) -> None:
    hostile_key = object()
    hostile_value = object()
    hostile_manifest_key = object()
    hostile_manifest_value = object()
    foreign_error = LookupError("SENTINEL-WIRE-OWNER-FOREIGN")
    manifest = {hostile_manifest_key: hostile_manifest_value}
    valid = {
        "schema_id": "governed-execution.nwp-rw0-wire-protocol-profile.v1",
        "profile_ref": "rw0-wire-nwpf-v1",
        "manifest": {},
        "profile_digest": "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454",
    }
    if failure_mode == "key":
        mapping = {hostile_key: valid["schema_id"], **{key: value for key, value in valid.items() if key != "schema_id"}}
    elif failure_mode == "value":
        mapping = {**valid, "schema_id": hostile_value}
    elif failure_mode == "mapping":
        mapping = {**valid, "profile_digest": hostile_value}
    elif failure_mode == "manifest":
        mapping = {**valid, "manifest": manifest, "profile_digest": "0" * 64}
    else:
        mapping = valid

    def owner_call(captured=mapping, error=foreign_error):
        if failure_mode == "exception":
            raise error
        return captured

    hostile_objects = {
        id(hostile_key), id(hostile_value), id(hostile_manifest_key),
        id(hostile_manifest_value), id(foreign_error), id(manifest), id(mapping),
        id(owner_call),
    }
    caught, module = _failed_isolated_capability_import(owner_call)
    assert caught.args == ("RW0WorkerMechanismCapabilityWireOwnerInvariant",)
    assert caught.__cause__ is None
    assert caught.__context__ is None
    assert "_wire_profile_mapping_owner" not in module.__dict__

    assert not _contains_hostile_identity(module.__dict__, hostile_objects)
    traceback_cursor = caught.__traceback__
    owned_frames = 0
    while traceback_cursor is not None:
        frame = traceback_cursor.tb_frame
        if _owned_capability_frame(frame):
            owned_frames += 1
            assert not _contains_hostile_identity(frame.f_locals, hostile_objects)
            assert not _contains_hostile_identity(frame.f_globals, hostile_objects)
        traceback_cursor = traceback_cursor.tb_next
    assert owned_frames >= 1


@pytest.mark.parametrize(
    "signal", (KeyboardInterrupt(), SystemExit(), GeneratorExit())
)
def test_wire_capture_propagates_process_control(signal: BaseException) -> None:
    def owner_call() -> object:
        raise signal

    with pytest.raises(type(signal)) as caught:
        capability._capture_wire_owner_pair(owner_call)
    assert caught.value is signal


def test_owner_and_five_status_projections_are_visible_unique_and_synchronized() -> None:
    owner = OWNER.read_text(encoding="utf-8")
    assert_owner_layout(owner)
    bodies = []
    for path in STATUS_PATHS:
        text = path.read_text(encoding="utf-8")
        body = extract_visible_block(text, STATUS_BEGIN, STATUS_END)
        bodies.append(normalize(body))
    assert len(set(bodies)) == 1
    assert bodies[0] == normalize(EXPECTED_STATUS)

    owner_mutants = (
        owner.replace(OWNER_END, OWNER_END + "\ntrailing visible owner prose"),
        owner.replace(OWNER_END, OWNER_BEGIN, 1),
        owner.replace(OWNER_BEGIN, OWNER_END, 1),
        owner.replace(OWNER_BEGIN, "```\n" + OWNER_BEGIN, 1),
        owner.replace(OWNER_END, OWNER_END + "\n```", 1),
        owner.replace("# RW0-B2-Capability", "# RW0-B2-Capability\n\n# RW0-B2-Capability", 1),
    )
    for mutant in owner_mutants:
        with pytest.raises(AssertionError):
            assert_owner_layout(mutant)

def test_required_candidate_surface_is_literal_unique_regular_and_mode_0644() -> None:
    if type(REQUIRED_CANDIDATE_ROWS) is not tuple:
        raise AssertionError("candidate_rows:shape")
    if not all(type(row) is tuple and len(row) == 5 for row in REQUIRED_CANDIDATE_ROWS):
        raise AssertionError("candidate_rows:shape")
    expected_ids = (
        "R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10",
        "R11", "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20",
        "R21", "R22", "R23", "R24", "R25", "R26", "R27", "R28", "R29", "R30",
    )
    expected_paths = (
        ".docs/authority-boundaries.md",
        ".docs/autonomous-software-development-operating-model.md",
        ".docs/c2a-first-slice-semantic-protocol-contract.md",
        ".docs/c2a1-pure-semantic-values.md",
        ".docs/durable-state-model.md",
        ".docs/rw0-b1-pure-phase-values.md",
        ".docs/rw0-b2-capability.md",
        ".docs/rw0-b2-wire-protocol.md",
        ".docs/rw0-remote-worker-contact-phase-entry.md",
        ".docs/worker-execution-boundary.md",
        "src/ge_nwp_coordinator/_development_pre_execution_plan_disposition_contracts.py",
        "src/ge_nwp_coordinator/_rw0_phase_entry_semantic_values.py",
        "src/ge_nwp_coordinator/_rw0_worker_mechanism_capability_values.py",
        "src/ge_nwp_coordinator/_worker_execution_semantic_values.py",
        "tests/test_architecture_contracts.py",
        "tests/test_c2a_nonimplementation.py",
        "tests/test_runtime_non_authority.py",
        "tests/test_rw0_b1_boundaries.py",
        "tests/test_rw0_b1_phase_values.py",
        "tests/test_rw0_b1_relations.py",
        "tests/test_rw0_b2_capability_boundaries.py",
        "tests/test_rw0_b2_capability_relations.py",
        "tests/test_rw0_b2_capability_values.py",
        "tests/test_rw0_b2_capability_vectors.py",
        "tests/test_rw0_b2_wire_boundaries.py",
        "tests/test_rw0_remote_contact_phase_entry_contract.py",
        "tests/test_section41_pre_execution_plan_disposition_contracts.py",
        "tests/test_software_development_progression_boundary.py",
        "tests/test_worker_execution_semantic_boundaries.py",
        "tests/test_worker_execution_semantic_values.py",
    )
    if tuple(row[0] for row in REQUIRED_CANDIDATE_ROWS) != expected_ids:
        raise AssertionError("candidate_rows:inventory")
    if tuple(row[1] for row in REQUIRED_CANDIDATE_ROWS) != expected_paths:
        raise AssertionError("candidate_rows:inventory")
    row_ids = tuple(row[0] for row in REQUIRED_CANDIDATE_ROWS)
    paths = tuple(row[1] for row in REQUIRED_CANDIDATE_ROWS)
    purposes = tuple(row[4] for row in REQUIRED_CANDIDATE_ROWS)
    if not all(type(row_id) is str for row_id in row_ids):
        raise AssertionError("candidate_rows:shape")
    if not all(type(path) is str for path in paths):
        raise AssertionError("candidate_rows:shape")
    if len(set(row_ids)) != 30:
        raise AssertionError("candidate_rows:unique_ids")
    if len(set(paths)) != 30:
        raise AssertionError("candidate_rows:unique_paths")
    if not all(type(purpose) is str and purpose for purpose in purposes):
        raise AssertionError("candidate_rows:shape")
    if len(set(purposes)) != 30:
        raise AssertionError("candidate_rows:unique_purposes")
    for row_id, relative_path, expected_mode, contract_classes, _purpose in REQUIRED_CANDIDATE_ROWS:
        if type(expected_mode) is not int or expected_mode != 0o644:
            raise AssertionError("candidate_rows:shape")
        if type(contract_classes) is not tuple or not all(
            type(contract_class) is str for contract_class in contract_classes
        ):
            raise AssertionError("candidate_rows:contract_classes")
        _assert_regular_mode_0644(row_id, relative_path)


def test_protected_content_surface_has_exact_literal_identities() -> None:
    observed = _guard_replacement_semantic_evidence()
    _assert_capability_semantic_integrity(observed, CAPABILITY_REPLACEMENT_EXPECTED)
    _assert_single_literal_protected_rows_source(Path(__file__).read_text(encoding="utf-8"))
    if type(PROTECTED_CONTENT_ROWS) is not tuple:
        raise AssertionError("protected_rows:shape")
    if not all(type(row) is tuple and len(row) == 6 for row in PROTECTED_CONTENT_ROWS):
        raise AssertionError("protected_rows:shape")
    expected_ids = (
        "P01", "P02", "P03", "P04", "P05", "P06", "P07",
        "P08", "P09", "P10", "P11", "P12", "P13",
    )
    expected_paths = (
        "src/ge_nwp_coordinator/_rw0_wire_protocol_values.py",
        "src/ge_nwp_coordinator/_development_author_effect_establishment_contracts.py",
        "src/ge_nwp_coordinator/_development_decision_row_values.py",
        "src/ge_nwp_coordinator/_development_effect_row_values.py",
        "src/ge_nwp_coordinator/_development_program_row_values.py",
        "src/ge_nwp_coordinator/__init__.py",
        "pyproject.toml",
        "tests/c2a_contract_support.py",
        "tests/test_c2b2_development_row_value_boundaries.py",
        "tests/test_codex_agent_config.py",
        "AGENTS.md",
        "README.md",
        ".docs/software-development-progression-boundary.md",
    )
    if tuple(row[0] for row in PROTECTED_CONTENT_ROWS) != expected_ids:
        raise AssertionError("protected_rows:inventory")
    if tuple(row[1] for row in PROTECTED_CONTENT_ROWS) != expected_paths:
        raise AssertionError("protected_rows:inventory")
    row_ids = tuple(row[0] for row in PROTECTED_CONTENT_ROWS)
    paths = tuple(row[1] for row in PROTECTED_CONTENT_ROWS)
    purposes = tuple(row[5] for row in PROTECTED_CONTENT_ROWS)
    if not all(type(row_id) is str for row_id in row_ids):
        raise AssertionError("protected_rows:shape")
    if not all(type(path) is str for path in paths):
        raise AssertionError("protected_rows:shape")
    if len(set(row_ids)) != 13:
        raise AssertionError("protected_rows:unique_ids")
    if len(set(paths)) != 13:
        raise AssertionError("protected_rows:unique_paths")
    if not all(type(purpose) is str and purpose for purpose in purposes):
        raise AssertionError("protected_rows:shape")
    if len(set(purposes)) != 13:
        raise AssertionError("protected_rows:unique_purposes")
    required_paths = {row[1] for row in REQUIRED_CANDIDATE_ROWS}
    if required_paths & set(paths):
        raise AssertionError("boundary_rows:disjoint_paths")
    for row_id, relative_path, expected_size, expected_sha256, contract_classes, _purpose in PROTECTED_CONTENT_ROWS:
        if type(expected_size) is not int or expected_size < 0:
            raise AssertionError("protected_rows:shape")
        if not (
            type(expected_sha256) is str
            and len(expected_sha256) == 64
            and all(character in "0123456789abcdef" for character in expected_sha256)
        ):
            raise AssertionError("protected_rows:shape")
        if type(contract_classes) is not tuple or not all(
            type(contract_class) is str for contract_class in contract_classes
        ):
            raise AssertionError("protected_rows:contract_classes")
        _assert_exact_content_identity(
            row_id, relative_path, expected_size, expected_sha256
        )


@pytest.mark.parametrize("case", (
    "comment", "string", "readonly", "second_direct", "second_annotated",
    "second_augmented", "inside_if", "inside_for", "nonliteral", "missing",
))
def test_protected_table_source_binding_variants(case: str) -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    if case in {"nonliteral", "missing"}:
        node = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.Assign) and any(
                        isinstance(target, ast.Name) and target.id == "PROTECTED_CONTENT_ROWS"
                        for target in node.targets))
        lines = source.splitlines(keepends=True)
        replacement = ([] if case == "missing" else
                       ["PROTECTED_CONTENT_ROWS = CAPABILITY_REPLACEMENT_EXPECTED\n"])
        lines[node.lineno - 1:node.end_lineno] = replacement
        variant = "".join(lines)
    else:
        additions = {
            "comment": "\n# PROTECTED_CONTENT_ROWS = dynamic_example\n",
            "string": "\nexample_text = 'PROTECTED_CONTENT_ROWS = dynamic_example'\n",
            "readonly": "\nfor observed_row in PROTECTED_CONTENT_ROWS:\n    pass\n",
            "second_direct": "\nPROTECTED_CONTENT_ROWS = tuple(PROTECTED_CONTENT_ROWS)\n",
            "second_annotated": "\nPROTECTED_CONTENT_ROWS: tuple = tuple(PROTECTED_CONTENT_ROWS)\n",
            "second_augmented": "\nPROTECTED_CONTENT_ROWS += ()\n",
            "inside_if": "\nif True:\n    PROTECTED_CONTENT_ROWS = tuple(PROTECTED_CONTENT_ROWS)\n",
            "inside_for": "\nfor _ in (0,):\n    PROTECTED_CONTENT_ROWS = tuple(PROTECTED_CONTENT_ROWS)\n",
        }
        variant = source + additions[case]
    if case in {"comment", "string", "readonly"}:
        assert _assert_single_literal_protected_rows_source(variant) == PROTECTED_CONTENT_ROWS
    else:
        with pytest.raises(AssertionError, match="^protected_rows:single_literal_binding$"):
            _assert_single_literal_protected_rows_source(variant)


def test_boundary_contract_rows_are_literal_complete_unique_and_consistent() -> None:
    if len(REQUIRED_CANDIDATE_ROWS) != 30 or len(PROTECTED_CONTENT_ROWS) != 13:
        raise AssertionError("boundary_rows:count_30_13")
    allowed_classes = {
        "authority_non_effect",
        "private_module_export",
        "production_importer_caller",
        "dependency_schema_migration",
        "state_store_writer_session",
    }
    required_classes = tuple(row[3] for row in REQUIRED_CANDIDATE_ROWS)
    protected_classes = tuple(row[4] for row in PROTECTED_CONTENT_ROWS)
    expected_required_classes = (
        ("authority_non_effect",), ("authority_non_effect",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("state_store_writer_session",), ("authority_non_effect",),
        ("private_module_export",), ("authority_non_effect",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("private_module_export", "production_importer_caller"),
        ("authority_non_effect",), ("authority_non_effect",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("authority_non_effect",), (), ("private_module_export",),
        ("private_module_export",), ("private_module_export",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("authority_non_effect",), ("state_store_writer_session",),
        ("authority_non_effect",), ("authority_non_effect",),
    )
    expected_protected_classes = (
        ("authority_non_effect",), ("authority_non_effect",),
        ("dependency_schema_migration",), ("dependency_schema_migration",),
        ("dependency_schema_migration",), ("private_module_export",),
        ("dependency_schema_migration",), ("authority_non_effect",),
        ("dependency_schema_migration",), ("authority_non_effect",),
        ("authority_non_effect",), ("authority_non_effect",),
        ("state_store_writer_session",),
    )
    if required_classes != expected_required_classes:
        raise AssertionError("candidate_rows:contract_classes")
    if protected_classes != expected_protected_classes:
        raise AssertionError("protected_rows:contract_classes")
    all_classes = {
        contract_class
        for classes in (*required_classes, *protected_classes)
        for contract_class in classes
    }
    if all_classes != allowed_classes:
        raise AssertionError("boundary_rows:class_coverage")
    classes_by_id = {
        row[0]: row[3] for row in REQUIRED_CANDIDATE_ROWS
    } | {
        row[0]: row[4] for row in PROTECTED_CONTENT_ROWS
    }
    if classes_by_id.get("R13") != (
        "private_module_export", "production_importer_caller"
    ):
        raise AssertionError("boundary_rows:class_coverage")
    if classes_by_id.get("R21") != ():
        raise AssertionError("boundary_rows:class_coverage")
    if classes_by_id.get("P06") != ("private_module_export",):
        raise AssertionError("boundary_rows:class_coverage")
    for row_id in ("P03", "P04", "P05", "P07", "P09"):
        if classes_by_id.get(row_id) != ("dependency_schema_migration",):
            raise AssertionError("boundary_rows:class_coverage")
    if classes_by_id.get("P13") != ("state_store_writer_session",):
        raise AssertionError("boundary_rows:class_coverage")
    all_ids = tuple(row[0] for row in REQUIRED_CANDIDATE_ROWS) + tuple(
        row[0] for row in PROTECTED_CONTENT_ROWS
    )
    all_paths = tuple(row[1] for row in REQUIRED_CANDIDATE_ROWS) + tuple(
        row[1] for row in PROTECTED_CONTENT_ROWS
    )
    all_purposes = tuple(row[4] for row in REQUIRED_CANDIDATE_ROWS) + tuple(
        row[5] for row in PROTECTED_CONTENT_ROWS
    )
    if len(set(all_ids)) != 43:
        raise AssertionError("boundary_rows:unique_ids")
    if len(set(all_paths)) != 43:
        raise AssertionError("boundary_rows:disjoint_paths")
    if len(set(all_purposes)) != 43:
        raise AssertionError("boundary_rows:unique_purposes")

def test_error_and_value_surface_is_exactly_private_semantics() -> None:
    assert RW0WorkerMechanismCapabilityError.__module__ == capability.__name__
    assert RW0WorkerMechanismCapabilityDeclarationV1.__module__ == capability.__name__
    assert RW0WorkerMechanismCapabilityObservationV1.__module__ == capability.__name__
    assert RW0WorkerMechanismCapabilityQualificationV1.__module__ == capability.__name__
    assert validate_worker_mechanism_capability_qualification.__module__ == capability.__name__
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("StateStore", "WriterSession", "acceptance", "permission_granted"):
        assert forbidden not in source


CAPABILITY_REPLACEMENT_EXPECTED = {'P08': {'path': 'tests/c2a_contract_support.py',
         'contract_classes': ('authority_non_effect',),
         'old_identity': (154329,
                          '4952d25086220632c969a29e44b9abe29b966fbb031d2305c11d4bf13d39c4f1'),
         'old_identity_changed': True,
         'replacement_identity': (154372,
                                  '58be92ddffae6f4b901ae3632521481ab8d9ce0e02a819ef9421408d08eedd85'),
         'semantic_markers': ('Expansion beyond the first accepted slice without immutable '
                              'admitted-lineage scope and bootstrap-acceptance facts under the '
                              'guard owner and a separately accepted migration review.',),
         'purpose': 'protected C2A support'},
 'P11': {'path': 'AGENTS.md',
         'contract_classes': ('authority_non_effect',),
         'old_identity': (60530,
                          'c12a3449e761728f2093c19bb30134c54994b045843313471a6d715b648355a6'),
         'old_identity_changed': True,
         'replacement_identity': (64142,
                                  'ddf5485d88fc4604429a2b553643e3a8a80828002d17f7cfcb10cb935d018166'),
         'semantic_markers': ('explicitly standing-policy-admitted Coordinator authority lineage',
                              'at most one distinct productive acceptance may commit',
                              'Later ES operation is separately governed and non-replenishing',
                              'Mutable-latch target requirements are explicitly superseded',
                              'none is implemented'),
         'purpose': 'protected repository governance'},
 'P12': {'path': 'README.md',
         'contract_classes': ('authority_non_effect',),
         'old_identity': (44919,
                          '80428110e282c8c17e23c5929a9b7110c098979fee8629dda436ac54ac5418cb'),
         'old_identity_changed': True,
         'replacement_identity': (47694,
                                  'f48f2439d282350e36b5d8374864cb5dfe19eb417672737e820500c3a68224f3'),
         'semantic_markers': ('explicitly standing-policy-admitted Coordinator authority lineage',
                              'at most one distinct productive acceptance may commit',
                              'Later ES operation is separately governed and non-replenishing',
                              'Mutable-latch target requirements are explicitly superseded',
                              'none is implemented'),
         'purpose': 'protected public claims'},
 'P13': {'path': '.docs/software-development-progression-boundary.md',
         'contract_classes': ('state_store_writer_session',),
         'old_identity': (27704,
                          'ab5c686211065eee0d9ad603b11eb32d61f1744a92660104108ead673ae9f4b4'),
         'old_identity_changed': True,
         'replacement_identity': (28654,
                                  'b8761655ee42512c0e77ab8c774c2b2d3d8f9ac36a9bd0c74872ad4bf2994419'),
         'semantic_markers': ('explicitly standing-policy-admitted Coordinator authority lineage',
                              'at most one distinct productive acceptance may commit',
                              'Later ES operation is separately governed and non-replenishing',
                              'Mutable-latch target requirements are explicitly superseded',
                              'none is implemented'),
         'purpose': 'protected progression authority'}}


CAPABILITY_OLD_IDENTITIES = {'P08': (154329, '4952d25086220632c969a29e44b9abe29b966fbb031d2305c11d4bf13d39c4f1'),
 'P11': (60530, 'c12a3449e761728f2093c19bb30134c54994b045843313471a6d715b648355a6'),
 'P12': (44919, '80428110e282c8c17e23c5929a9b7110c098979fee8629dda436ac54ac5418cb'),
 'P13': (27704, 'ab5c686211065eee0d9ad603b11eb32d61f1744a92660104108ead673ae9f4b4')}
CAPABILITY_SEMANTIC_MARKERS = {'P08': ('Expansion beyond the first accepted slice without immutable admitted-lineage scope and '
         'bootstrap-acceptance facts under the guard owner and a separately accepted migration '
         'review.',),
 'P11': ('explicitly standing-policy-admitted Coordinator authority lineage',
         'at most one distinct productive acceptance may commit',
         'Later ES operation is separately governed and non-replenishing',
         'Mutable-latch target requirements are explicitly superseded',
         'none is implemented'),
 'P12': ('explicitly standing-policy-admitted Coordinator authority lineage',
         'at most one distinct productive acceptance may commit',
         'Later ES operation is separately governed and non-replenishing',
         'Mutable-latch target requirements are explicitly superseded',
         'none is implemented'),
 'P13': ('explicitly standing-policy-admitted Coordinator authority lineage',
         'at most one distinct productive acceptance may commit',
         'Later ES operation is separately governed and non-replenishing',
         'Mutable-latch target requirements are explicitly superseded',
         'none is implemented')}

def _guard_replacement_semantic_evidence():
    """Observed document semantics and protected ownership, not assertion side effects."""
    evidence = {}
    for row in PROTECTED_CONTENT_ROWS:
        pid, path, _size, _sha, classes, purpose = row
        if pid not in ('P08', 'P11', 'P12', 'P13'):
            continue
        data = (ROOT / path).read_bytes()
        identity = (len(data), hashlib.sha256(data).hexdigest())
        compact = ' '.join(data.decode('utf-8').split())
        evidence[pid] = {
            'path': path, 'contract_classes': classes,
            'old_identity': CAPABILITY_OLD_IDENTITIES[pid],
            'old_identity_changed': identity != CAPABILITY_OLD_IDENTITIES[pid],
            'replacement_identity': identity,
            'semantic_markers': tuple(marker for marker in CAPABILITY_SEMANTIC_MARKERS[pid] if marker in compact),
            'purpose': purpose,
        }
    return evidence


def _assert_capability_semantic_integrity(observed, expected, path=''):
    location = path or '/'
    if type(observed) is not type(expected):
        raise AssertionError('capability_semantic_integrity:' + location + ':type')
    if type(expected) is dict:
        if set(observed) != set(expected):
            raise AssertionError('capability_semantic_integrity:' + location + ':keys')
        for key, value in expected.items():
            _assert_capability_semantic_integrity(observed[key], value, path + '/' + key)
    elif type(expected) is tuple:
        if len(observed) != len(expected):
            raise AssertionError('capability_semantic_integrity:' + location + ':length')
        for index, (actual, wanted) in enumerate(zip(observed, expected, strict=True)):
            _assert_capability_semantic_integrity(actual, wanted, path + '/' + str(index))
    elif observed != expected:
        raise AssertionError('capability_semantic_integrity:' + location + ':value')


@pytest.mark.parametrize('case', ['none', 'empty', 'missing_P08', 'missing_markers'])
def test_capability_semantic_integrity_hostile(case):
    from copy import deepcopy
    observed = deepcopy(CAPABILITY_REPLACEMENT_EXPECTED)
    boundary = 'capability_semantic_integrity:/:keys'
    if case == 'none':
        observed = None; boundary = 'capability_semantic_integrity:/:type'
    elif case == 'empty':
        observed = {}
    elif case == 'missing_P08':
        observed.pop('P08')
    else:
        observed['P11']['semantic_markers'] = ()
        boundary = 'capability_semantic_integrity:/P11/semantic_markers:length'
    import re
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_capability_semantic_integrity(observed, CAPABILITY_REPLACEMENT_EXPECTED)
