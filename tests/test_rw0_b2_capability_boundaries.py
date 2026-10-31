from __future__ import annotations

import ast
import hashlib
import importlib.util
import stat
import sys
import types
from pathlib import Path

import pytest
from test_rw0_c2_bootstrap_acceptance_guard_semantic_contract import (
    _rw0_c2_current_drift_predecessor,
)

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
# Exact Capability-stage prose remains historical where it says C2 physical
# persistence is future. The current C2 status is checked separately below.
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
    ('P09', 'tests/test_c2b2_development_row_value_boundaries.py', 18232, 'd23abee15a3284674f0f7cf3a89fb5a9813fec1527b6904784b16e2602a71ae7',
     ('dependency_schema_migration',), 'protected C2B2 schema controls'),
    ('P10', 'tests/test_codex_agent_config.py', 1082, '0691c90c0178632a793a93595ba344169fb9b9669de155939fb4873db2f0d3ee',
     ('authority_non_effect',), 'protected Codex configuration'),
    ('P11', 'AGENTS.md', 71265, '1e1159352c56f668bc6a43d3a03124e1db33b60fb0b96aca62b17409c473816e',
     ('authority_non_effect',), 'protected repository governance'),
    ('P12', 'README.md', 48578, 'd39ed1289dd0d4305ea0744a12186d12b2e3ecdafdfd991ff9e838b9764ec8e2',
     ('authority_non_effect',), 'protected public claims'),
    ('P13', '.docs/software-development-progression-boundary.md', 28654, 'b8761655ee42512c0e77ab8c774c2b2d3d8f9ac36a9bd0c74872ad4bf2994419',
     ('state_store_writer_session',), 'protected progression authority'),
)


_P0_PROTECTED_APPEND = {
    'AGENTS.md': (644, '5a6268e7a6a848cf638e5092633d8e773bdf5b9d12498f5deb92aa9119523923',
                  b'<!-- RW0_C2_P0_PHYSICAL_CANDIDATE_BEGIN -->'),
    'README.md': (470, '07d99f5eab07a2d57d39a8ce5836ae062b523b2cdfc89c6d2c87f29a5d4bed6e',
                  b'<!-- RW0_C2_P0_PHYSICAL_CANDIDATE_BEGIN -->'),
}
_P1_PROTECTED_APPEND = {
    'AGENTS.md': (837, '733268376667429162a6b5a62e8b1a2a695a271e695c3cda5869825e49bd4ede',
                  b'<!-- RW0_C2_P1_PHYSICAL_CANDIDATE_BEGIN -->'),
    'README.md': (772, 'aa49da5e056b8dca34a772d8d7c4da4ba5525037d9a2b5517bd8f673566eb367',
                  b'<!-- RW0_C2_P1_PHYSICAL_CANDIDATE_BEGIN -->'),
}

_RW0_C2_LOCAL_STATUS_DOCUMENT_IDENTITIES = {
    'AGENTS.md': ((74410, 'c8ccf0552265d172a659a30be898fffd35cc70fad4821a350c3a9bf00e8f6b5d'),
                  (1664, '35b0ef1755c05f0a58ca6b073dcfcbacb333d2a78e0725e9d72012b2aa725f03')),
    'README.md': ((50883, '97af30802aea371b231e6509df62743006218065b3decbeb3bcc3db94df98981'),
                  (1063, '9a10331a1876103db243e8bc7d4abc8a5c876bb00a7fea9abb4ab505a42dad55')),
}

# The normal terminal candidate is a later bounded current successor. Peel it
# only after authenticating its complete bytes, then retain the old P09/P11/P13
# identities and all of their historical mutation oracles unchanged.
_RW0_NORMAL_TERMINAL_CURRENT_IDENTITIES = {
    'AGENTS.md': ((75552, '4d947ee8f6b20e40f6f20755ae3a28fd5603ca99dda97cb436fa35dd0db7c482'),
                  (1142, '84f8d8ea0a360c9ed20ec654b0b6f6abf58578e2f39a3395f312ad4ea13a8110')),
    'README.md': ((51873, 'b1fff34a97decde7e14eb8f346b3568aee97cb539f7da1e9d4f7f2e9aab9f96f'),
                  (990, '58d4e8e08df9f7cc6ee93722a25292f4f9c4d84ebc21a8fa4d7d65e74edc988a')),
    '.docs/software-development-progression-boundary.md': (
        (29615, 'd76f13ace3759ed6f7dc586142254b4aac092e8a177adad1b0435f96329aca92'),
        (961, '7c9cbc5f08da2e653823990937fcd2fce8eade9262cb464a920a0974901ae409')),
}
_RW0_NORMAL_TERMINAL_P09_IDENTITY = (19320, '15bd748914eb55f3427d02cf53eeace7529ec7812b883352e2f33f3577aaecad')
_RW0_NORMAL_TERMINAL_P09_ADDITION = b'''        "_rw0_terminal_head_witness.py":{\n            "_development_effect_row_values",\n            "_development_program_row_values",\n        },\n        "_rw0_terminal_outcome_plan.py":{\n            "_development_decision_row_values",\n        },\n        "_sqlite_rw0_terminal_outcome.py":{\n            "_development_decision_row_values",\n            "_development_program_row_values",\n        },\n'''


# Exact local-commit status successor to the three bounded capability docs.
_RW0_LOCAL_TERMINAL_CAPABILITY_IDENTITIES = {
    'AGENTS.md': (78298, '798429772e14d564701f93be43e8bc2da23893f05f4f99abc2f3a040e696e8c7'),
    'README.md': (54619, 'e54ea88e20143f0b1eaf612388adb31f8f5db63c9a5901db606a5641fa899f3f'),
    '.docs/software-development-progression-boundary.md': (32361, 'ff4bf801de9101892a28ffb992d4ad620ab38065097d95e24cb17b33e35d4df7'),
}
_RW0_LOCAL_TERMINAL_CAPABILITY_SUFFIX = (2746, '123d4c562ecc39e492aa6636912abb2423b00a5de91a7e0858496d8f4d06064c')

