"""B1 private source and privacy boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
from test_rw0_b1_vectors import mapping_for

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ge_nwp_coordinator/_rw0_phase_entry_semantic_values.py"
PACKAGE = ROOT / "src/ge_nwp_coordinator"


def test_private_module_has_no_package_exports_or_production_importer() -> None:
    assert b1.__all__ == ()
    import ge_nwp_coordinator
    assert not any(name.startswith("RW0") for name in ge_nwp_coordinator.__dict__)
    for path in PACKAGE.rglob("*.py"):
        if path == SOURCE:
            continue
        assert "_rw0_phase_entry_semantic_values" not in path.read_text()


def test_pure_import_and_ast_boundary() -> None:
    tree = ast.parse(SOURCE.read_text())
    allowed_std = {"datetime", "hashlib", "json", "re", "typing"}
    allowed_private = {
        "_worker_execution_semantic_values",
        "_development_pre_execution_plan_disposition_contracts",
        "_cognitive_proposal_row_values", "_development_effect_row_values",
        "_development_program_row_values", "_development_decision_row_values",
        "persistence_contracts",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed_std for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.level == 1 and node.module in allowed_private or (
                node.module == "__future__" and node.level == 0)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"now", "utcnow", "time", "monotonic",
                                          "open", "connect", "run", "Popen"}
    assert "__all__: tuple[str, ...] = ()" in SOURCE.read_text()


def test_privacy_sentinels_and_error_content_free() -> None:
    cls = b1.RW0RemoteHostReadinessObservationV1
    payload = mapping_for(cls)
    for forbidden in ("hostname", "ip_address", "endpoint", "host_key",
                      "username", "bearer_token", "credential_secret",
                      "absolute_path", "stdout", "transcript", "provider_session"):
        with pytest.raises(b1.RW0PhaseValueError) as caught:
            bounded = dict(payload)
            del bounded["observation_ref"]
            bounded[forbidden] = "SENTINEL-PRIVATE"
            cls.from_mapping(bounded)
        assert caught.value.reason == "privacy_forbidden_material"
        assert "SENTINEL-PRIVATE" not in str(caught.value)
        assert "SENTINEL-PRIVATE" not in repr(caught.value)
        assert caught.value.__cause__ is None
    value = cls.from_mapping(payload)
    assert "ref-safe-host-correlation-ref" not in repr(value)
    assert "ref-safe-host-correlation-ref" not in str(value)


def _assert_no_hidden_runtime_or_identity_shortcut(source: str) -> None:
    tree = ast.parse(source)
    forbidden_calls = {"eval", "exec", "compile", "__import__", "open"}
    forbidden_attributes = {
        "open", "connect", "run", "Popen", "set_int_max_str_digits",
        "import_module", "getenv", "system", "now", "utcnow",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attributes
        if isinstance(node, ast.Compare) and any(isinstance(op, ast.Is) for op in node.ops):
            names = {member.id for member in (node.left, *node.comparators)
                     if isinstance(member, ast.Name)}
            assert names != {"current_effect_fence", "author_effect_fence"}


def test_private_source_forbids_runtime_calls_and_fence_identity_shortcut() -> None:
    source = SOURCE.read_text()
    _assert_no_hidden_runtime_or_identity_shortcut(source)
    for mutation in (
        "\nimport os\nos.system('forbidden')\n",
        "\nimport sys\nsys.set_int_max_str_digits(0)\n",
        "\ndef bad(current_effect_fence, author_effect_fence):\n"
        "    return current_effect_fence is author_effect_fence\n",
    ):
        with pytest.raises(AssertionError):
            _assert_no_hidden_runtime_or_identity_shortcut(source + mutation)



def _assert_cardinality_precedes_caller_traversal(source: str) -> None:
    tree = ast.parse(source)
    helper = next(node for node in tree.body
                  if isinstance(node, ast.FunctionDef) and node.name == "_closed_mapping")
    # Test-owned structural oracle: an exact-type guard, then an O(1) size
    # rejection, before even aliasing or passing the caller mapping elsewhere.
    expected_type = ast.parse("type(payload) is not dict", mode="eval").body
    expected_size = ast.parse("len(payload) > len(fields)", mode="eval").body
    first, guard = helper.body[:2]
    assert isinstance(first, ast.If) and ast.dump(first.test) == ast.dump(expected_type)
    assert isinstance(guard, ast.If) and ast.dump(guard.test) == ast.dump(expected_size)
    assert len(guard.body) == 1 and not guard.orelse
    rejection = guard.body[0]
    assert isinstance(rejection, ast.Expr) and isinstance(rejection.value, ast.Call)
    call = rejection.value
    assert isinstance(call.func, ast.Name) and call.func.id == "_fail"
    assert [ast.dump(arg) for arg in call.args] == [
        ast.dump(ast.Constant("unknown_field")), ast.dump(ast.Name(id="label", ctx=ast.Load()))]
    # No caller sort, copy, or collection materialization is part of closure.
    for node in ast.walk(helper):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"sorted", "list", "tuple", "set", "dict"}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"sort", "copy", "keys", "items"}


def test_fourth_closed_mapping_cardinality_precedes_caller_traversal() -> None:
    _assert_cardinality_precedes_caller_traversal(SOURCE.read_text())


def test_fourth_all_eight_constructors_use_common_closed_mapping(monkeypatch) -> None:
    classes = (
        b1.RW0PhaseEntryBasisV1, b1.RW0AuthorityVerificationObservationV1,
        b1.RW0SubordinateAuthorizationProposalV1, b1.RW0CustodyAvailabilityObservationV1,
        b1.RW0RetrievalCapabilityEventObservationV1, b1.RW0RemoteHostReadinessObservationV1,
        b1.RW0EffectHostQualificationV1, b1.RW0TerminalOutcomeV1,
    )
    original = b1._closed_mapping
    seen = []
    def measured(payload, fields, label):
        seen.append((payload, fields, label))
        return original(payload, fields, label)
    monkeypatch.setattr(b1, "_closed_mapping", measured)
    for cls in classes:
        seen.clear()
        payload = mapping_for(cls)
        assert cls.from_mapping.__func__ is b1._B1Value.from_mapping.__func__
        assert cls.from_mapping(payload) is not None
        assert sum(item[0] is payload for item in seen) == 1
        assert seen[0] == (payload, cls._FIELDS, cls.__name__)