def _peel_rw0_normal_terminal_successor(relative_path: str, payload: bytes) -> bytes:
    if relative_path == 'tests/test_c2b2_development_row_value_boundaries.py':
        if ((len(payload), hashlib.sha256(payload).hexdigest()) != _RW0_NORMAL_TERMINAL_P09_IDENTITY
                or payload.count(_RW0_NORMAL_TERMINAL_P09_ADDITION) != 1):
            raise AssertionError('P09:terminal_successor_identity')
        return payload.replace(_RW0_NORMAL_TERMINAL_P09_ADDITION, b'', 1)
    if relative_path in _RW0_LOCAL_TERMINAL_CAPABILITY_IDENTITIES:
        current = _RW0_LOCAL_TERMINAL_CAPABILITY_IDENTITIES[relative_path]
        size, digest = _RW0_LOCAL_TERMINAL_CAPABILITY_SUFFIX
        begin = b'\n<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->\n'
        end = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
        if (payload.count(begin) != 1 or payload.count(end) != 1
                or not payload.endswith(end) or not payload[-size:].startswith(begin)
                or hashlib.sha256(payload[-size:]).hexdigest() != digest
                or (len(payload), hashlib.sha256(payload).hexdigest()) != current):
            raise AssertionError(relative_path + ':terminal_successor_identity:local_commit')
        predecessor = payload[:-size]
        if ((len(predecessor), hashlib.sha256(predecessor).hexdigest()) !=
                _RW0_NORMAL_TERMINAL_CURRENT_IDENTITIES[relative_path][0]):
            raise AssertionError(relative_path + ':terminal_successor_identity:local_predecessor')
        payload = predecessor
    if relative_path not in _RW0_NORMAL_TERMINAL_CURRENT_IDENTITIES:
        return payload
    current, suffix = _RW0_NORMAL_TERMINAL_CURRENT_IDENTITIES[relative_path]
    begin = b'\n<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->\n'
    end = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->\n'
    size, digest = suffix
    if ((len(payload), hashlib.sha256(payload).hexdigest()) != current
            or len(payload) < size or not payload.endswith(end)
            or payload.count(begin) != 1 or payload.count(end) != 1
            or not payload[-size:].startswith(begin)
            or hashlib.sha256(payload[-size:]).hexdigest() != digest):
        raise AssertionError(relative_path + ':terminal_successor_identity')
    return payload[:-size]


def _peel_rw0_c2_local_status(relative_path: str, payload: bytes) -> bytes:
    current, suffix = _RW0_C2_LOCAL_STATUS_DOCUMENT_IDENTITIES[relative_path]
    marker = b'\n<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->\n'
    end = b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
    size, digest = suffix
    if ((len(payload), hashlib.sha256(payload).hexdigest()) != current
            or len(payload) < size or not payload.endswith(end)
            or payload.count(marker) != 1 or payload.count(end) != 1
            or hashlib.sha256(payload[-size:]).hexdigest() != digest
            or not payload[-size:].startswith(marker)):
        raise AssertionError(relative_path + ':local_status_successor_identity')
    return payload[:-size]


def _protected_historical_bytes(relative_path: str, payload: bytes) -> bytes:
    """Verify bounded successors, then retain each old exact identity oracle."""
    payload = _peel_rw0_normal_terminal_successor(relative_path, payload)
    if relative_path == 'tests/test_c2b2_development_row_value_boundaries.py':
        if (len(payload), hashlib.sha256(payload).hexdigest()) != _P09_RW0_C2_P1_SUCCESSOR_IDENTITY:
            raise AssertionError('P09:rw0_c2_p1_successor_identity')
        if payload.count(_P09_RW0_C2_P1_ADDITION) != 1:
            raise AssertionError('P09:rw0_c2_p1_successor_identity')
        return payload.replace(_P09_RW0_C2_P1_ADDITION, b'', 1)
    if relative_path not in _P0_PROTECTED_APPEND:
        return payload
    payload = _peel_rw0_c2_local_status(relative_path, payload)
    p1_size, p1_digest, p1_marker = _P1_PROTECTED_APPEND[relative_path]
    if (len(payload) < p1_size or payload[-p1_size:].count(p1_marker) != 1
            or hashlib.sha256(payload[-p1_size:]).hexdigest() != p1_digest):
        raise AssertionError(relative_path + ':p1_successor_identity')
    payload = payload[:-p1_size]
    size, digest, marker = _P0_PROTECTED_APPEND[relative_path]
    if (len(payload) < size or payload[-size:].count(marker) != 1
            or hashlib.sha256(payload[-size:]).hexdigest() != digest):
        raise AssertionError(relative_path + ':p0_successor_identity')
    return payload[:-size]


@pytest.mark.parametrize('relative_path', (
    'AGENTS.md', 'README.md',
    '.docs/software-development-progression-boundary.md',
    'tests/test_c2b2_development_row_value_boundaries.py',
))
def test_rw0_normal_terminal_successor_reconstructs_protected_predecessor(
    relative_path: str,
) -> None:
    current = (ROOT / relative_path).read_bytes()
    predecessor = _peel_rw0_normal_terminal_successor(relative_path, current)
    expected = {
        'AGENTS.md': _RW0_C2_LOCAL_STATUS_DOCUMENT_IDENTITIES['AGENTS.md'][0],
        'README.md': _RW0_C2_LOCAL_STATUS_DOCUMENT_IDENTITIES['README.md'][0],
        '.docs/software-development-progression-boundary.md': (
            28654, 'b8761655ee42512c0e77ab8c774c2b2d3d8f9ac36a9bd0c74872ad4bf2994419'),
        'tests/test_c2b2_development_row_value_boundaries.py': _P09_RW0_C2_P1_SUCCESSOR_IDENTITY,
    }[relative_path]
    assert (len(predecessor), hashlib.sha256(predecessor).hexdigest()) == expected
    with pytest.raises(AssertionError, match='terminal_successor_identity'):
        _peel_rw0_normal_terminal_successor(relative_path, current + b'X')


def _p11_historical_bytes() -> bytes:
    return _protected_historical_bytes('AGENTS.md', (ROOT / 'AGENTS.md').read_bytes())

# P09's one post-D2 reader-consumer addition is an exact successor to the
# protected C2B2 boundary oracle, not a replacement of its historical rules.
_P09_POST_D2_PREDECESSOR_IDENTITY = (17972, 'f2a7089748f39dc8c40a932ac770edd3ffa7f8ea581b053af101dfda8100c830')
_P09_POST_D2_SUCCESSOR_IDENTITY = (18232, 'd23abee15a3284674f0f7cf3a89fb5a9813fec1527b6904784b16e2602a71ae7')
_P09_RW0_C2_P1_SUCCESSOR_IDENTITY = (18923, 'a0c6972f3f51563c6a735865d060ed738fd623f8084f87e90586dd5781bbcf2f')
_P09_POST_D2_ADDITION = b'''        # The native Section 41 checked reader consumes only the decision
        # row adapter for retained D2 bound-effect mutation receipts.
        "_sqlite_section41_post_execution_proposal.py":{
            "_development_decision_row_values",
        },
'''
_P09_POST_D2_FOLLOWING = b'        "_rw0_phase_entry_semantic_values.py":{\n'
_P09_RW0_C2_P1_ADDITION = b'''        # P1 consumes existing typed 0002 values inside its private plan,
        # physical reader, and writer; these are not public row-value APIs.
        "_rw0_c2_progression_contracts.py":{"_development_program_row_values"},
        "_rw0_c2_progression_plan.py":{
            "_development_decision_row_values",
            "_development_program_row_values",
            "_development_row_value_support",
        },
        "_rw0_c2_progression_rows.py":{"_development_program_row_values"},
        "_sqlite_rw0_c2_progression.py":{
            "_development_decision_row_values",
            "_development_effect_row_values",
            "_development_program_row_values",
        },
'''


def test_p09_exact_post_d2_reader_consumer_successor_preserves_predecessor() -> None:
    current = _peel_rw0_normal_terminal_successor(
        'tests/test_c2b2_development_row_value_boundaries.py',
        (ROOT / 'tests/test_c2b2_development_row_value_boundaries.py').read_bytes())
    assert (len(current), hashlib.sha256(current).hexdigest()) == _P09_RW0_C2_P1_SUCCESSOR_IDENTITY
    assert current.count(_P09_RW0_C2_P1_ADDITION) == 1
    post_d2 = current.replace(_P09_RW0_C2_P1_ADDITION, b'', 1)
    assert (len(post_d2), hashlib.sha256(post_d2).hexdigest()) == _P09_POST_D2_SUCCESSOR_IDENTITY
    assert post_d2.count(_P09_POST_D2_ADDITION) == 1
    assert post_d2.count(_P09_POST_D2_ADDITION + _P09_POST_D2_FOLLOWING) == 1
    predecessor = post_d2.replace(_P09_POST_D2_ADDITION, b'', 1)
    assert (len(predecessor), hashlib.sha256(predecessor).hexdigest()) == _P09_POST_D2_PREDECESSOR_IDENTITY


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
    payload = _protected_historical_bytes(relative_path, payload)
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
    for relative in (
        '.docs/rw0-remote-worker-contact-phase-entry.md',
        '.docs/durable-state-model.md',
        '.docs/worker-execution-boundary.md',
    ):
        _rw0_c2_current_drift_predecessor(
            relative, (ROOT / relative).read_bytes())

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
         'replacement_identity': (71265,
                                  '1e1159352c56f668bc6a43d3a03124e1db33b60fb0b96aca62b17409c473816e'),
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
         'replacement_identity': (48578,
                                  'd39ed1289dd0d4305ea0744a12186d12b2e3ecdafdfd991ff9e838b9764ec8e2'),
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
        data = _protected_historical_bytes(path, (ROOT / path).read_bytes())
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


# P11 cumulative local commit is an exact append-only successor to Unit 2.
_P11_LOCAL_COMMIT_PREDECESSOR_IDENTITY = (69392, 'a23fe109833ddc4ee70f526826058c503dcab93438047e2e68365819bfec3171')
_P11_LOCAL_COMMIT_SUCCESSOR_IDENTITY = (71265, '1e1159352c56f668bc6a43d3a03124e1db33b60fb0b96aca62b17409c473816e')
_P11_LOCAL_COMMIT_NEW = b'''
<!-- POST_D2_CUMULATIVE_LOCAL_COMMIT_CURRENT_SUCCESSOR_BEGIN -->
### Post-D2 cumulative local-commit status successor

The bounded post-D2 implementation in the exact sealed tree
`3965cd3d1d3e28b43c9bc3709058c2524bad369d` was independently reviewed
for a separately governed commit gate. That gate locally committed those
bytes as `66ee79132501e636d848ff8578fb674a208d6ac5`, reauthenticated all
299 committed blobs and Git modes, and recorded 9,295 collected and 9,295
passing tests, zero failures, errors, or skips, and three known Python 3.13
fork deprecation warnings. The earlier Unit 2 pending-review sentence remains
historical candidate-stage evidence and is superseded only for review and
local-commit status.

The gate performed no push, PR, merge, publication, deployment, or product
effect. This is a historical local-gate statement, not a live remote-ref or
publication claim. Git objects and refs remain authoritative for current
commit and publication truth. Audit, validation, provenance, reports, and
status text remain evidence, not Coordinator durable authority or permission
to perform effects. The artifact-only audit did not certify live Git state;
the gate proves only its prospective opening-to-commit interval. Earlier
raw-index and diagnostic-ref provenance gaps remain unresolved history. F03
remains a nonblocking private-constructor observation; F2 and qualified
F3/F6/F7 findings, cross-host clock ordering, and future live concerns are
not claimed closed.

This implementation adds no live custody, physical C2 decision or acceptance,
terminal outcome, executable permission, production provider or worker
readiness, ES or Bridge route, product Git authority, service, scheduler, or
autonomous loop. The original D2 entry and Unit 2 behavioral boundaries above
remain unchanged.
<!-- POST_D2_CUMULATIVE_LOCAL_COMMIT_CURRENT_SUCCESSOR_END -->
'''


def _p11_reconstruct_exact_local_commit_predecessor(candidate: bytes) -> bytes:
    begin = b'<!-- POST_D2_CUMULATIVE_LOCAL_COMMIT_CURRENT_SUCCESSOR_BEGIN -->'
    end = b'<!-- POST_D2_CUMULATIVE_LOCAL_COMMIT_CURRENT_SUCCESSOR_END -->'
    if (type(candidate) is not bytes or candidate.count(_P11_LOCAL_COMMIT_NEW) != 1
            or candidate.count(begin) != 1 or candidate.count(end) != 1):
        raise AssertionError('p11:local_commit_successor_count')
    if not candidate.endswith(_P11_LOCAL_COMMIT_NEW):
        raise AssertionError('p11:local_commit_successor_context')
    predecessor = candidate[:-len(_P11_LOCAL_COMMIT_NEW)]
    if (len(predecessor), hashlib.sha256(predecessor).hexdigest()) != _P11_LOCAL_COMMIT_PREDECESSOR_IDENTITY:
        raise AssertionError('p11:local_commit_predecessor_identity')
    if not predecessor.endswith(b'<!-- POST_D2_UNIT2_CURRENT_SUCCESSOR_END -->\n'):
        raise AssertionError('p11:local_commit_predecessor_context')
    compact = b' '.join(_P11_LOCAL_COMMIT_NEW.split())
    required = (
        b'3965cd3d1d3e28b43c9bc3709058c2524bad369d',
        b'66ee79132501e636d848ff8578fb674a208d6ac5',
        b'independently reviewed', b'299 committed blobs and Git modes',
        b'9,295 collected and 9,295 passing tests',
        b'no push, PR, merge, publication, deployment, or product effect',
        b'not a live remote-ref', b'Git objects and refs remain authoritative',
        b'not Coordinator durable authority or permission to perform effects',
        b'no live custody, physical C2 decision or acceptance',
        b'no live custody, physical C2 decision or acceptance, terminal outcome, executable permission',
        b'production provider or worker readiness', b'product Git authority',
        b'service, scheduler, or autonomous loop',
    )
    if any(fragment not in compact for fragment in required):
        raise AssertionError('p11:local_commit_semantics')
    return predecessor


def test_p11_exact_local_commit_successor_reconstructs_full_history() -> None:
    current = _p11_historical_bytes()
    assert (len(current), hashlib.sha256(current).hexdigest()) == _P11_LOCAL_COMMIT_SUCCESSOR_IDENTITY
    unit2 = _p11_reconstruct_exact_local_commit_predecessor(current)
    assert unit2 + _P11_LOCAL_COMMIT_NEW == current
    native = _p11_reconstruct_exact_unit2_predecessor(unit2)
    d2 = _p11_reconstruct_exact_post_d2_predecessor(native)
    historical = _p11_reconstruct_exact_status_predecessor(d2)
    assert (len(historical), hashlib.sha256(historical).hexdigest()) == _P11_STATUS_PREDECESSOR_IDENTITY


@pytest.mark.parametrize(('case', 'boundary'), (
    ('missing', 'p11:local_commit_successor_count'),
    ('duplicate', 'p11:local_commit_successor_count'),
    ('moved', 'p11:local_commit_successor_context'),
    ('semantic_change', 'p11:local_commit_successor_count'),
    ('outside_change', 'p11:local_commit_predecessor_identity'),
))
def test_p11_local_commit_successor_rejects_exact_mutants(case: str, boundary: str) -> None:
    current = _p11_historical_bytes()
    predecessor = _p11_reconstruct_exact_local_commit_predecessor(current)
    if case == 'missing':
        changed = predecessor
    elif case == 'duplicate':
        changed = current + _P11_LOCAL_COMMIT_NEW
    elif case == 'moved':
        changed = _P11_LOCAL_COMMIT_NEW + predecessor
    elif case == 'semantic_change':
        changed = current.replace(b'no push, PR, merge', b'did push, PR, merge', 1)
    else:
        changed = current.replace(b'Coordinator cannot self-authorize',
                                  b'Coordinator cannoX self-authorize', 1)
    assert changed != current
    with pytest.raises(AssertionError, match='^' + boundary + '$'):
        _p11_reconstruct_exact_local_commit_predecessor(changed)


# P11 Unit 2 is an exact append-only successor to the 67,252-byte identity.
_P11_UNIT2_PREDECESSOR_IDENTITY = (67252, '24a17a3c87b92306837bf18e69e2d425919aa9c57f01a307d3fdb018a124c728')
_P11_UNIT2_SUCCESSOR_IDENTITY = (69392, 'a23fe109833ddc4ee70f526826058c503dcab93438047e2e68365819bfec3171')
_P11_UNIT2_NEW = b'''
<!-- POST_D2_UNIT2_CURRENT_SUCCESSOR_BEGIN -->
### Post-D2 Unit 2 bounded evidence successor

The current private offline D2 A path accepts exactly two Worker Wire observation
orders: `worker_started, worker_completed` and `worker_started,
candidate_captured, worker_completed`. The parent captures and verifies the
candidate capsule in either case; omission of the optional worker-authored
`candidate_captured` observation makes no claim that the parent did not capture
a candidate. `worker_completed` still carries no candidate or capsule
conditional fields. The checked C1 A families have exactly 13 or 14 members,
respectively, with rank sequences `(12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6,
12, 1)` and `(12, 12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)`. One private
layout resolver anchors role positions and reached prefixes to the actual D1
Wire result. Pure V40 reviewer separation binds the parent capsule, the
rank-13 worker-result candidate, and the review observation in both layouts;
only the three-observation layout reads a `candidate_captured.candidate_ref`.

A clean, reaped validator or reviewer child whose closed checking response is
invalid stops with `validator_evidence_invalid` or
`reviewer_evidence_invalid`, respectively. The returned handback retains the
exact prior checked prefix and child outcomes without admitting the bad
observation or launching a later child. Process failure, cleanup failure, and
programming faults retain their separate handling. The native Section 41 fresh
writer derives one command and canonical safe basis from the original open D2
run and requires complete equality before route probing or target writes.
Receipt-first historical replay and checked readback use the persisted family
without rerunning children or requiring present process custody. The existing
three-observation command and safe-basis bytes remain unchanged.

This bounded implementation is pending independent review. It adds no C2
decision, acceptance, executable permission, live provider or ES route,
production worker, Git effect, publication, or autonomous loop.
<!-- POST_D2_UNIT2_CURRENT_SUCCESSOR_END -->
'''


def _p11_reconstruct_exact_unit2_predecessor(candidate: bytes) -> bytes:
    if type(candidate) is not bytes or candidate.count(_P11_UNIT2_NEW) != 1:
        raise AssertionError('p11:unit2_successor_count')
    if not candidate.endswith(_P11_UNIT2_NEW):
        raise AssertionError('p11:unit2_successor_context')
    predecessor = candidate[:-len(_P11_UNIT2_NEW)]
    if (len(predecessor), hashlib.sha256(predecessor).hexdigest()) != _P11_UNIT2_PREDECESSOR_IDENTITY:
        raise AssertionError('p11:unit2_predecessor_identity')
    if not predecessor.endswith(b'<!-- POST_D2_NATIVE_PROPOSAL_ADMISSION_CURRENT_SUCCESSOR_END -->\n'):
        raise AssertionError('p11:unit2_predecessor_context')
    required = (
        b'worker_started, worker_completed', b'candidate_captured',
        b'validator_evidence_invalid', b'reviewer_evidence_invalid',
        b'original open D2', b'Receipt-first historical replay',
        b'no C2', b'pending independent review',
    )
    if any(marker not in _P11_UNIT2_NEW for marker in required):
        raise AssertionError('p11:unit2_semantics')
    return predecessor


def test_p11_exact_unit2_successor_reconstructs_all_predecessors() -> None:
    current = _p11_reconstruct_exact_local_commit_predecessor(_p11_historical_bytes())
    assert (len(current), hashlib.sha256(current).hexdigest()) == _P11_UNIT2_SUCCESSOR_IDENTITY
    prior = _p11_reconstruct_exact_unit2_predecessor(current)
    assert prior + _P11_UNIT2_NEW == current
    d2 = _p11_reconstruct_exact_post_d2_predecessor(prior)
    assert _p11_reconstruct_exact_status_predecessor(d2)


@pytest.mark.parametrize(('case', 'boundary'), (
    ('missing', 'p11:unit2_successor_count'),
    ('duplicate', 'p11:unit2_successor_count'),
    ('moved', 'p11:unit2_successor_context'),
    ('semantic_change', 'p11:unit2_successor_count'),
    ('outside_change', 'p11:unit2_predecessor_identity'),
))
def test_p11_unit2_successor_rejects_exact_mutants(case: str, boundary: str) -> None:
    current = _p11_reconstruct_exact_local_commit_predecessor(_p11_historical_bytes())
    predecessor = _p11_reconstruct_exact_unit2_predecessor(current)
    if case == 'missing':
        changed = predecessor
    elif case == 'duplicate':
        changed = current + _P11_UNIT2_NEW
    elif case == 'moved':
        changed = _P11_UNIT2_NEW + predecessor
    elif case == 'semantic_change':
        changed = current.replace(b'no candidate or capsule', b'candidate or capsule', 1)
    else:
        changed = current.replace(b'Coordinator cannot self-authorize',
                                  b'Coordinator cannoX self-authorize', 1)
    assert changed != current
    with pytest.raises(AssertionError, match='^' + boundary + '$'):
        _p11_reconstruct_exact_unit2_predecessor(changed)


# P11's native post-D2 addition is a third, exact, append-only successor.
_P11_POST_D2_PREDECESSOR_IDENTITY = (65275, '1137167c50bbc8c302f126bea89a7f1032555664b278db66d5aae4feedd79cbc')
_P11_POST_D2_SUCCESSOR_IDENTITY = (67252, '24a17a3c87b92306837bf18e69e2d425919aa9c57f01a307d3fdb018a124c728')
_P11_POST_D2_NEW = b'''
<!-- POST_D2_NATIVE_PROPOSAL_ADMISSION_CURRENT_SUCCESSOR_BEGIN -->
### Post-D2 native proposal admission successor

The adjacent private post-D2 offline continuation calls the original D2 run
once, records one native Section 41 post-execution proposal/context/receipt
family in transaction A, checks the committed twelve owner rows in a fresh
guarded session, then uses a distinct C1 transaction B to admit exactly one
rank-15 member. Fresh guarded readback of both families feeds unchanged pure
V22 projection. The original D2 entry and `preadmission_ready` meaning remain
as documented above. The five model recommendations remain evidence only.

The current additive production catalog now ends at
`0005_section41_post_execution_proposal_family`, still at application
generation 2 with SQLite 3.37.0 minimum. Migration 0005 adds exactly two
immutable STRICT tables, four guards, no explicit index or seed, giving 64
user tables, 114 triggers, and five explicit indexes cumulatively. Existing
0004 states require explicit administrative migration before normal writer
admission; normal validation, acquisition and mutation do not auto-migrate.
Earlier current-tip and absent-0005 statements in this file describe the
historical D2/C1 tranches and are superseded only for this additive successor.

The owning contract is `.docs/section41-post-execution-proposal-family.md`,
incorporated by Section 41 in `.docs/c2b-durable-development-state.md`.
The proof retains only a closed safe basis, uses the original process-owned
temporary state, and provides read-only three-way recovery after uncertain A
or B commits. It adds no C2 decision, acceptance, terminal outcome, executable
permission, real custody, restart/clone recovery, live provider/worker, ES or
Bridge route, Git effect, publication, service, scheduler, or autonomous loop.
This source successor is not an independent audit or deployment assertion.
<!-- POST_D2_NATIVE_PROPOSAL_ADMISSION_CURRENT_SUCCESSOR_END -->
'''
_P11_POST_D2_PRE_CONTEXT = b'<!-- RW0_D2_CURRENT_STATUS_END -->\n'


def _p11_reconstruct_exact_post_d2_predecessor(candidate: bytes) -> bytes:
    if type(candidate) is not bytes or candidate.count(_P11_POST_D2_NEW) != 1:
        raise AssertionError('p11:post_d2_successor_count')
    if not candidate.endswith(_P11_POST_D2_NEW):
        raise AssertionError('p11:post_d2_successor_context')
    predecessor = candidate[:-len(_P11_POST_D2_NEW)]
    if not predecessor.endswith(_P11_POST_D2_PRE_CONTEXT):
        raise AssertionError('p11:post_d2_predecessor_context')
    if (len(predecessor), hashlib.sha256(predecessor).hexdigest()) != _P11_POST_D2_PREDECESSOR_IDENTITY:
        raise AssertionError('p11:post_d2_predecessor_identity')
    return predecessor


def test_p11_exact_native_post_d2_successor_reconstructs_integrated_predecessor() -> None:
    current = _p11_reconstruct_exact_unit2_predecessor(
        _p11_reconstruct_exact_local_commit_predecessor(_p11_historical_bytes())
    )
    assert (len(current), hashlib.sha256(current).hexdigest()) == _P11_POST_D2_SUCCESSOR_IDENTITY
    predecessor = _p11_reconstruct_exact_post_d2_predecessor(current)
    assert predecessor + _P11_POST_D2_NEW == current
    assert (len(predecessor), hashlib.sha256(predecessor).hexdigest()) == _P11_STATUS_SUCCESSOR_IDENTITY
    assert _p11_reconstruct_exact_status_predecessor(predecessor)
    assert b'0005_section41_post_execution_proposal_family' in _P11_POST_D2_NEW
    assert b'no C2 decision, acceptance, terminal outcome' in b' '.join(_P11_POST_D2_NEW.split())


@pytest.mark.parametrize(('case', 'boundary'), (
    ('missing', 'p11:post_d2_successor_count'),
    ('duplicate', 'p11:post_d2_successor_count'),
    ('moved', 'p11:post_d2_successor_context'),
    ('semantic_change', 'p11:post_d2_successor_count'),
    ('outside_change', 'p11:post_d2_predecessor_identity'),
))
def test_p11_native_post_d2_successor_rejects_exact_mutants(
    case: str, boundary: str,
) -> None:
    current = _p11_reconstruct_exact_unit2_predecessor(
        _p11_reconstruct_exact_local_commit_predecessor(_p11_historical_bytes())
    )
    predecessor = _p11_reconstruct_exact_post_d2_predecessor(current)
    if case == 'missing':
        changed = predecessor
    elif case == 'duplicate':
        changed = current + _P11_POST_D2_NEW
    elif case == 'moved':
        changed = _P11_POST_D2_NEW + predecessor
    elif case == 'semantic_change':
        changed = current.replace(b'five model recommendations remain evidence only',
                                  b'five model recommendations grant acceptance', 1)
    else:
        changed = current.replace(b'Coordinator cannot self-authorize',
                                  b'Coordinator cannoX self-authorize', 1)
    assert changed != current
    with pytest.raises(AssertionError, match='^' + boundary + '$'):
        _p11_reconstruct_exact_post_d2_predecessor(changed)


# P11's later D2 status-only successor is separate from the earlier bootstrap reset.
_P11_STATUS_PREDECESSOR_IDENTITY = (64142, 'ddf5485d88fc4604429a2b553643e3a8a80828002d17f7cfcb10cb935d018166')
_P11_STATUS_SUCCESSOR_IDENTITY = (65275, '1137167c50bbc8c302f126bea89a7f1032555664b278db66d5aae4feedd79cbc')
_P11_OLD_TOP = b'''RW0-D2 now contains a private offline implementation candidate continuing the
D1 capsule: two guarded validation/review bound effects, 14 checked C1 members,
separate fake validator/reviewer/model processes, nine-role model input, and one
typed transient preadmission handback. D2 does not own acceptance, Section 41
post-execution persistence, C1 rank-15 admission, a C2 decision writer,
production execution, or migration 0005. External-copy validation and
independent audit are separate gates; this source status grants neither. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
'''
_P11_NEW_TOP = b'''RW0-D2's bounded private offline D1-to-D2 implementation was independently
reviewed and introduced by commit `59621aa041a409c6ead27b74ffe25598c159e78e`. It continues
the D1 capsule with two guarded validation/review bound effects, 14 checked C1
members, separate fake validator/reviewer/model processes, exact nine-role
model input, and one typed transient preadmission handback. The guarded
Coordinator program, author-effect, Section 41 pre-execution selection, and
C1 paths retain durable authority. The local commit gate recorded no push, PR,
or merge; this records that gate, not live publication status. Git owns
committed object and ref truth. Audit, validation, provenance, and closeout
records are evidence, not Coordinator durable authority or permission to
perform effects. D2 adds no Section 41 post-execution proposal-family writer,
C1 rank-15 admission, physical C2 decision or terminal acceptance, migration
0005, live provider/Codex invocation, ES/Bridge route, production direct-local
adapter, product Git effect, or autonomous loop. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
'''
_P11_OLD_BOTTOM = b'''RW0-D2 has a private offline source candidate for bounded validation/review
evidence closure and one fake cognitive-review handback. Its current source
uses the D1 capsule, guarded Coordinator bound-effect and C1 paths, exact
nine-role input, and three separate D2 children. This successor supersedes the
D1 status sentence that placed D2 wholly in the future. It implements no
post-execution Section 41 proposal-family or C2 decision persistence, rank-15
admission, terminal acceptance, ES route, live provider, production adapter,
or migration 0005. External-copy validation and independent audit remain
pending. `.docs/rw0-d2-offline-evidence-and-review.md` is the detailed owner.
'''
_P11_NEW_BOTTOM = b'''RW0-D2's bounded private offline evidence and cognitive-review implementation
was independently reviewed and introduced by commit
`59621aa041a409c6ead27b74ffe25598c159e78e`. The D1 capsule remains the
author/checking boundary. Two guarded validation/review bound effects, 14
checked C1 members, three separate fake validator/reviewer/model processes,
exact nine-role input, and one typed transient preadmission handback form this
artificial proof. The guarded Coordinator program, author-effect, Section 41
pre-execution selection, and C1 paths retain durable authority. The local
commit gate recorded no push, PR, or merge; this records that gate, not live
publication status. Git owns committed object and ref truth. Audit,
validation, provenance, and closeout records are evidence, not Coordinator
durable authority or effect permission. This successor supersedes only the D1
sentence placing D2 closure in the future. It adds no Section 41 post-execution
proposal-family writer, C1 rank-15 admission, physical C2 decision or terminal
acceptance, migration 0005, live provider/Codex invocation, ES/Bridge route,
production direct-local adapter, product Git handler, or autonomous loop.
`preadmission_ready` is not acceptance. The detailed owner is
`.docs/rw0-d2-offline-evidence-and-review.md`.
'''
_P11_TOP_CONTEXT_BEFORE = b'''truth, or hidden program state.

'''
_P11_TOP_CONTEXT_AFTER = b'''
The bounded operational-change progression target is separate, target-only
'''
_P11_BOTTOM_CONTEXT_BEFORE = b'''<!-- RW0_D2_CURRENT_STATUS_BEGIN -->
'''
_P11_BOTTOM_CONTEXT_AFTER = b'''<!-- RW0_D2_CURRENT_STATUS_END -->
'''


def _p11_reconstruct_exact_status_predecessor(candidate: bytes) -> bytes:
    if type(candidate) is not bytes:
        raise AssertionError('p11:status_candidate_type')
    top = _P11_TOP_CONTEXT_BEFORE + _P11_NEW_TOP + _P11_TOP_CONTEXT_AFTER
    bottom = _P11_BOTTOM_CONTEXT_BEFORE + _P11_NEW_BOTTOM + _P11_BOTTOM_CONTEXT_AFTER
    if candidate.count(_P11_NEW_TOP) != 1 or candidate.count(top) != 1:
        raise AssertionError('p11:top_status_context')
    if candidate.count(_P11_NEW_BOTTOM) != 1 or candidate.count(bottom) != 1:
        raise AssertionError('p11:bottom_status_context')
    if candidate.index(top) + len(top) > candidate.index(bottom):
        raise AssertionError('p11:status_order')
    predecessor = candidate.replace(_P11_NEW_TOP, _P11_OLD_TOP, 1).replace(
        _P11_NEW_BOTTOM, _P11_OLD_BOTTOM, 1
    )
    if (len(predecessor), hashlib.sha256(predecessor).hexdigest()) != _P11_STATUS_PREDECESSOR_IDENTITY:
        raise AssertionError('p11:predecessor_identity')
    return predecessor


def test_p11_exact_d2_status_successor_reconstructs_historical_governance() -> None:
    current = _p11_reconstruct_exact_unit2_predecessor(
        _p11_reconstruct_exact_local_commit_predecessor(_p11_historical_bytes())
    )
    historical_current = _p11_reconstruct_exact_post_d2_predecessor(current)
    assert (len(historical_current), hashlib.sha256(historical_current).hexdigest()) == _P11_STATUS_SUCCESSOR_IDENTITY
    predecessor = _p11_reconstruct_exact_status_predecessor(historical_current)
    assert predecessor.count(_P11_OLD_TOP) == predecessor.count(_P11_OLD_BOTTOM) == 1
    assert predecessor.replace(_P11_OLD_TOP, _P11_NEW_TOP, 1).replace(
        _P11_OLD_BOTTOM, _P11_NEW_BOTTOM, 1
    ) == historical_current
    for span in (_P11_NEW_TOP, _P11_NEW_BOTTOM):
        assert b'59621aa041a409c6ead27b74ffe25598c159e78e' in span
        assert b'commit gate recorded no push, PR, or merge' in b' '.join(span.split())
        assert b'not live publication status' in b' '.join(span.split())
        assert b'Git owns committed object and ref truth' in b' '.join(span.split())
        assert b'not Coordinator durable authority' in b' '.join(span.split())
        assert b'C1 rank-15 admission' in b' '.join(span.split())


@pytest.mark.parametrize('case,boundary', (
    ('fully_stale', 'p11:top_status_context'),
    ('only_top_new', 'p11:bottom_status_context'),
    ('only_bottom_new', 'p11:top_status_context'),
    ('missing_top', 'p11:top_status_context'),
    ('missing_bottom', 'p11:bottom_status_context'),
    ('duplicate_top', 'p11:top_status_context'),
    ('duplicate_bottom', 'p11:bottom_status_context'),
    ('reordered', 'p11:top_status_context'),
    ('wrong_commit', 'p11:top_status_context'),
    ('missing_commit', 'p11:bottom_status_context'),
    ('product_authority_overclaim', 'p11:top_status_context'),
    ('acceptance_overclaim', 'p11:bottom_status_context'),
    ('unrelated_byte', 'p11:predecessor_identity'),
    ('authority_sentence_byte', 'p11:predecessor_identity'),
    ('nonstatus_scope_sentence', 'p11:top_status_context'),
))
def test_p11_status_successor_rejects_bounded_mutations(case: str, boundary: str) -> None:
    current = _p11_reconstruct_exact_post_d2_predecessor(
        _p11_reconstruct_exact_unit2_predecessor(
        _p11_reconstruct_exact_local_commit_predecessor(_p11_historical_bytes())
    )
    )
    assert _p11_reconstruct_exact_status_predecessor(current)
    if case == 'fully_stale':
        changed = current.replace(_P11_NEW_TOP, _P11_OLD_TOP, 1).replace(
            _P11_NEW_BOTTOM, _P11_OLD_BOTTOM, 1)
        assert (len(changed), hashlib.sha256(changed).hexdigest()) == _P11_STATUS_PREDECESSOR_IDENTITY
    elif case == 'only_top_new':
        changed = current.replace(_P11_NEW_BOTTOM, _P11_OLD_BOTTOM, 1)
    elif case == 'only_bottom_new':
        changed = current.replace(_P11_NEW_TOP, _P11_OLD_TOP, 1)
    elif case == 'missing_top':
        changed = current.replace(_P11_NEW_TOP, b'', 1)
    elif case == 'missing_bottom':
        changed = current.replace(_P11_NEW_BOTTOM, b'', 1)
    elif case == 'duplicate_top':
        changed = current.replace(_P11_NEW_TOP, _P11_NEW_TOP * 2, 1)
        assert changed.count(_P11_NEW_TOP) == 2
    elif case == 'duplicate_bottom':
        changed = current.replace(_P11_NEW_BOTTOM, _P11_NEW_BOTTOM * 2, 1)
        assert changed.count(_P11_NEW_BOTTOM) == 2
    elif case == 'reordered':
        placeholder = b'P11_UNIQUE_TEMPORARY_SWAP_ANCHOR'
        assert placeholder not in current
        changed = current.replace(_P11_NEW_TOP, placeholder, 1).replace(
            _P11_NEW_BOTTOM, _P11_NEW_TOP, 1).replace(placeholder, _P11_NEW_BOTTOM, 1)
        assert changed.count(_P11_NEW_TOP) == changed.count(_P11_NEW_BOTTOM) == 1
    elif case == 'wrong_commit':
        changed = current.replace(
            _P11_NEW_TOP, _P11_NEW_TOP.replace(b'59621aa041a409c6ead27b74ffe25598c159e78e',
                                              b'69621aa041a409c6ead27b74ffe25598c159e78e', 1), 1)
    elif case == 'missing_commit':
        changed = current.replace(
            _P11_NEW_BOTTOM, _P11_NEW_BOTTOM.replace(b'59621aa041a409c6ead27b74ffe25598c159e78e', b'', 1), 1)
    elif case == 'product_authority_overclaim':
        changed = current.replace(
            _P11_NEW_TOP, _P11_NEW_TOP.replace(
                b'records are evidence, not Coordinator durable authority or permission to\nperform effects.',
                b'records grant Coordinator durable authority and permission to\nperform effects.', 1), 1)
    elif case == 'acceptance_overclaim':
        changed = current.replace(
            _P11_NEW_BOTTOM, _P11_NEW_BOTTOM.replace(
                b'`preadmission_ready` is not acceptance.',
                b'`preadmission_ready` is terminal acceptance.', 1), 1)
    elif case == 'unrelated_byte':
        changed = current.replace(b'If `.docs/` exists', b'If `.dacs/` exists', 1)
    elif case == 'authority_sentence_byte':
        changed = current.replace(b'Coordinator cannot self-authorize',
                                  b'Coordinator cannoX self-authorize', 1)
    else:
        assert case == 'nonstatus_scope_sentence'
        changed = current.replace(
            _P11_NEW_TOP, _P11_NEW_TOP.replace(
                b'C1 paths retain durable authority.', b'C1 paths cede durable authority.', 1), 1)
    assert changed != current
    if boundary == 'p11:predecessor_identity':
        assert changed.count(_P11_NEW_TOP) == changed.count(_P11_NEW_BOTTOM) == 1
    with pytest.raises(AssertionError, match='^' + boundary + '$'):
        _p11_reconstruct_exact_status_predecessor(changed)


_D2_LOCAL_COMMIT_PREDECESSOR_IDENTITY = (12012, 'd5420bdf363aa09d896ab9711c6a700c95e6c55267e7e1e8b9feb264acaec646')
_SECTION41_LOCAL_COMMIT_PREDECESSOR_IDENTITY = (12956, '727a5048a0aafc26ad8676a76ac47377c83c8958d9f5976e84d47a84fabb5e90')
_CAPABILITY_LOCAL_COMMIT_PREDECESSOR_IDENTITY = (19883, '8fdfc493a3ecf78ee3020a83687466812fab1687f46d2f279c694cf079999129')
_D2_LOCAL_COMMIT_NEW = b'''
<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->
### Post-D2 cumulative local-commit status

The preceding pending-review sentence is historical implementation-stage
evidence, superseded only for review and local-commit status. The exact
sealed tree `3965cd3d1d3e28b43c9bc3709058c2524bad369d` was
independently reviewed for a separately governed commit gate and locally
committed as `66ee79132501e636d848ff8578fb674a208d6ac5`. The gate
reauthenticated all 299 committed blobs and Git modes and recorded 9,295
collected and 9,295 passing tests, zero failures, errors, or skips, with
three known Python 3.13 fork deprecation warnings. The two legal D2 layouts,
typed invalid-evidence stops, and original-run association above are unchanged.

The gate performed no push, PR, merge, publication, deployment, or product
effect. This is historical local-gate evidence, not a live remote-ref or
publication claim. Git objects and refs remain current commit and publication
truth. Audit, validation, provenance, reports, and status text are evidence,
not Coordinator durable authority or effect permission. The artifact-only
audit did not certify live Git, and the gate proves only its prospective
opening-to-commit interval; earlier raw-index and diagnostic-ref gaps remain
unresolved. F03 remains a nonblocking private-constructor observation; F2,
qualified F3/F6/F7, cross-host clock ordering, and live concerns remain open.

This proof adds no live custody, physical C2 decision or acceptance, terminal
outcome, executable permission, production provider or worker readiness, ES
or Bridge route, product Git authority, service, scheduler, or autonomous loop.
<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->
'''
_SECTION41_LOCAL_COMMIT_NEW = b'''
<!-- SECTION41_POST_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->
### Post-D2 cumulative local-commit status

The opening selected-contract status and the preceding outstanding-review
sentence are historical design and implementation-stage statements. The
bounded offline implementation in exact sealed tree
`3965cd3d1d3e28b43c9bc3709058c2524bad369d` was independently reviewed
for a separately governed commit gate and locally committed as
`66ee79132501e636d848ff8578fb674a208d6ac5`. The gate reauthenticated
all 299 committed blobs and Git modes and recorded 9,295 collected and 9,295
passing tests, zero failures, errors, or skips, with three known Python 3.13
fork deprecation warnings. The A/B split, original-run fresh association,
receipt-first replay, checked readback, schema, and recovery above retain
their exact bounds.

The gate performed no push, PR, merge, publication, deployment, or product
effect. This is a historical local-gate statement, not a live remote-ref or
publication claim. Git objects and refs remain current commit and publication
truth. Audit, validation, provenance, reports, and status text are evidence,
not Coordinator durable authority or effect permission. The artifact-only
audit did not certify live Git; the gate proves only its prospective
opening-to-commit interval. Earlier raw-index and diagnostic-ref gaps remain
unresolved. F03 remains a nonblocking private-constructor observation; F2,
qualified F3/F6/F7, cross-host clock ordering, and live concerns remain open.

This implementation adds no live custody, physical C2 decision or acceptance,
terminal outcome, executable permission, production provider or worker
readiness, ES or Bridge route, product Git authority, service, scheduler, or
autonomous loop.
<!-- SECTION41_POST_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->
'''
_CAPABILITY_LOCAL_COMMIT_NEW = b'''### P11 post-D2 cumulative local-commit exact successor

The P11 Unit 2 paragraph above remains the exact historical
implementation-stage predecessor. Current complete `AGENTS.md` records the
independent review of exact sealed tree
`3965cd3d1d3e28b43c9bc3709058c2524bad369d` for a separately governed
commit gate and its local commit
`66ee79132501e636d848ff8578fb674a208d6ac5`. That gate reauthenticated
all 299 committed blobs and Git modes and recorded 9,295 collected and 9,295
passing tests, zero failures, errors, or skips, with three known Python 3.13
fork deprecation warnings. It performed no push, PR, merge, publication,
deployment, or product effect. This is historical local-gate evidence, not a
live remote-ref or publication claim. Git objects and refs remain current
commit and publication truth. Audit, validation, provenance, reports, and
status text remain evidence, not Coordinator durable authority or effect
permission. Historical raw-index and diagnostic-ref gaps remain unresolved;
the artifact-only audit did not certify live Git, and the gate proves only
its prospective interval. F03 remains a nonblocking private-constructor
observation; F2, qualified F3/F6/F7, cross-host clock ordering, and live
concerns remain outside this successor. It adds no live custody, physical C2
decision or acceptance, terminal outcome, executable permission, production
provider or worker readiness, ES or Bridge route, product Git authority,
service, scheduler, or autonomous loop. Capability values, profile, digest,
qualification, and authority boundaries are unchanged.

'''


def _assert_exact_appended_owner_status(candidate: bytes, addition: bytes, predecessor_identity: tuple[int, str], begin: bytes, end: bytes) -> bytes:
    if (type(candidate) is not bytes or candidate.count(addition) != 1
            or candidate.count(begin) != 1 or candidate.count(end) != 1):
        raise AssertionError('owner:successor_count')
    if not candidate.endswith(addition):
        raise AssertionError('owner:successor_context')
    predecessor = candidate[:-len(addition)]
    if (len(predecessor), hashlib.sha256(predecessor).hexdigest()) != predecessor_identity:
        raise AssertionError('owner:predecessor_identity')
    return predecessor


def test_subordinate_post_d2_owner_statuses_reconstruct_exact_predecessors() -> None:
    d2_prior = _assert_exact_appended_owner_status(
        (ROOT / '.docs/rw0-d2-offline-evidence-and-review.md').read_bytes(),
        _D2_LOCAL_COMMIT_NEW, _D2_LOCAL_COMMIT_PREDECESSOR_IDENTITY,
        b'<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->',
        b'<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->')
    assert b'implementation evidence pending independent review' in d2_prior
    section_prior = _assert_exact_appended_owner_status(
        (ROOT / '.docs/section41-post-execution-proposal-family.md').read_bytes(),
        _SECTION41_LOCAL_COMMIT_NEW, _SECTION41_LOCAL_COMMIT_PREDECESSOR_IDENTITY,
        b'<!-- SECTION41_POST_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->',
        b'<!-- SECTION41_POST_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->')
    assert b'Independent review remains\noutstanding.' in section_prior
    assert b'selected contract' in section_prior.lower()
    capability = (ROOT / '.docs/rw0-b2-capability.md').read_bytes()
    ending = b'<!-- RW0_B2_CAPABILITY_OWNER_END -->\n'
    if capability.count(_CAPABILITY_LOCAL_COMMIT_NEW) != 1 or not capability.endswith(_CAPABILITY_LOCAL_COMMIT_NEW + ending):
        raise AssertionError('capability:successor_context')
    cap_prior = capability[:-len(_CAPABILITY_LOCAL_COMMIT_NEW + ending)] + ending
    assert (len(cap_prior), hashlib.sha256(cap_prior).hexdigest()) == _CAPABILITY_LOCAL_COMMIT_PREDECESSOR_IDENTITY
    assert b'implementation evidence pending independent review' in cap_prior
    required = (
        b'3965cd3d1d3e28b43c9bc3709058c2524bad369d',
        b'66ee79132501e636d848ff8578fb674a208d6ac5',
        b'299 committed blobs and Git modes', b'9,295', b'no push, PR, merge',
        b'not a live remote-ref', b'Git objects and refs remain',
        b'not Coordinator durable authority', b'no live custody',
        b'physical C2 decision or acceptance', b'executable permission',
        b'ES or Bridge route', b'product Git authority',
        b'service, scheduler, or autonomous loop',
    )
    for addition in (_D2_LOCAL_COMMIT_NEW, _SECTION41_LOCAL_COMMIT_NEW, _CAPABILITY_LOCAL_COMMIT_NEW):
        compact = b' '.join(addition.split())
        assert all(fragment in compact for fragment in required)


@pytest.mark.parametrize('owner', ('d2', 'section41'))
def test_subordinate_appended_owner_status_rejects_missing_and_outside_changes(owner):
    paths = {
        'd2': ('.docs/rw0-d2-offline-evidence-and-review.md', _D2_LOCAL_COMMIT_NEW,
               _D2_LOCAL_COMMIT_PREDECESSOR_IDENTITY,
               b'<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->',
               b'<!-- RW0_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->'),
        'section41': ('.docs/section41-post-execution-proposal-family.md',
                      _SECTION41_LOCAL_COMMIT_NEW, _SECTION41_LOCAL_COMMIT_PREDECESSOR_IDENTITY,
                      b'<!-- SECTION41_POST_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_BEGIN -->',
                      b'<!-- SECTION41_POST_D2_CUMULATIVE_LOCAL_COMMIT_STATUS_END -->'),
    }
    path, addition, identity, begin, end = paths[owner]
    current = (ROOT / path).read_bytes()
    prior = _assert_exact_appended_owner_status(current, addition, identity, begin, end)
    for changed, boundary in ((prior, 'owner:successor_count'),
                              (current + addition, 'owner:successor_count'),
                              (addition + prior, 'owner:successor_context'),
                              (b'X' + current, 'owner:predecessor_identity')):
        with pytest.raises(AssertionError, match='^' + boundary + '$'):
            _assert_exact_appended_owner_status(changed, addition, identity, begin, end)
