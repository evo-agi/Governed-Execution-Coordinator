"""Finite target-contract conformance; no production guard implementation."""
from copy import deepcopy
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
import sys
import ast
import hashlib
import json
from pathlib import Path
import re
import threading
from types import FunctionType

import pytest

from test_rw0_c2_durable_progression_decision_semantic_contract import (
    _baseline, _interpret, _interpret_pre_model, _c2_guard_gate, _model_consistency_phase,
    _no_write, _recover, _replay_family, _validate_document_text,
)

ROOT = Path(__file__).resolve().parents[1]
GUARD = '.docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md'
C2 = '.docs/rw0-c2-durable-progression-decision-semantic-contract.md'
HUMAN_BEGIN = '<!-- RW0_C2_BOOTSTRAP_GUARD_HUMAN_BEGIN -->'
HUMAN_END = '<!-- RW0_C2_BOOTSTRAP_GUARD_HUMAN_END -->'
MACHINE_BEGIN = '<!-- RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN -->'
MACHINE_END = '<!-- RW0_C2_BOOTSTRAP_GUARD_MACHINE_END -->'

# Independently reviewed test expectations, never derived from a parsed owner.
EXPECTED = {
    'authority': {'admission': 'external_standing_policy', 'guard': GUARD,
                  'decision': C2, 'writer': 'future_guarded_decision_transaction',
                  'replay': 'decision_owner', 'recovery': 'decision_owner', 'physical': 'unselected'},
    'scope': {'identity': 'admitted_coordinator_authority_lineage',
              'independence': 'explicit_independent_standing_policy_admission',
              'active_authorities': 1, 'distinct_productive_acceptances': 1,
              'applicability': 'admitted_direct_local_bootstrap', 'local_absence_is_proof': False,
              'continuity': 'positively_established',
              'nonidentity': ['deployment', 'machine', 'process', 'database', 'database_file',
                              'repository', 'program', 'attempt', 'candidate', 'command',
                              'parent_grant', 'restore', 'rollback', 'clone', 'passive_backup', 'relocation'],
              'uncertainty': ['missing', 'ambiguous', 'foreign', 'stale', 'conflicting', 'unreadable', 'unfenced'],
              'forbidden_changes': ['reset', 'renew', 'reopen', 'replenish', 'delete', 'recreate']},
    'admission_roles': ['guard_owner_profile', 'authority_lineage', 'bootstrap_scope',
                        'standing_policy_admission_act_identity_digest', 'bounded_direct_local_applicability',
                        'admission_provenance', 'nonrenewable_one_shot_ceiling',
                        'admission_fact_identity', 'canonical_admission_digest'],
    'relation': {'roles': ['canonical_admitted_lineage', 'canonical_scope_expectation', 'deterministic_family_route'],
                 'command_digest_covered': True, 'recovery_selector_covered': True,
                 'every_applicable_command': True, 'authority': False, 'requests_acceptance': False,
                 'prohibited': ['caller_admission', 'caller_acceptance_fact', 'model_scope', 'model_branch',
                                'mutable_selector', 'available_state_revision', 'available_preimage_digest',
                                'consumed_postimage_identity']},
    'acceptance_roles': ['guard_owner_profile', 'authority_lineage', 'bootstrap_scope',
                         'admission_fact_identity_digest', 'acceptance_fact_identity', 'consuming_mutation_ref',
                         'canonical_command_digest', 'acceptance_decision_identity_digest', 'resulting_program_version',
                         'committed_head_identity_digest', 'semantic_attempt_candidate_lineage',
                         'immutable_basis_identity_digest', 'family_route', 'single_transaction_timestamp',
                         'canonical_acceptance_digest'],
    'dag': ['standing_policy_admission_act', 'immutable_scope_admission_fact', 'command_expectation_and_digest',
            'decision_version_head', 'immutable_acceptance_fact', 'result', 'receipt',
            'replay_projection_and_whole_family_recovery'],
    'branch_effects': {'candidate_acceptance': 1, 'candidate_repair': 0, 'attempt_selecting_replan': 0,
                       'program_terminal_reject': 0, 'post_execution_program_block': 0},
    'eligibility': {'universal': ['lineage', 'scope', 'admission', 'continuity', 'sole_active', 'no_foreign_claim'],
                    'acceptance_only': ['exhaustive_guard_family_read', 'zero_committed_facts',
                                        'zero_duplicate_alias_collision_partial_malformed_foreign_unreadable_families',
                                        'exact_command_family_route', 'ordinary_acceptance_preconditions'],
                    'unknown_claim_nonaccept': 'exact_other_preconditions_no_unclaimed_assertion_no_fact',
                    'conflict': 'bootstrap_acceptance_guard_conflict', 'conflict_outcome': 'no_write'},
    'taxonomy': {
        'missing_admission': 'bootstrap_acceptance_guard_conflict', 'duplicate_admission': 'bootstrap_acceptance_guard_conflict',
        'malformed_admission': 'bootstrap_acceptance_guard_conflict', 'foreign_admission': 'bootstrap_acceptance_guard_conflict',
        'unreadable_admission': 'bootstrap_acceptance_guard_conflict', 'admission_substitution': 'bootstrap_acceptance_guard_conflict',
        'lineage_mismatch': 'bootstrap_acceptance_guard_conflict', 'continuity_unproven': 'bootstrap_acceptance_guard_conflict',
        'multiple_active': 'bootstrap_acceptance_guard_conflict', 'ambiguous_active': 'bootstrap_acceptance_guard_conflict',
        'stale_scope': 'bootstrap_acceptance_guard_conflict', 'wrong_scope': 'bootstrap_acceptance_guard_conflict',
        'unreadable_guard_family': 'bootstrap_acceptance_guard_conflict',
        'zero_exact_facts': 'fresh_acceptance_eligible_only_with_all_proofs', 'same_complete_family': 'exact_replay',
        'different_complete_winner': 'bootstrap_acceptance_guard_conflict', 'duplicate_facts': 'bootstrap_acceptance_guard_conflict',
        'malformed_partial_family': 'bootstrap_acceptance_guard_conflict',
        'fact_identity_collision': 'preassigned_identity_or_family_route_collision',
        'family_route_collision': 'preassigned_identity_or_family_route_collision',
        'mutation_different_digest': 'mutation_ref_reuse_conflict',
        'ordinary_precondition_failure': 'existing_command_basis_current_head_owner', 'nonaccept': 'no_acceptance_fact',
        'forbidden_scope_change': 'bootstrap_acceptance_guard_conflict', 'es_transition': 'separately_governed_nonreplenishing'},
    'family': {'acceptance_member': True, 'separate_receipt': False, 'separate_replay': False, 'separate_recovery': False,
               'receipt_first': True, 'replay_reevaluates': False, 'replay_new_fact': False, 'replay_new_timestamp': False,
               'replay_historical_head_freshness': False, 'committed_exact': 'every_expected_immutable_member_exact',
               'definitely_not_committed': 'original_new_family_exhaustively_absent_no_fragment_alias_collision_read_fault',
               'unresolved': 'neither_proposition_provable', 'competing_winner_retry': False,
               'recovery_repairs': False, 'recovery_new_timestamp': False, 'automatic_retry_unresolved': False},
    'terminal': {'binds_acceptance_identity_digest': True, 'binds_decision_result_receipt': True,
                 'mutates_guard': False, 'missing_uncommits_acceptance': False,
                 'unresolved_family_inference': False, 'uncertainty_erases_fact': False},
    'es': {'separately_governed': True, 'consumes': False, 'replenishes': False, 'resets': False, 'reinterprets': False,
           'fact_is_runtime_authority': False, 'new_grant_or_policy_epoch_replenishes': False},
    'b1': {'legacy_pair': ['latch_postimage_ref', 'latch_postimage_digest'],
           'target_binding': 'immutable_acceptance_fact_identity_digest',
           'current_validation': 'pair_shape_and_supplied_coherence_only', 'durable_guard_proof': False,
           'future_consumer': 'separately_accepted_safe_value_compatibility_versioning_decision'},
    'prohibited_architecture': ['mutable_available_consumed_subsystem', 'latch_state_row', 'latch_revision', 'reset_path',
                                'separate_latch_commit', 'separate_latch_receipt', 'separate_latch_replay_classifier',
                                'separate_latch_recovery_classifier', 'result_receipt_digest_in_acceptance_fact',
                                'timestamp_or_postcommit_projection_in_command_digest'],
    'implementation': {'source': False, 'migration': False, 'schema': False, 'provisioner': False, 'writer': False,
                       'reader': False, 'recovery': False, 'production_caller': False, 'public_surface': False,
                       'runtime': False, 'rw0_d_e': False, 'es_change': False},
}


HUMAN_TABLES = (
    ('Authority', 'authority'), ('Scope', 'scope'), ('Admission roles', 'admission_roles'),
    ('Relation', 'relation'), ('Acceptance roles', 'acceptance_roles'), ('Dag', 'dag'),
    ('Branch effects', 'branch_effects'), ('Eligibility', 'eligibility'), ('Taxonomy', 'taxonomy'),
    ('Family', 'family'), ('Terminal', 'terminal'), ('Es', 'es'), ('B1', 'b1'),
    ('Prohibited architecture', 'prohibited_architecture'), ('Implementation', 'implementation'),
)
OPERATIONAL_REALIZATIONS = (
    'deployment', 'machine', 'process', 'database', 'database_file', 'repository', 'program',
    'attempt', 'candidate', 'command', 'parent_grant', 'restore', 'rollback', 'clone',
    'passive_backup', 'relocation',
)
# The fixed parameter inventory survives omission of a case from this runtime case map.
OPERATIONAL_REALIZATION_CASES = dict.fromkeys(OPERATIONAL_REALIZATIONS)
GUARD_CAPABILITY_EXPECTED = {'P08': {'path': 'tests/c2a_contract_support.py',
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

PROSE = (
    ('scope', 'One scope belongs to one explicitly standing-policy-admitted Coordinator authority lineage.'),
    ('sole_active', 'One active authority per lineage is required; active-active database copies are forbidden.'),
    ('local_absence', 'Local row absence never proves an unclaimed scope.'),
    ('cross_program', 'At most one distinct productive candidate acceptance may commit across all programs in one admitted scope.'),
    ('nonreplenishment', 'Replacement, restore, rollback, clone, passive backup, and relocation never replenish allowance.'),
    ('universal', 'Every applicable command requires exact admitted lineage, scope, admission, continuity, sole-active authority, and no foreign claim.'),
    ('acceptance_only', 'Acceptance alone requires exhaustive unclaimed-scope proof and all ordinary C2 preconditions.'),
    ('nonaccept', 'Nonaccept branches create no acceptance fact and make no unclaimed-scope assertion.'),
    ('membership', 'Only derived candidate acceptance creates one immutable acceptance-fact family member.'),
    ('replay', 'Exact replay returns the original complete family and fact without reevaluation or a new timestamp.'),
    ('partial', 'Decision without fact or fact without decision is unresolved.'),
    ('competing_winner', 'A competing complete winner can prove original-family absence but never permits fresh retry in the claimed scope.'),
    ('terminal', 'A later terminal fact binds exact acceptance identity/digest and committed decision/result/receipt without guard mutation.'),
    ('es', 'Later ES operation is separately governed and never consumes, replenishes, resets, or reinterprets direct-local allowance.'),
    ('b1', 'The B1 legacy pair is representation/coherence only and is not current durable guard proof.'),
    ('fencing_before_receipt', 'Command-local grammar/basis and writer fencing precede private P1 receipt lookup.'),
    ('replay_before_eligibility', 'Receipt presence requires fresh universal disclosure posture before command-digest association or complete historical-family reconstruction; replay does not reevaluate fresh claimed status or acceptance eligibility.'),
    ('recording_before_eligibility', 'Receipt absence requires fresh universal recording posture before route and current-state checks, then authoritative branch derivation and acceptance-only eligibility, construction/application of the atomic family, capability invalidation, one commit attempt, and readback-only uncertainty resolution.'),
    ('implementation', 'Production/live physical representation, provisioning, runtime, and ES routing remain unimplemented and unselected.'),
)


def _require(condition, boundary):
    if not condition:
        raise AssertionError(boundary)


def _strict(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            _require(key not in result, 'guard:duplicate_json_key:' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def _region(text, begin, end):
    _require(text.count(begin) == text.count(end) == 1, 'guard:marker_inventory')
    _require(text.index(begin) < text.index(end), 'guard:marker_order')
    return text.split(begin)[1].split(end)[0]


def _type_exact(observed, expected, path='', *, boundary='guard:human_machine_equivalence', ordered_keys=False):
    """One recursive built-in-only policy for human, machine and fixed values."""
    location = path or '/'
    if type(expected) not in (dict, list, tuple, bool, int, str, type(None)) or type(observed) is not type(expected):
        raise AssertionError(boundary + ':' + location + ':type')
    if type(expected) is dict:
        _require(all(type(key) is str for key in observed) and set(observed) == set(expected), boundary + ':' + location + ':keys')
        if ordered_keys:
            _require(tuple(observed) == tuple(expected), boundary + ':' + location + ':order')
        for key, value in expected.items():
            escaped = key.replace('~', '~0').replace('/', '~1')
            _type_exact(observed[key], value, path + '/' + escaped, boundary=boundary, ordered_keys=ordered_keys)
    elif type(expected) in (list, tuple):
        _require(len(observed) == len(expected), boundary + ':' + location + ':length')
        for index, (actual, wanted) in enumerate(zip(observed, expected, strict=True)):
            _type_exact(actual, wanted, path + '/' + str(index), boundary=boundary, ordered_keys=ordered_keys)
    else:
        _require(observed == expected, boundary + ':' + location + ':value')


def _compare(observed, expected, path=''):
    try:
        _type_exact(observed, expected, path, boundary='guard:inventory')
    except AssertionError as error:
        # Retain the reviewed inventory hostile IDs while using the same exact policy.
        message = str(error)
        raise AssertionError(message.rsplit(':', 1)[0]) from None


def _human_rows_for(group):
    value = EXPECTED[group]
    return {group + '.' + key: item for key, item in value.items()} if type(value) is dict else {group: value}


def _table_cell(cell, role):
    value = cell.strip()
    if '`' in value:
        _require(value.startswith('`') and value.endswith('`') and value.count('`') == 2,
                 'guard:closed_human_table:cell:' + role)
        value = value[1:-1]
    return value.replace('\\|', '|')


def _parse_human_tables(text):
    region = _region(text, HUMAN_BEGIN, HUMAN_END)
    lines = region.splitlines()
    headings = [(index, line[4:]) for index, line in enumerate(lines) if line.startswith('### ')]
    _require(tuple(title for _, title in headings) == tuple(title for title, _ in HUMAN_TABLES),
             'guard:closed_human_table:headings')
    _require(not any(line.strip() for line in lines[:headings[0][0]]), 'guard:closed_human_table:outside')
    human = {}
    for position, ((index, title), (_, group)) in enumerate(zip(headings, HUMAN_TABLES, strict=True)):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        table = [line for line in lines[index + 1:end] if line.strip()]
        _require(len(table) >= 2 and table[0] == '| Role | Exact semantic inventory |',
                 'guard:closed_human_table:header:' + title)
        _require(table[1] == '| --- | --- |', 'guard:closed_human_table:separator:' + title)
        expected = _human_rows_for(group)
        seen = {}
        for number, line in enumerate(table[2:], 1):
            _require(line.startswith('|') and line.endswith('|'), 'guard:closed_human_table:line:' + title + ':' + str(number))
            cells = re.split(r'(?<!\\)\|', line[1:-1])
            _require(len(cells) == 2, 'guard:closed_human_table:columns:' + title + ':' + str(number))
            role = _table_cell(cells[0], title + ':' + str(number))
            _require(role not in human, 'guard:closed_human_table:duplicate:' + role)
            _require(role in expected, 'guard:closed_human_table:extra:' + role)
            value = _table_cell(cells[1], role)
            try:
                parsed = _strict(value)
            except json.JSONDecodeError:
                raise AssertionError('guard:closed_human_table:value:' + role) from None
            seen[role] = human[role] = parsed
        _require(tuple(seen) == tuple(expected), 'guard:closed_human_table:rows:' + title)
    return human


def _ordered_pipeline(text):
    section = text.split('## Deterministic reducer pipeline\n', 1)
    _require(len(section) == 2, 'guard_ordering_integrity:c2_pipeline')
    section = section[1].split('## Command and model non-authority\n', 1)[0]
    rows = re.findall(r'(?m)^(\d+)\. (.*(?:\n {3}.*)*)', section)
    _require(tuple(number for number, _ in rows) == tuple(str(number) for number in range(1, 10)),
             'guard_ordering_integrity:c2_pipeline')
    return {int(number): ' '.join(body.split()) for number, body in rows}


def _assert_guard_ordering_integrity(text, decision_text):
    section = text.split('## Immutable acceptance family and digest order\n', 1)
    _require(len(section) == 2, 'guard_ordering_integrity:guard_pipeline')
    section = section[1].split('## Terminal, ES, and compatibility boundaries\n', 1)[0]
    paragraphs = [' '.join(paragraph.split()) for paragraph in section.split('\n\n') if paragraph.strip()]
    candidates = [paragraph for paragraph in paragraphs if paragraph.startswith('Command-local grammar/basis and writer fencing')]
    _require(len(candidates) == 1, 'guard_ordering_integrity:fencing_before_receipt')
    sentences = re.split(r'(?<=\.) ', candidates[0])
    _require(sentences[0] == 'Command-local grammar/basis and writer fencing precede private P1 receipt lookup.',
             'guard_ordering_integrity:fencing_before_receipt')
    _require(sentences[1] == 'Receipt presence requires fresh universal disclosure posture before command-digest association or complete historical-family reconstruction; replay does not reevaluate fresh claimed status or acceptance eligibility.',
             'guard_ordering_integrity:replay_before_eligibility')
    chain = re.fullmatch(r'(.+) before (.+), then (.+), (.+), (.+), (.+), and (.+)\.', sentences[2])
    _require(chain is not None, 'guard_ordering_integrity:replay_before_eligibility')
    stages = chain.groups()
    _require(stages[0] == 'Receipt absence requires fresh universal recording posture', 'guard_ordering_integrity:replay_before_eligibility')
    _require(stages[1] == 'route and current-state checks' and stages[2] == 'authoritative branch derivation and acceptance-only eligibility',
             'guard_ordering_integrity:replay_before_eligibility')
    _require(stages[3] == 'construction/application of the atomic family', 'guard_ordering_integrity:eligibility_before_family')
    _require(stages[4:] == ('capability invalidation', 'one commit attempt', 'readback-only uncertainty resolution'),
             'guard_ordering_integrity:commit_resolution')
    rows = _ordered_pipeline(decision_text)
    _require(rows[7] == 'Retain the exact admitted-lineage relation and universal posture already established in the command/writer admission prefix. If and only if acceptance was derived, prove the scope exhaustively unclaimed. Failure is no-write; success creates one immutable acceptance-fact member of the future atomic decision family.',
             'guard_ordering_integrity:model_after_guard')
    _require(rows[8] == 'Only after all authoritative no-write gates, including the bootstrap guard, evaluate model-recommendation consistency. Retain that evidence without changing the branch. This is always the last evaluation stage while the basis remains valid.',
             'guard_ordering_integrity:model_after_guard')


def _parse(text):
    _require(text.startswith('# RW0-C2 Bootstrap Acceptance-Guard Semantic Contract\n'), 'guard:title')
    machine_region = _region(text, MACHINE_BEGIN, MACHINE_END)
    _require(machine_region.count('```') == 2, 'guard:single_json')
    raw = machine_region.split('```json\n')[1].split('\n```')[0]
    machine = _strict(raw)
    _require(json.dumps(machine, sort_keys=True, separators=(',', ':')) == raw, 'guard:canonical_json')
    human = _parse_human_tables(text)
    expected_human = {}
    for key, value in machine.items():
        if type(value) is dict:
            expected_human.update({key + '.' + subkey: item for subkey, item in value.items()})
        else:
            expected_human[key] = value
    _type_exact(human, expected_human)
    _compare(machine, EXPECTED)
    _assert_guard_ordering_integrity(text, (ROOT / C2).read_text())
    compact = ' '.join(text.split())
    for boundary, sentence in PROSE:
        _require(sentence in compact, 'guard:prose:' + boundary)
    _require('## Acceptance-latch dependency' not in text, 'guard:competing_mutable_owner')
    return machine


@pytest.fixture
def guard():
    return _parse((ROOT / GUARD).read_text())


@pytest.fixture
def decision():
    return _validate_document_text((ROOT / C2).read_text())


def _posture():
    return {'lineage': 'L', 'scope': 'S', 'admission': 'A', 'admission_issuer': 'external_standing_policy',
            'expected_lineage': 'L', 'expected_scope': 'S', 'expected_admission': 'A',
            'admission_binding': ('L', 'S', 'A'),
            'continuity': 'exact', 'active': 1, 'foreign': False, 'exhaustive': True,
            'families_clean': True, 'route_exact': True, 'claimed': False, 'forbidden': None}


def _guard_relation(g, posture):
    """Abstract supplied-proof classifier, not an authority issuer or branch reducer."""
    for role in ('lineage', 'scope', 'admission'):
        if not posture.get(role) or posture.get(role) != posture.get('expected_' + role):
            return 'bootstrap_acceptance_guard_conflict'
    if (posture.get('admission_binding') != (posture['lineage'], posture['scope'], posture['admission']) or
            posture.get('admission_issuer') != g['authority']['admission'] or
            posture.get('continuity') != 'exact' or posture.get('active') != g['scope']['active_authorities'] or
            posture.get('foreign') is not False or posture.get('forbidden') is not None):
        return 'bootstrap_acceptance_guard_conflict'
    return None


def _acceptance_guard_eligibility(g, posture, prepared):
    result = deepcopy(prepared)
    result['audit_trace'] += ('bootstrap_guard_evaluated',)
    if (not posture['exhaustive'] or not posture['families_clean'] or not posture['route_exact'] or
            posture['claimed'] is not False):
        return _no_write(g['eligibility']['conflict'], result['audit_trace'])
    return result


def _evaluate(g, c, posture, state, previous=None, mutation='M', digest='D'):
    trace = ['command_structure_checked']
    if posture.get('command_structure_valid', True) is not True or any(field in posture for field in g['relation']['prohibited']):
        return _no_write('required_fact_invalid', tuple(trace))
    trace.append('writer_fencing_checked')
    if posture.get('writer_fenced', True) is not True:
        return _no_write('bootstrap_acceptance_guard_conflict', tuple(trace))
    trace.append('universal_authority_checked')
    conflict = _guard_relation(g, posture)
    if conflict:
        return _no_write(conflict, tuple(trace))
    trace.append('receipt_replay_checked')
    replay = _receipt_replay_check(previous, mutation, digest)
    if replay is not None:
        return replay
    prepared = _interpret_pre_model(c, state)
    prepared['audit_trace'] = tuple(trace) + prepared['audit_trace']
    if prepared['outcome'] == 'no_write':
        return prepared
    prepared['audit_trace'] += ('authoritative_branch_derived',)
    if prepared['branch'] == 'candidate_acceptance':
        prepared = _acceptance_guard_eligibility(g, posture, prepared)
        if prepared['outcome'] == 'no_write':
            return prepared
    prepared = _c2_guard_gate(c, prepared)
    return _model_consistency_phase(c, prepared)


def _family(result, program='P', mutation='M', digest='D'):
    """Opaque test evidence members, deliberately not a future DTO/schema."""
    f = {'mutation_ref': mutation, 'command_digest': digest, 'decision': program + ':decision',
         'version': program + ':version', 'head': program + ':head', 'result': program + ':result',
         'receipt': program + ':receipt', 'timestamp': 'one_original_timestamp', 'branch': result['branch']}
    if result['branch'] == 'candidate_acceptance':
        f['acceptance_fact'] = (program + ':fact', 'immutable_digest')
    return f


def _state_for(c, branch):
    s = _baseline(c)
    if branch != 'candidate_acceptance':
        s['guard_state'] = 'unknown'
    if branch == 'post_execution_program_block':
        s['currentness'] = 'unknown'
    elif branch != 'candidate_acceptance':
        source = {'candidate_repair': 'repair', 'attempt_selecting_replan': 'replan', 'program_terminal_reject': 'terminal'}[branch]
        s['validation'] = deepcopy(next(row for row in c['validation_projection'] if row['normalized_class'] == source))
    return s


def test_guard_inventory_and_two_owner_split(guard, decision):
    _require(decision['guard']['owner'] == GUARD, 'guard:sole_owner_route')
    _require('admission_roles' not in decision and 'acceptance_roles' not in decision, 'guard:nonoverlapping_owners')
    _require('latch' not in decision, 'guard:no_mutable_dependency')
    for relative in ('AGENTS.md', 'README.md', '.docs/architecture.md', '.docs/c2a-first-slice-semantic-protocol-contract.md',
                     '.docs/rw0-remote-worker-contact-phase-entry.md', '.docs/rw0-b1-pure-phase-values.md',
                     '.docs/c2b-durable-development-state.md', '.docs/c2b3-program-initialization.md'):
        text = (ROOT / relative).read_text()
        _require(GUARD in text or 'under the guard owner' in text, 'guard:projection_route:' + relative)


@pytest.mark.parametrize('branch', ['candidate_acceptance', 'candidate_repair', 'attempt_selecting_replan',
                                   'program_terminal_reject', 'post_execution_program_block'])
def test_all_five_branch_effects(guard, decision, branch):
    p = _posture()
    if branch != 'candidate_acceptance':
        p['claimed'] = 'unknown'
    result = _evaluate(guard, decision, p, _state_for(decision, branch))
    _require(result['branch'] == branch, 'guard:derived_branch:' + branch)
    members = _family(result)
    _require(int('acceptance_fact' in members) == guard['branch_effects'][branch], 'guard:branch_fact_count:' + branch)
    _require(result['acceptance_fact_effect'] == ('create_one_immutable_acceptance_fact' if branch == 'candidate_acceptance' else 'none'), 'guard:branch_effect:' + branch)


def test_cross_program_ceiling_and_independent_lineages(guard, decision):
    posture = CANONICAL_GUARD_POSTURE
    scenario = _cross_program_scenario(posture)
    _assert_cross_program_scenario(scenario, posture)
    ledger = {}
    for label, command in zip(('A', 'B'), scenario, strict=True):
        _assert_command_admission_binding(command, posture, label)
        p = _posture()
        for role in ('lineage', 'scope'):
            p[role] = command[role]
            p['expected_' + role] = getattr(posture, role)
        p['admission'] = command['admission']
        p['expected_admission'] = posture.admission_ref
        p['admission_binding'] = (command['lineage'], command['scope'], command['admission'])
        p['active'] = command['active_authorities']
        scope_key = (command['lineage'], command['scope'], command['admission'], command['admission_digest'])
        p['claimed'] = scope_key in ledger
        state = _baseline(decision)
        # Opaque supplied coordinates, not a future command or storage schema.
        state['program_coordinates'] = command['basis']
        state['attempt_candidate_lineage'] = command['attempt_candidate']
        _require(state['program_coordinates'][0] == command['program_ref'],
                 'guard:cross_program_scenario:behavior_program_binding')
        result = _evaluate(guard, decision, p, state,
                           mutation=command['mutation_ref'], digest=command['command_digest'])
        expected = CROSS_PROGRAM_OUTCOMES[command['program_ref']]
        _require(result['outcome'] == expected, 'guard:cross_program_ceiling:' + command['label'])
        if result['outcome'] == 'durable_decision':
            _require(result['retained_basis']['program_coordinates'] == command['basis'],
                     'guard:cross_program_scenario:retained_program_binding')
            family = _family(result, command['program_ref'], command['mutation_ref'], command['command_digest'])
            _require('acceptance_fact' in family, 'guard:cross_program_scenario:first_fact')
            ledger[scope_key] = family
        else:
            _require(result['rejection'] == 'bootstrap_acceptance_guard_conflict',
                     'guard:cross_program_scenario:claimed_scope_rejection')
    _require(len(ledger) == 1, 'guard:cross_program_scenario:one_shared_fact')
    independent = _posture()
    for key, value in (('lineage', 'L2'), ('scope', 'S2'), ('admission', 'A2')):
        independent[key] = independent['expected_' + key] = value
    independent['admission_binding'] = ('L2', 'S2', 'A2')
    result = _evaluate(guard, decision, independent, _baseline(decision), mutation='independent_C')
    _require(result['outcome'] == 'durable_decision', 'guard:independent_admitted_lineages')


POSTURE_HOSTILES = [
    ('missing_admission', 'admission', None), ('duplicate_admission', 'admission', ['A', 'A']),
    ('malformed_admission', 'admission', {}), ('foreign_admission', 'admission', 'foreign'),
    ('unreadable_admission', 'admission', 'unreadable'), ('admission_substitution', 'expected_admission', 'A2'),
    ('lineage_mismatch', 'expected_lineage', 'L2'), ('continuity_unproven', 'continuity', 'missing'),
    ('multiple_active', 'active', 2), ('ambiguous_active', 'active', None),
    ('stale_scope', 'expected_scope', 'old'), ('wrong_scope', 'scope', 'wrong'),
    ('unreadable_guard_family', 'exhaustive', False), ('local_absence', 'exhaustive', False),
    ('duplicate_facts', 'families_clean', False), ('partial_family', 'families_clean', False),
    ('claimed', 'claimed', True), ('unknown_claim', 'claimed', 'unknown'),
    ('caller_admission', 'admission_issuer', 'caller'), ('model_admission', 'admission_issuer', 'model'),
    ('independent_without_admission', 'admission_issuer', None),
]


@pytest.mark.parametrize('case,key,value', POSTURE_HOSTILES)
def test_guard_hostiles_fail_at_no_write_boundary(guard, decision, case, key, value):
    p = _posture(); p[key] = value
    result = _evaluate(guard, decision, p, _baseline(decision))
    _require(result.get('outcome') == 'no_write' and result.get('rejection') == 'bootstrap_acceptance_guard_conflict', 'guard:hostile:' + case)


@pytest.mark.parametrize('realization', OPERATIONAL_REALIZATIONS)
def test_operational_realization_never_admits_or_replenishes(guard, decision, realization):
    _assert_operational_realization_inventory(tuple(OPERATIONAL_REALIZATION_CASES))
    _require(realization in guard['scope']['nonidentity'], 'guard:nonidentity:' + realization)
    p = _posture(); p['claimed'] = True; p['realization'] = realization + ':new'
    result = _evaluate(guard, decision, p, _baseline(decision))
    _require(result['outcome'] == 'no_write', 'guard:nonreplenishment:' + realization)
    p['claimed'] = False; p['admission'] = None
    _require(_evaluate(guard, decision, p, _baseline(decision))['outcome'] == 'no_write', 'guard:realization_no_admission:' + realization)


@pytest.mark.parametrize('change', ['reset', 'renew', 'reopen', 'replenish', 'delete', 'recreate'])
def test_forbidden_guard_changes(guard, decision, change):
    p = _posture(); p['forbidden'] = change
    _require(_evaluate(guard, decision, p, _baseline(decision))['outcome'] == 'no_write', 'guard:forbidden:' + change)


def test_receipt_first_replay_collision_and_no_second_fact(guard, decision):
    original = _family(_interpret(decision, _baseline(decision)))
    bad = _posture(); bad['claimed'] = True
    replay = _evaluate(guard, decision, bad, {'not_a_basis': True}, previous=original)
    _require(replay['acceptance_fact'] == original['acceptance_fact'] and replay['timestamp'] == original['timestamp'], 'guard:replay_no_new_fact_timestamp')
    _require(replay == original and replay is not original, 'guard:replay_same_family')
    conflict = _evaluate(guard, decision, bad, {}, previous=original, digest='different')
    _require(conflict['rejection'] == 'mutation_ref_reuse_conflict', 'guard:mutation_digest_collision')


@pytest.mark.parametrize('observation,exhaustive,fault,expected', [
    ('complete', True, False, 'committed_exact'), ('absent', True, False, 'definitely_not_committed'),
    ('decision_only', True, False, 'unresolved'), ('fact_only', True, False, 'unresolved'),
    ('complete', False, False, 'unresolved'), ('absent', False, False, 'unresolved'),
    ('absent', True, True, 'unresolved'), ('wrong_fact', True, False, 'unresolved'),
])
def test_one_whole_family_recovery(guard, decision, observation, exhaustive, fault, expected):
    family = _family(_interpret(decision, _baseline(decision)))
    observed = deepcopy(family)
    if observation == 'absent': observed = {}
    elif observation == 'decision_only': observed.pop('acceptance_fact')
    elif observation == 'fact_only': observed = {'acceptance_fact': family['acceptance_fact']}
    elif observation == 'wrong_fact': observed['acceptance_fact'] = 'foreign'
    result = _recover(decision, commit_attempted=True, expected_family=family, observed_family=observed,
                      exhaustive=exhaustive, collision_or_read_fault=fault)
    _require(result['classification'] == expected, 'guard:recovery:' + observation)
    _require(result['guard_mutated_by_recovery'] is False, 'guard:recovery_nonmutation')


def test_competing_winner_absence_is_not_retry_permission(guard, decision):
    original = _family(_interpret(decision, _baseline(decision)), mutation='original')
    # Exhaustive selector read of original newly-created members, independently of winner.
    result = _recover(decision, commit_attempted=True, expected_family=original, observed_family={})
    _require(result['classification'] == 'definitely_not_committed', 'guard:original_absent_with_winner')
    p = _posture(); p['claimed'] = True
    _require(_evaluate(guard, decision, p, _baseline(decision), mutation='original')['outcome'] == 'no_write', 'guard:competing_winner_no_retry')


def test_acyclic_identity_roles_and_terminal_es_nonmutation(guard, decision):
    edges = [('standing_policy_admission_act', 'immutable_scope_admission_fact'),
             ('immutable_scope_admission_fact', 'command_expectation_and_digest'),
             ('command_expectation_and_digest', 'decision_version_head'),
             ('decision_version_head', 'immutable_acceptance_fact'), ('immutable_acceptance_fact', 'result'),
             ('result', 'receipt'), ('receipt', 'replay_projection_and_whole_family_recovery')]
    positions = {role: i for i, role in enumerate(guard['dag'])}
    for parent, child in edges:
        _require(positions[parent] < positions[child], 'guard:acyclic:' + parent + ':' + child)
    family = _family(_interpret(decision, _baseline(decision)))
    before = deepcopy(family)
    terminal_binding = (family['acceptance_fact'], family['decision'], family['result'], family['receipt'])
    _require(terminal_binding[0] == before['acceptance_fact'] and family == before, 'guard:terminal_nonmutation')
    _require(guard['terminal']['mutates_guard'] is False, 'guard:terminal_mutation_forbidden')
    _require(all(guard['es'][key] is False for key in ('consumes', 'replenishes', 'resets', 'reinterprets', 'fact_is_runtime_authority', 'new_grant_or_policy_epoch_replenishes')), 'guard:es_nonreplenishment')


def test_b1_compatibility_and_focused_nonimplementation(guard):
    compact = ' '.join((ROOT / '.docs/rw0-b1-pure-phase-values.md').read_text().split())
    _require('No new target implementation may consume the pair as durable guard proof until a separately accepted safe-value compatibility/versioning decision.' in compact, 'guard:b1_future_consumer_gate')
    _require('Current B1 validates pair presence/absence and supplied-value coherence only.' in compact, 'guard:b1_nonproof')
    _require(all(value is False for value in guard['implementation'].values()), 'guard:implementation_nonclaims')
    source = ROOT / 'src' / 'ge_nwp_coordinator'
    _require(not any('bootstrap_acceptance_guard' in p.name or 'bootstrap_scope_admission' in p.name for p in source.rglob('*.py')), 'guard:source_module_absent')
    migration_root = source / 'sqlite_migrations'
    _require(
        {p.name for p in migration_root.glob('0005*')}
        == {'0005_section41_post_execution_proposal_family.sql'},
        'guard:section41_0005_exact_successor',
    )
    _require(
        {p.name for p in migration_root.glob('*rw0_c2*')}
        == {'0006_rw0_c2_scope_admission.sql',
            '0007_rw0_c2_progression_decision.sql'},
        'guard:p0_p1_migration_successor',
    )
    for relative in ('state_store.py', '__init__.py'):
        text = (source / relative).read_text()
        tree = ast.parse(text)
        _require(not any(isinstance(n, (ast.FunctionDef, ast.ClassDef)) and ('bootstrap_guard' in n.name or 'scope_admission' in n.name) for n in ast.walk(tree)), 'guard:public_source_absent:' + relative)


def test_capability_supersession_has_semantic_assertions():
    _assert_capability_semantic_source((ROOT / 'tests/test_rw0_b2_capability_boundaries.py').read_text())
    _assert_capability_documents_integrity()
    _require('P08/P11/P12/P13' in (ROOT / '.docs/rw0-b2-capability.md').read_text(), 'guard:capability_review_record')


# Hostile expectations authored independently of EXPECTED and parser output.
INVENTORY_HOSTILES = [
    ('scope', 'identity', 'database', 'guard:inventory:/scope/identity'),
    ('scope', 'independence', 'automatic', 'guard:inventory:/scope/independence'),
    ('scope', 'active_authorities', 2, 'guard:inventory:/scope/active_authorities'),
    ('scope', 'local_absence_is_proof', True, 'guard:inventory:/scope/local_absence_is_proof'),
    ('scope', 'distinct_productive_acceptances', 2, 'guard:inventory:/scope/distinct_productive_acceptances'),
    ('branch_effects', 'candidate_repair', 1, 'guard:inventory:/branch_effects/candidate_repair'),
    ('eligibility', 'conflict_outcome', 'durable_block', 'guard:inventory:/eligibility/conflict_outcome'),
    ('family', 'replay_new_fact', True, 'guard:inventory:/family/replay_new_fact'),
    ('family', 'replay_new_timestamp', True, 'guard:inventory:/family/replay_new_timestamp'),
    ('family', 'committed_exact', 'partial_allowed', 'guard:inventory:/family/committed_exact'),
    ('family', 'competing_winner_retry', True, 'guard:inventory:/family/competing_winner_retry'),
    ('terminal', 'mutates_guard', True, 'guard:inventory:/terminal/mutates_guard'),
    ('es', 'replenishes', True, 'guard:inventory:/es/replenishes'),
    ('b1', 'durable_guard_proof', True, 'guard:inventory:/b1/durable_guard_proof'),
    ('implementation', 'writer', True, 'guard:inventory:/implementation/writer'),
    ('relation', 'authority', True, 'guard:inventory:/relation/authority'),
]


@pytest.mark.parametrize('group,key,value,boundary', INVENTORY_HOSTILES)
def test_inventory_hostiles_have_exact_boundaries(group, key, value, boundary):
    changed = deepcopy(EXPECTED); changed[group][key] = value
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _compare(changed, EXPECTED)


@pytest.mark.parametrize('boundary,sentence', PROSE)
def test_prose_only_drift_has_exact_boundary(boundary, sentence):
    text = (ROOT / GUARD).read_text()
    changed = re.sub(r'\s+'.join(re.escape(word) for word in sentence.split()), 'Contradictory target prose.', text, count=1)
    exact = ('guard_ordering_integrity:' if boundary in ('fencing_before_receipt', 'replay_before_eligibility', 'recording_before_eligibility') else 'guard:prose:') + (('replay_before_eligibility' if boundary == 'recording_before_eligibility' else boundary))
    with pytest.raises(AssertionError, match='^' + re.escape(exact) + '$'):
        _parse(changed)


def test_duplicate_key_and_machine_only_drift_exact_boundaries():
    text = (ROOT / GUARD).read_text()
    changed = text.replace('"active_authorities":1', '"active_authorities":1,"active_authorities":1', 1)
    with pytest.raises(AssertionError, match='^guard:duplicate_json_key:active_authorities$'):
        _parse(changed)
    changed = text.replace('"active_authorities":1', '"active_authorities":2', 1)
    with pytest.raises(AssertionError, match='^guard:human_machine_equivalence:/scope.active_authorities:value$'):
        _parse(changed)


@pytest.mark.parametrize('field', ['caller_admission', 'caller_acceptance_fact', 'model_scope', 'model_branch', 'mutable_selector', 'available_state_revision', 'available_preimage_digest', 'consumed_postimage_identity'])
def test_authority_and_mutable_relation_fields_fail_closed(guard, decision, field):
    p = _posture(); p[field] = 'caller_supplied'
    result = _evaluate(guard, decision, p, _baseline(decision))
    _require(result['outcome'] == 'no_write' and result['rejection'] == 'required_fact_invalid', 'guard:prohibited_relation:' + field)


@pytest.mark.parametrize('role', ['lineage', 'scope', 'admission', 'continuity', 'sole_active', 'no_foreign_claim'])
@pytest.mark.parametrize('uncertainty', ['missing', 'ambiguous', 'foreign', 'stale', 'conflicting', 'unreadable', 'unfenced'])
def test_universal_uncertainty_is_no_write_for_nonaccept(guard, decision, role, uncertainty):
    state = _state_for(decision, 'candidate_repair')
    state['guard_relation'][role] = uncertainty
    result = _evaluate(guard, decision, _posture(), state)
    _require(result['outcome'] == 'no_write' and result['rejection'] == 'bootstrap_acceptance_guard_conflict', 'guard:universal_uncertainty:' + role + ':' + uncertainty)


@pytest.mark.parametrize('fault,reason', [('mutation_ref_reused_with_different_digest', 'mutation_ref_reuse_conflict'), ('preassigned_identity_collision', 'preassigned_identity_or_family_route_collision'), ('family_route_collision', 'preassigned_identity_or_family_route_collision')])
def test_collision_reason_owners_remain_distinct(guard, decision, fault, reason):
    state = _baseline(decision); state['admission_fault'] = fault
    result = _evaluate(guard, decision, _posture(), state)
    _require(result['outcome'] == 'no_write' and result['rejection'] == reason, 'guard:collision_owner:' + fault)


def test_no_competing_guard_inventory_owner(guard):
    holders = []
    for path in (ROOT / '.docs').glob('*.md'):
        text = path.read_text()
        if HUMAN_BEGIN in text or MACHINE_BEGIN in text:
            holders.append(path.relative_to(ROOT).as_posix())
    _require(holders == [GUARD], 'guard:sole_inventory_owner')


@pytest.mark.parametrize('missing', ['decision', 'acceptance_fact', 'receipt'])
def test_partial_family_cannot_replay(guard, decision, missing):
    family = _family(_interpret(decision, _baseline(decision)))
    family.pop(missing)
    result = _evaluate(guard, decision, _posture(), {}, previous=family)
    _require(result.get('outcome') == 'no_write' and result.get('rejection') == 'required_fact_invalid', 'guard:partial_replay:' + missing)


def test_four_document_guard_projection():
    begin = '<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_BEGIN -->'
    end = '<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->'
    bodies = []
    for relative in ('.docs/autonomous-software-development-operating-model.md', '.docs/worker-execution-boundary.md', '.docs/authority-boundaries.md', '.docs/durable-state-model.md'):
        payload = (ROOT / relative).read_bytes()
        if relative in ('.docs/worker-execution-boundary.md', '.docs/durable-state-model.md'):
            # Compare the exact historical shared projection after verifying
            # its separately governed, owner-local current C2 successor.
            payload, _status = _rw0_c2_current_drift_predecessor(relative, payload)
        text = payload.decode('utf-8')
        body = _region(text, begin, end)
        compact = ' '.join(body.split())
        _require('The accepted direct-local C2B decision alone atomically creates the immutable bootstrap-acceptance fact in its guarded writer transaction' in compact, 'guard:four_body_immutable_fact:' + relative)
        _require('acceptance-fact identity/digest without mutating guard truth' in compact, 'guard:four_body_terminal_binding:' + relative)
        _require(GUARD in compact, 'guard:four_body_owner_route:' + relative)
        bodies.append(compact)
    _require(len(set(bodies)) == 1, 'guard:four_body_drift')


def _assert_digest_dag(edges):
    graph = {}
    for parent, child in edges:
        graph.setdefault(parent, []).append(child)
    def visit(node, ancestors):
        _require(node not in ancestors, 'guard:digest_cycle:' + node)
        for child in graph.get(node, []):
            visit(child, ancestors | {node})
    for node in graph:
        visit(node, set())


def test_digest_cycle_is_rejected_without_full_future_schema():
    edges = [('admission', 'command'), ('command', 'decision'), ('decision', 'fact'), ('fact', 'result'), ('result', 'receipt')]
    _assert_digest_dag(edges)
    with pytest.raises(AssertionError, match='^guard:digest_cycle:fact$'):
        _assert_digest_dag(edges + [('receipt', 'fact')])


def test_replay_retains_universal_authority_prefix(guard, decision):
    family = _family(_interpret(decision, _baseline(decision)))
    p = _posture(); p['continuity'] = 'unfenced'
    result = _evaluate(guard, decision, p, {}, previous=family)
    _require(result['outcome'] == 'no_write' and result['rejection'] == 'bootstrap_acceptance_guard_conflict', 'guard:replay_universal_prefix')


def test_joint_caller_expectation_substitution_cannot_change_admission(guard, decision):
    p = _posture()
    p['lineage'] = p['expected_lineage'] = 'database_copy'
    p['scope'] = p['expected_scope'] = 'new_local_scope'
    result = _evaluate(guard, decision, p, _baseline(decision))
    _require(result['outcome'] == 'no_write' and result['rejection'] == 'bootstrap_acceptance_guard_conflict', 'guard:immutable_admission_binding')


@pytest.mark.parametrize('action', ['create', 'reset', 'update', 'delete', 'renew', 'repair', 'replenish'])
def test_terminal_has_no_guard_change_authority(guard, decision, action):
    family = _family(_interpret(decision, _baseline(decision)))
    before = deepcopy(family)
    with pytest.raises(AssertionError, match='^guard:terminal_action_forbidden:' + action + '$'):
        _require(guard['terminal']['mutates_guard'], 'guard:terminal_action_forbidden:' + action)
    _require(family == before, 'guard:terminal_family_permanent')



def _assert_capability_semantic_source(text):
    tree = ast.parse(text)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    helper = functions.get('_guard_replacement_semantic_evidence')
    _require(helper is not None, 'guard:capability_semantic_integrity:helper')
    returns = [node for node in ast.walk(helper) if isinstance(node, ast.Return)]
    _require(not any(isinstance(node, ast.Pass) for node in ast.walk(helper)) and len(returns) == 1 and
             isinstance(returns[0].value, ast.Name) and returns[0].value.id == 'evidence',
             'guard:capability_semantic_integrity:helper_body')
    attributes = {node.func.attr for node in ast.walk(helper) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    _require({'read_bytes', 'sha256', 'decode'} <= attributes, 'guard:capability_semantic_integrity:observed_documents')
    checker = functions.get('_assert_capability_semantic_integrity')
    _require(checker is not None and len(checker.body) == 3 and isinstance(checker.body[1], ast.If) and
             isinstance(checker.body[2], ast.If) and not any(isinstance(node, (ast.Pass, ast.Return)) for node in ast.walk(checker)),
             'guard:capability_semantic_integrity:comparison_body')
    caller = functions.get('test_protected_content_surface_has_exact_literal_identities')
    expected = ast.parse('observed = _guard_replacement_semantic_evidence()\n_assert_capability_semantic_integrity(observed, CAPABILITY_REPLACEMENT_EXPECTED)').body
    _require(caller is not None and len(caller.body) >= 2 and
             tuple(ast.dump(node, include_attributes=False) for node in caller.body[:2]) ==
             tuple(ast.dump(node, include_attributes=False) for node in expected),
             'guard:capability_semantic_integrity:compared_return')
    assignments = [node for node in tree.body if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == 'CAPABILITY_REPLACEMENT_EXPECTED' for target in node.targets)]
    _require(len(assignments) == 1, 'guard:capability_semantic_integrity:fixed_expectation')
    _type_exact(ast.literal_eval(assignments[0].value), GUARD_CAPABILITY_EXPECTED,
                boundary='guard:capability_semantic_integrity:fixed_expectation')
    protected_bindings = []

    def inspect_module_execution(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Lambda)):
            return
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign,
                             ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            if any(isinstance(name, ast.Name) and name.id == 'PROTECTED_CONTENT_ROWS'
                   and isinstance(name.ctx, ast.Store)
                   for target in targets for name in ast.walk(target)):
                protected_bindings.append(node)
        for child in ast.iter_child_nodes(node):
            inspect_module_execution(child)

    inspect_module_execution(tree)
    _require(len(protected_bindings) == 1,
             'guard:capability_semantic_integrity:protected_single_literal')
    protected = protected_bindings[0]
    _require(isinstance(protected, ast.Assign) and len(protected.targets) == 1 and
             isinstance(protected.targets[0], ast.Name) and
             protected.targets[0].id == 'PROTECTED_CONTENT_ROWS',
             'guard:capability_semantic_integrity:protected_single_literal')
    try:
        literal_rows = ast.literal_eval(protected.value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise AssertionError('guard:capability_semantic_integrity:protected_single_literal') from None
    _require(type(literal_rows) is tuple and len(literal_rows) == 13 and
             all(type(row) is tuple and len(row) == 6 for row in literal_rows),
             'guard:capability_semantic_integrity:protected_literal_rows')
    rows = {row[0]: row for row in literal_rows}
    _require(len(rows) == 13,
             'guard:capability_semantic_integrity:protected_literal_rows')
    for pid, reference in GUARD_CAPABILITY_EXPECTED.items():
        _require(pid in rows, 'guard:capability_semantic_integrity:protected:' + pid)
        row = rows[pid]
        _type_exact((row[1], (row[2], row[3]), row[4], row[5]),
                    (reference['path'], reference['replacement_identity'],
                     reference['contract_classes'], reference['purpose']),
                    boundary='guard:capability_semantic_integrity:ownership:' + pid)


def _assert_capability_documents_integrity():
    for pid, reference in GUARD_CAPABILITY_EXPECTED.items():
        data = (ROOT / reference['path']).read_bytes()
        if pid in ('P11', 'P12', 'P13'):
            data = _rw0_normal_terminal_status_predecessor(
                reference['path'], data,
                boundary='guard:capability_semantic_integrity')
        if pid in ('P11', 'P12'):
            current, status_suffix = {
                'P11': ((74410, 'c8ccf0552265d172a659a30be898fffd35cc70fad4821a350c3a9bf00e8f6b5d'),
                        (1664, '35b0ef1755c05f0a58ca6b073dcfcbacb333d2a78e0725e9d72012b2aa725f03')),
                'P12': ((50883, '97af30802aea371b231e6509df62743006218065b3decbeb3bcc3db94df98981'),
                        (1063, '9a10331a1876103db243e8bc7d4abc8a5c876bb00a7fea9abb4ab505a42dad55')),
            }[pid]
            status_size, status_digest = status_suffix
            status_begin = b'\n<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->\n'
            status_end = b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
            _require((len(data), hashlib.sha256(data).hexdigest()) == current and
                     len(data) >= status_size and data.endswith(status_end) and
                     data.count(status_begin) == data.count(status_end) == 1 and
                     data[-status_size:].startswith(status_begin) and
                     hashlib.sha256(data[-status_size:]).hexdigest() == status_digest,
                     'guard:capability_semantic_integrity:local_status_successor:' + pid)
            data = data[:-status_size]
            p1_suffix = {
                'P11': (837, '733268376667429162a6b5a62e8b1a2a695a271e695c3cda5869825e49bd4ede'),
                'P12': (772, 'aa49da5e056b8dca34a772d8d7c4da4ba5525037d9a2b5517bd8f673566eb367'),
            }[pid]
            p1_size, p1_digest = p1_suffix
            _require(len(data) >= p1_size and
                     hashlib.sha256(data[-p1_size:]).hexdigest() == p1_digest and
                     data[-p1_size:].count(b'<!-- RW0_C2_P1_PHYSICAL_CANDIDATE_BEGIN -->') == 1,
                     'guard:capability_semantic_integrity:p1_successor:' + pid)
            data = data[:-p1_size]
            suffix = {
                'P11': (644, '5a6268e7a6a848cf638e5092633d8e773bdf5b9d12498f5deb92aa9119523923'),
                'P12': (470, '07d99f5eab07a2d57d39a8ce5836ae062b523b2cdfc89c6d2c87f29a5d4bed6e'),
            }[pid]
            size, digest = suffix
            _require(len(data) >= size and
                     hashlib.sha256(data[-size:]).hexdigest() == digest and
                     data[-size:].count(b'<!-- RW0_C2_P0_PHYSICAL_CANDIDATE_BEGIN -->') == 1,
                     'guard:capability_semantic_integrity:p0_successor:' + pid)
            data = data[:-size]
        identity = (len(data), hashlib.sha256(data).hexdigest())
        _type_exact(identity, reference['replacement_identity'], boundary='guard:capability_semantic_integrity:identity:' + pid)
        _require(identity != reference['old_identity'], 'guard:capability_semantic_integrity:changed:' + pid)
        compact = ' '.join(data.decode('utf-8').split())
        for index, marker in enumerate(reference['semantic_markers']):
            _require(marker in compact, 'guard:capability_semantic_integrity:marker:' + pid + ':' + str(index))


@pytest.mark.parametrize('case,boundary', [
    ('pass', 'guard:capability_semantic_integrity:helper_body'),
    ('empty', 'guard:capability_semantic_integrity:helper_body'),
    ('call_only', 'guard:capability_semantic_integrity:compared_return'),
    ('ignored_return', 'guard:capability_semantic_integrity:compared_return'),
    ('no_op_compare', 'guard:capability_semantic_integrity:comparison_body'),
])
def test_capability_semantic_integrity_source_hostile(case, boundary):
    text = (ROOT / 'tests/test_rw0_b2_capability_boundaries.py').read_text()
    if case in ('pass', 'empty', 'no_op_compare'):
        tree = ast.parse(text)
        node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == ('_assert_capability_semantic_integrity' if case == 'no_op_compare' else '_guard_replacement_semantic_evidence'))
        lines = text.splitlines(keepends=True)
        lines[node.lineno:node.end_lineno] = ['    pass\n' if case in ('pass', 'no_op_compare') else '    return {}\n']
        changed = ''.join(lines)
    else:
        old = 'observed = _guard_replacement_semantic_evidence()'
        new = '_guard_replacement_semantic_evidence()' if case == 'call_only' else 'observed = CAPABILITY_REPLACEMENT_EXPECTED; _guard_replacement_semantic_evidence()'
        changed = text.replace(old, new, 1)
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_capability_semantic_source(changed)


@pytest.mark.parametrize('case', (
    'comment', 'string', 'readonly', 'second_dynamic', 'second_annotated',
    'inside_if', 'nonliteral', 'missing',
))
def test_capability_protected_literal_source_variants(case):
    source = (ROOT / 'tests/test_rw0_b2_capability_boundaries.py').read_text()
    if case in ('nonliteral', 'missing'):
        node = next(node for node in ast.parse(source).body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'PROTECTED_CONTENT_ROWS'
                            for target in node.targets))
        lines = source.splitlines(keepends=True)
        lines[node.lineno - 1:node.end_lineno] = (
            [] if case == 'missing' else
            ['PROTECTED_CONTENT_ROWS = CAPABILITY_REPLACEMENT_EXPECTED\n']
        )
        variant = ''.join(lines)
    else:
        additions = {
            'comment': '\n# PROTECTED_CONTENT_ROWS = dynamic_example\n',
            'string': "\nexample_text = 'PROTECTED_CONTENT_ROWS = dynamic_example'\n",
            'readonly': '\nfor observed_row in PROTECTED_CONTENT_ROWS:\n    pass\n',
            'second_dynamic': (
                '\nPROTECTED_CONTENT_ROWS = tuple('
                'tuple((row[0], row[1], len((ROOT / row[1]).read_bytes()), '
                'hashlib.sha256((ROOT / row[1]).read_bytes()).hexdigest(), row[4], row[5])) '
                'if row[0] in ("P11", "P12") else row for row in PROTECTED_CONTENT_ROWS)\n'
            ),
            'second_annotated': '\nPROTECTED_CONTENT_ROWS: tuple = tuple(PROTECTED_CONTENT_ROWS)\n',
            'inside_if': '\nif True:\n    PROTECTED_CONTENT_ROWS = tuple(PROTECTED_CONTENT_ROWS)\n',
        }
        variant = source + additions[case]
    if case in ('comment', 'string', 'readonly'):
        _assert_capability_semantic_source(variant)
    else:
        with pytest.raises(AssertionError,
                           match='^guard:capability_semantic_integrity:protected_single_literal$'):
            _assert_capability_semantic_source(variant)


@pytest.mark.parametrize('case,boundary', [
    ('fencing', 'guard_ordering_integrity:fencing_before_receipt'),
    ('replay', 'guard_ordering_integrity:replay_before_eligibility'),
    ('family', 'guard_ordering_integrity:eligibility_before_family'),
    ('model', 'guard_ordering_integrity:model_after_guard'),
])
def test_guard_ordering_integrity_hostile(case, boundary):
    text = (ROOT / GUARD).read_text(); decision_text = (ROOT / C2).read_text()
    if case == 'fencing':
        text = text.replace('Command-local grammar/basis and writer fencing precede private P1 receipt\nlookup.', 'Private P1 receipt lookup precedes command-local grammar/basis and writer fencing.', 1)
    elif case == 'replay':
        text = text.replace('Receipt presence requires fresh universal disclosure posture before\ncommand-digest association', 'Receipt presence checks command-digest association before fresh universal disclosure posture', 1)
    elif case == 'family':
        text = text.replace('construction/application of the atomic family', 'fresh acceptance-only eligibility', 1)
    else:
        decision_text = decision_text.replace('Only after all authoritative no-write gates, including the bootstrap guard,', 'Before the bootstrap guard,', 1)
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_guard_ordering_integrity(text, decision_text)


@pytest.mark.parametrize('human,machine,kind', [
    (True, 1, 'type'), (1, True, 'type'), (False, 0, 'type'), (0, False, 'type'),
    ('sibling', 'original', 'value'), (None, 'value', 'type'),
    ([True], [1], 'type'), ((1,), [1], 'type'),
])
def test_typed_human_machine_equivalence_guard_scalars(human, machine, kind):
    pointer = '/role/0' if type(human) is list and type(machine) is list else '/role'
    with pytest.raises(AssertionError, match='^' + re.escape('guard:human_machine_equivalence:' + pointer + ':' + kind) + '$'):
        _type_exact({'role': human}, {'role': machine})


@pytest.mark.parametrize('role,old,new,kind', [
    ('scope.active_authorities', '1', 'true', 'type'),
    ('relation.command_digest_covered', 'true', '1', 'type'),
    ('branch_effects.candidate_repair', '0', 'false', 'type'),
    ('terminal.mutates_guard', 'false', '0', 'type'),
    ('scope.identity', '"admitted_coordinator_authority_lineage"', '"sibling"', 'value'),
    ('family.separate_receipt', 'false', 'null', 'type'),
])
def test_typed_human_machine_equivalence_guard_document(role, old, new, kind):
    text = (ROOT / GUARD).read_text()
    changed = text.replace('| `' + role + '` | `' + old + '` |', '| `' + role + '` | `' + new + '` |', 1)
    with pytest.raises(AssertionError, match='^' + re.escape('guard:human_machine_equivalence:/' + role + ':' + kind) + '$'):
        _parse(changed)


@pytest.mark.parametrize('case,boundary', [
    ('bare_duplicate', 'guard:closed_human_table:duplicate:scope.identity'),
    ('duplicate', 'guard:closed_human_table:duplicate:scope.identity'),
    ('extra', 'guard:closed_human_table:extra:scope.extra'),
    ('missing', 'guard:closed_human_table:rows:Scope'),
    ('column', 'guard:closed_human_table:columns:Scope:1'),
    ('value', 'guard:closed_human_table:value:scope.identity'),
    ('header', 'guard:closed_human_table:header:Authority'),
    ('separator', 'guard:closed_human_table:separator:Authority'),
    ('pipe', 'guard:closed_human_table:columns:Scope:1'),
    ('cell', 'guard:closed_human_table:cell:scope.identity'),
])
def test_closed_human_table_hostile(case, boundary):
    text = (ROOT / GUARD).read_text()
    row = '| `scope.identity` | `"admitted_coordinator_authority_lineage"` |'
    replacements = {
        'bare_duplicate': row + '\n| scope.identity | database |',
        'duplicate': row + '\n| `scope.identity` | `"database"` |',
        'extra': row + '\n| scope.extra | "database" |',
        'missing': '', 'column': row + ' extra |',
        'value': '| `scope.identity` | not_json |',
        'pipe': '| `scope.identity` | `"lineage|database"` |',
        'cell': '| `scope.identity` | `"database" |',
    }
    if case == 'header': changed = text.replace('| Role | Exact semantic inventory |', '| Role | Meaning |', 1)
    elif case == 'separator': changed = text.replace('| --- | --- |', '| --- |', 1)
    else: changed = text.replace(row, replacements[case], 1)
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _parse_human_tables(changed)


def test_closed_human_table_accepts_legitimate_unbackticked_row():
    text = (ROOT / GUARD).read_text()
    changed = text.replace('| `scope.identity` | `"admitted_coordinator_authority_lineage"` |',
                           '| scope.identity | "admitted_coordinator_authority_lineage" |', 1)
    _type_exact(_parse_human_tables(changed), _parse_human_tables(text))


def _assert_operational_realization_inventory(cases):
    _require(type(cases) is tuple and cases == OPERATIONAL_REALIZATIONS, 'guard:operational_realization:case_inventory')


def test_operational_realization_fixed_completeness():
    text = ' '.join((ROOT / GUARD).read_text().split())
    match = re.search(r'A (deployment, .+?) creates neither lineage nor allowance merely by existing\.', text)
    _require(match is not None, 'guard:operational_realization:owner_inventory')
    parsed = tuple(item.replace(' ', '_') for item in re.split(r', (?:or )?', match[1]))
    _require(parsed == OPERATIONAL_REALIZATIONS, 'guard:operational_realization:owner_inventory')
    _assert_operational_realization_inventory(tuple(OPERATIONAL_REALIZATION_CASES))
    tree = ast.parse(Path(__file__).read_text())
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'test_operational_realization_never_admits_or_replenishes')
    parameter = next(node for node in node.decorator_list if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'parametrize')
    _require(ast.dump(parameter.args[1], include_attributes=False) == ast.dump(ast.Name(id='OPERATIONAL_REALIZATIONS', ctx=ast.Load()), include_attributes=False),
             'guard:operational_realization:parameter_inventory')


def test_operational_realization_missing_case_is_integrity_failure():
    with pytest.raises(AssertionError, match='^guard:operational_realization:case_inventory$'):
        _assert_operational_realization_inventory(OPERATIONAL_REALIZATIONS[1:])


@pytest.mark.parametrize('case', ['claimed_scope', 'unresolved_scope', 'lineage_mismatch', 'multiple_active',
                                  'accepted_recognized', 'accepted_unrecognized', 'candidate_repair',
                                  'attempt_selecting_replan', 'program_terminal_reject', 'post_execution_program_block', 'replay'])
def test_model_after_guard_exact_order(guard, decision, monkeypatch, case):
    _assert_actual_entry_case(guard, decision, monkeypatch, case)
    p = _posture(); state = _baseline(decision); previous = None
    if case == 'claimed_scope': p['claimed'] = True
    elif case == 'unresolved_scope': p['claimed'] = 'unknown'
    elif case == 'lineage_mismatch': p['expected_lineage'] = 'foreign'
    elif case == 'multiple_active': p['active'] = 2
    elif case == 'accepted_unrecognized': state['model_recommendation'] = 'out_of_vocabulary'
    elif case == 'replay':
        previous = _family(_interpret(decision, state)); p['claimed'] = True; state = {'not_a_fresh_basis': True}
    elif case in ('candidate_repair', 'attempt_selecting_replan', 'program_terminal_reject', 'post_execution_program_block'):
        p['claimed'] = 'unknown'; state = _state_for(decision, case)
    events = []
    for name, stage in (('_interpret_pre_model', 'authoritative_branch_derived'),
                        ('_acceptance_guard_eligibility', 'bootstrap_guard_evaluated'),
                        ('_model_consistency_phase', 'model_consistency_evaluated')):
        original = globals()[name]
        def spy(*args, _original=original, _stage=stage, **kwargs):
            events.append(_stage)
            return _original(*args, **kwargs)
        monkeypatch.setitem(globals(), name, spy)
    result = _evaluate(guard, decision, p, state, previous=previous)
    fresh = case not in ('lineage_mismatch', 'multiple_active', 'replay')
    acceptance = case in ('claimed_scope', 'unresolved_scope', 'accepted_recognized', 'accepted_unrecognized')
    passes = case not in ('claimed_scope', 'unresolved_scope', 'lineage_mismatch', 'multiple_active', 'replay')
    expected = (['authoritative_branch_derived'] if fresh else []) + (['bootstrap_guard_evaluated'] if acceptance else []) + (['model_consistency_evaluated'] if passes else [])
    _require(events == expected, 'guard:model_after_guard:phase_order:' + case)
    if case == 'replay':
        _type_exact(result, previous, boundary='guard:model_after_guard:replay')
        return
    trace = result['audit_trace']
    _require('model_consistency_evaluated' not in trace if not passes else trace[-1] == 'model_consistency_evaluated',
             'guard:model_after_guard:trace:' + case)
    if fresh:
        _require(trace.index('receipt_replay_checked') < trace.index('authoritative_branch_derived'), 'guard:model_after_guard:receipt_before_branch:' + case)
    if acceptance:
        _require(trace.index('authoritative_branch_derived') < trace.index('bootstrap_guard_evaluated'), 'guard:model_after_guard:branch_before_guard:' + case)
    if passes and acceptance:
        _require(trace.index('bootstrap_guard_evaluated') < trace.index('model_consistency_evaluated'), 'guard:model_after_guard:guard_before_model:' + case)
    if not passes:
        _require(result['outcome'] == 'no_write' and result['rejection'] == 'bootstrap_acceptance_guard_conflict', 'guard:model_after_guard:no_write:' + case)


# V3 observes function entry, including calls resolved in C2's defining module.
# This adapter exposes the existing absent/present receipt check and delegates
# all persisted-family semantics to the original C2 owner without reinterpreting it.
def _receipt_replay_check(previous, mutation, digest):
    if previous is None:
        return None
    return _replay_family(previous, mutation, digest)


# Fixed expectations from C2 normative steps 7-8 and guard's receipt-first prefix.
# All five valid final branches require model consistency after their no-write
# gates; only acceptance requires acceptance-only eligibility. Parsed behavior
# does not author these expectations.
ACTUAL_ENTRY_EXPECTED = {
    'claimed_scope': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'acceptance_guard_entered'),
    'unresolved_scope': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'acceptance_guard_entered'),
    'lineage_mismatch': (), 'missing_admission': (), 'foreign_admission': (),
    'multiple_active': (), 'unfenced': (), 'invalid_session': (),
    'accepted_recognized': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'acceptance_guard_entered', 'model_consistency_entered'),
    'accepted_unrecognized': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'acceptance_guard_entered', 'model_consistency_entered'),
    'candidate_repair': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'model_consistency_entered'),
    'attempt_selecting_replan': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'model_consistency_entered'),
    'program_terminal_reject': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'model_consistency_entered'),
    'post_execution_program_block': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered', 'model_consistency_entered'),
    'replay': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered'),
    'mutation_conflict': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered'),
    'family_route_collision': ('writer_or_session_fenced', 'receipt_or_collision_helper_entered', 'authoritative_pre_model_entered'),
}
MODEL_ENTRY_CASES = (
    'replay', 'lineage_mismatch', 'missing_admission', 'foreign_admission', 'multiple_active',
    'claimed_scope', 'unresolved_scope', 'accepted_recognized', 'accepted_unrecognized',
    'candidate_repair', 'attempt_selecting_replan', 'program_terminal_reject', 'post_execution_program_block',
)
REPLAY_ENTRY_CASES = (
    'unfenced', 'invalid_session', 'lineage_mismatch', 'missing_admission', 'foreign_admission',
    'accepted_recognized', 'replay', 'mutation_conflict', 'family_route_collision',
)
ACTUAL_ENTRY_ROLES = {
    'fence': ('_guard_relation', 'writer_or_session_fenced'),
    'receipt': ('_receipt_replay_check', 'receipt_or_collision_helper_entered'),
    'pre_model': ('_interpret_pre_model', 'authoritative_pre_model_entered'),
    'acceptance': ('_acceptance_guard_eligibility', 'acceptance_guard_entered'),
    'model': ('_model_consistency_phase', 'model_consistency_entered'),
    'persisted_replay': ('_replay_family', None),
}

# The C2 owner requires model consistency as the final stage for every valid
# branch. The guard owner adds acceptance-only eligibility and receipt-first
# replay. These code-entry expectations are fixed independently of returned
# traces and independently of the reference-patching probe above.
CODE_OBJECT_ENTRY_EXPECTED = {
    'replay': ('fence', 'receipt', 'persisted_replay'),
    'mutation_conflict': ('fence', 'receipt', 'persisted_replay'),
    'family_route_collision': ('fence', 'receipt', 'pre_model'),
    'unfenced': (), 'invalid_session': (),
    'lineage_mismatch': ('fence',), 'missing_admission': ('fence',),
    'foreign_admission': ('fence',), 'multiple_active': ('fence',),
    'claimed_scope': ('fence', 'receipt', 'pre_model', 'acceptance'),
    'unresolved_scope': ('fence', 'receipt', 'pre_model', 'acceptance'),
    'accepted_recognized': ('fence', 'receipt', 'pre_model', 'acceptance', 'model'),
    'accepted_unrecognized': ('fence', 'receipt', 'pre_model', 'acceptance', 'model'),
    'candidate_repair': ('fence', 'receipt', 'pre_model', 'model'),
    'attempt_selecting_replan': ('fence', 'receipt', 'pre_model', 'model'),
    'program_terminal_reject': ('fence', 'receipt', 'pre_model', 'model'),
    'post_execution_program_block': ('fence', 'receipt', 'pre_model', 'model'),
}
_CODE_OBJECT_OBSERVER_GATE = threading.Lock()
_ACTUAL_CALL_PROBE_GATE = threading.Lock()


@contextmanager
def _code_object_actual_entry_observer(targets):
    """Observe exact code-object entry, including prebound callable routes."""
    _require(_CODE_OBJECT_OBSERVER_GATE.acquire(blocking=False),
             'guard:code_object_actual_entry:nested')
    previous_sys_profile = sys.getprofile()
    previous_thread_profile = threading.getprofile()
    previous_sys_trace = sys.gettrace()
    previous_thread_trace = threading.gettrace()
    owner_thread = threading.get_ident()
    observed = {'events': [], 'counts': dict.fromkeys(targets, 0)}
    try:
        _require(type(targets) is dict and all(type(role) is str and type(target) is FunctionType
                                               for role, target in targets.items()),
                 'guard:code_object_actual_entry:targets')
        code_roles = tuple((target.__code__, role) for role, target in targets.items())
        _require(len({id(code) for code, _ in code_roles}) == len(code_roles),
                 'guard:code_object_actual_entry:duplicate_code')

        def profile(frame, event, arg):
            if event == 'call':
                for code, role in code_roles:
                    if frame.f_code is code:
                        observed['events'].append(role)
                        observed['counts'][role] += 1
                        break
            previous = (previous_sys_profile if threading.get_ident() == owner_thread
                        else previous_thread_profile)
            if previous is not None:
                previous(frame, event, arg)

        sys.setprofile(profile)
        threading.setprofile(profile)
        yield observed
    finally:
        sys.setprofile(previous_sys_profile)
        threading.setprofile(previous_thread_profile)
        sys.settrace(previous_sys_trace)
        threading.settrace(previous_thread_trace)
        _CODE_OBJECT_OBSERVER_GATE.release()


def _assert_code_object_actual_entries(actual, expected_events, targets, case):
    expected_counts = {role: expected_events.count(role) for role in targets}
    for role in targets:
        _require(actual['counts'][role] == expected_counts[role],
                 'guard:code_object_actual_entry:counts:' + role + ':' + case)
    _type_exact(tuple(actual['events']), expected_events,
                boundary='guard:code_object_actual_entry:order:' + case)


def _assert_actual_entry_owner_contract(decision):
    compact = ' '.join((ROOT / C2).read_text().split())
    _require('Only after all authoritative no-write gates, including the bootstrap guard, evaluate model-recommendation consistency.' in compact,
             'guard:actual_entry:owner_model_order')
    _require('This is always the last evaluation stage while the basis remains valid.' in compact,
             'guard:actual_entry:owner_all_branches')
    _type_exact(tuple(decision['branch_mapping']),
                ('candidate_acceptance', 'candidate_repair', 'attempt_selecting_replan', 'program_terminal_reject', 'post_execution_program_block'),
                boundary='guard:actual_entry:owner_branch_inventory')
    _require(decision['model']['evaluation_order'] == 'after_bootstrap_guard_gate',
             'guard:actual_entry:owner_model_order')
    _assert_guard_ordering_integrity((ROOT / GUARD).read_text(), (ROOT / C2).read_text())


def _record_actual_entry(probe, role, stage, expected_events, expected_counts, case):
    probe['counts'][role] += 1
    _require(expected_counts[role] != 0, 'guard:actual_entry:forbidden:' + role + ':' + case)
    _require(probe['counts'][role] <= expected_counts[role], 'guard:actual_entry:count:' + role + ':' + case)
    if stage is None:
        _require(probe['events'] and probe['events'][-1] == 'receipt_or_collision_helper_entered',
                 'guard:actual_entry:order:' + role + ':' + case)
    else:
        probe['events'].append(stage)
        _type_exact(tuple(probe['events']), expected_events[:len(probe['events'])],
                    boundary='guard:actual_entry:order:' + case)


def _actual_entry_wrapper(original, role, stage, probe, expected_events, expected_counts, case):
    def wrapped(*args, **kwargs):
        if role == 'fence':
            result = original(*args, **kwargs)
            if result is None:
                _record_actual_entry(probe, role, stage, expected_events, expected_counts, case)
            return result
        _record_actual_entry(probe, role, stage, expected_events, expected_counts, case)
        return original(*args, **kwargs)
    return wrapped


@contextmanager
def _actual_call_probe(monkeypatch, originals, expected_events, expected_counts, case):
    _require(_ACTUAL_CALL_PROBE_GATE.acquire(blocking=False), 'guard:actual_entry:nested_probe')
    probe = {'events': [], 'counts': dict.fromkeys(originals, 0), 'wrappers': {}, 'references': []}
    guard_module = sys.modules[__name__]
    try:
        with monkeypatch.context() as patcher:
            for role, original in originals.items():
                defining_module = sys.modules[original.__module__]
                _require(getattr(defining_module, original.__name__) is original,
                         'guard:actual_entry:defining_function:' + role)
                wrapped = _actual_entry_wrapper(original, role, ACTUAL_ENTRY_ROLES[role][1], probe,
                                                expected_events, expected_counts, case)
                probe['wrappers'][role] = wrapped
                # Snapshot all actual references before patching either namespace.
                modules = (defining_module,) if defining_module is guard_module else (defining_module, guard_module)
                aliases = [(module, name, value) for module in modules
                           for name, value in tuple(vars(module).items()) if value is original]
                registries = [(container, key, value) for module in modules
                              for container in tuple(vars(module).values()) if type(container) in (dict, list)
                              for key, value in (tuple(container.items()) if type(container) is dict else tuple(enumerate(container)))
                              if value is original]
                bound_attributes = []
                functions = {value for module in modules for value in tuple(vars(module).values())
                             if type(value) is type(_record_actual_entry)}
                for function in functions:
                    defaults = function.__defaults__
                    if defaults and any(value is original for value in defaults):
                        replacement = tuple(wrapped if value is original else value for value in defaults)
                        bound_attributes.append((function, '__defaults__', defaults, replacement))
                    if function.__kwdefaults__:
                        registries.extend((function.__kwdefaults__, key, value)
                                          for key, value in tuple(function.__kwdefaults__.items()) if value is original)
                    for cell in function.__closure__ or ():
                        try:
                            value = cell.cell_contents
                        except ValueError:
                            continue
                        if value is original:
                            bound_attributes.append((cell, 'cell_contents', value, wrapped))
                probe['references'].extend(('attribute', owner, name, value)
                                           for owner, name, value, replacement in bound_attributes)
                probe['references'].extend(('attribute', module, name, value) for module, name, value in aliases)
                probe['references'].extend(('item', container, key, value) for container, key, value in registries)
                patcher.setattr(defining_module, original.__name__, wrapped)
                for module, name, value in aliases:
                    patcher.setattr(module, name, wrapped)
                for owner, name, value, replacement in bound_attributes:
                    patcher.setattr(owner, name, replacement)
                for container, key, value in registries:
                    if type(container) is dict:
                        patcher.setitem(container, key, wrapped)
                    else:
                        # No list registry is used by the current oracle; retain
                        # an exact restoration path if one is supplied in a probe.
                        container[key] = wrapped
            yield probe
    finally:
        try:
            for kind, owner, key, original in probe['references']:
                if kind == 'item' and type(owner) is list:
                    owner[key] = original
            for kind, owner, key, original in probe['references']:
                restored = getattr(owner, key) if kind == 'attribute' else owner[key]
                boundary = ('guard:actual_entry:restoration:list'
                            if kind == 'item' and type(owner) is list
                            else 'guard:actual_entry:restoration')
                _require(restored is original, boundary)
        finally:
            _ACTUAL_CALL_PROBE_GATE.release()


def _actual_entry_case(decision, case):
    p = _posture(); state = _baseline(decision); previous = None; digest = 'D'
    if case == 'claimed_scope': p['claimed'] = True
    elif case == 'unresolved_scope': p['claimed'] = 'unknown'
    elif case == 'lineage_mismatch': p['expected_lineage'] = 'foreign'
    elif case == 'missing_admission': p['admission'] = None
    elif case == 'foreign_admission': p['admission'] = 'foreign'
    elif case == 'multiple_active': p['active'] = 2
    elif case == 'unfenced': p['writer_fenced'] = False
    elif case == 'invalid_session': p['writer_fenced'] = False
    elif case == 'accepted_unrecognized': state['model_recommendation'] = 'out_of_vocabulary'
    elif case == 'family_route_collision': state['admission_fault'] = 'family_route_collision'
    elif case in ('replay', 'mutation_conflict'):
        previous = _family(_interpret(decision, state)); p['claimed'] = True; state = {'not_a_fresh_basis': True}
        if case == 'mutation_conflict': digest = 'different'
    elif case in ('candidate_repair', 'attempt_selecting_replan', 'program_terminal_reject', 'post_execution_program_block'):
        p['claimed'] = 'unknown'; state = _state_for(decision, case)
    if case in ('unfenced', 'invalid_session', 'lineage_mismatch', 'missing_admission', 'foreign_admission'):
        previous = _family(_interpret(decision, _baseline(decision)))
    return p, state, previous, digest


def _assert_actual_entry_case(guard, decision, monkeypatch, case):
    _assert_actual_entry_owner_contract(decision)
    p, state, previous, digest = _actual_entry_case(decision, case)
    expected_events = ACTUAL_ENTRY_EXPECTED[case]
    expected_counts = {role: expected_events.count(stage) if stage is not None else int(case in ('replay', 'mutation_conflict'))
                       for role, (_, stage) in ACTUAL_ENTRY_ROLES.items()}
    originals = {role: globals()[name] for role, (name, _) in ACTUAL_ENTRY_ROLES.items()}
    with _actual_call_probe(monkeypatch, originals, expected_events, expected_counts, case) as probe:
        with _code_object_actual_entry_observer(originals) as actual:
            result = _evaluate(guard, decision, p, state, previous=previous, digest=digest)
        code_events = CODE_OBJECT_ENTRY_EXPECTED[case]
        _assert_code_object_actual_entries(actual, code_events, originals, case)
        for role in ('receipt', 'pre_model', 'acceptance', 'model', 'persisted_replay'):
            _require(probe['counts'][role] == actual['counts'][role],
                     'guard:code_object_actual_entry:probe_mismatch:' + role + ':' + case)
        _type_exact(probe['counts'], expected_counts, boundary='guard:actual_entry:counts:' + case)
        _type_exact(tuple(probe['events']), expected_events, boundary='guard:actual_entry:events:' + case)
    if case == 'replay':
        _type_exact(result, previous, boundary='guard:actual_entry:replay_projection')
    return probe, result


@pytest.mark.parametrize('case', MODEL_ENTRY_CASES)
def test_actual_model_entry_model_after_guard_actual(guard, decision, monkeypatch, case):
    _assert_actual_entry_case(guard, decision, monkeypatch, case)


@pytest.mark.parametrize('case', REPLAY_ENTRY_CASES)
def test_actual_replay_entry_fencing_before_replay_actual(guard, decision, monkeypatch, case):
    _assert_actual_entry_case(guard, decision, monkeypatch, case)


def test_actual_model_entry_defining_module_integrity(guard, decision, monkeypatch):
    defining_module = sys.modules[_interpret_pre_model.__module__]
    original = getattr(defining_module, '_model_consistency_phase')
    _require(original is _model_consistency_phase and original.__globals__ is vars(defining_module),
             'guard:actual_entry:defining_module_identity')
    p, state, previous, digest = _actual_entry_case(decision, 'accepted_recognized')
    events = ACTUAL_ENTRY_EXPECTED['accepted_recognized']
    counts = {role: events.count(stage) if stage is not None else 0 for role, (_, stage) in ACTUAL_ENTRY_ROLES.items()}
    originals = {role: globals()[name] for role, (name, _) in ACTUAL_ENTRY_ROLES.items()}
    with _actual_call_probe(monkeypatch, originals, events, counts, 'defining_module_integrity') as probe:
        _require(getattr(defining_module, '_model_consistency_phase') is probe['wrappers']['model'],
                 'guard:actual_entry:defining_module_wrapped')
        _require(_model_consistency_phase is probe['wrappers']['model'], 'guard:actual_entry:alias_wrapped')
        _evaluate(guard, decision, p, state, previous=previous, digest=digest)
        _type_exact(probe['counts'], counts, boundary='guard:actual_entry:defining_module_counts')
        _type_exact(tuple(probe['events']), events, boundary='guard:actual_entry:defining_module_order')
    _require(getattr(defining_module, '_model_consistency_phase') is original,
             'guard:actual_entry:defining_module_restored')


@pytest.mark.parametrize('role', ('model', 'persisted_replay'))
def test_actual_call_probe_hostile_alias_registry_and_restoration(monkeypatch, role):
    original = globals()[ACTUAL_ENTRY_ROLES[role][0]]
    defining_module = sys.modules[original.__module__]
    original_name = original.__name__
    monkeypatch.setitem(globals(), '_probe_extra_alias', original)
    registry = {'entry': original}
    monkeypatch.setitem(globals(), '_probe_bound_registry', registry)
    def default_entry(target=original):
        return target()
    def closure_entry():
        return original()
    monkeypatch.setitem(globals(), '_probe_default_entry', default_entry)
    monkeypatch.setitem(globals(), '_probe_closure_entry', closure_entry)
    boundary = 'guard:actual_entry:forbidden:' + role + ':zero_probe'
    for route in ('defining_module', 'alias', 'registry', 'default', 'closure'):
        with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
            with _actual_call_probe(monkeypatch, {role: original}, (), {role: 0}, 'zero_probe') as probe:
                if route == 'defining_module': getattr(defining_module, original_name)()
                elif route == 'alias': _probe_extra_alias()
                elif route == 'registry': registry['entry']()
                elif route == 'default': default_entry()
                else: closure_entry()
        _require(probe['counts'][role] == 1, 'guard:actual_entry:zero_probe_observed')
        _require(getattr(defining_module, original_name) is original and _probe_extra_alias is original and registry['entry'] is original and
                 default_entry.__defaults__[0] is original and closure_entry.__closure__[0].cell_contents is original,
                 'guard:actual_entry:all_references_restored')


@pytest.mark.parametrize('role', ('model', 'persisted_replay'))
def test_prebound_callable_actual_entry_bypasses_reference_probe(guard, decision, monkeypatch, role):
    # Capture the immutable tuple before any namespace replacement. The patch
    # probe cannot see this local reference; exact frame entry still can.
    prebound = (_model_consistency_phase, _replay_family)
    originals = {'model': prebound[0], 'persisted_replay': prebound[1]}
    family = _family({'branch': 'candidate_acceptance'})
    with _actual_call_probe(monkeypatch, originals, (), dict.fromkeys(originals, 0), 'prebound') as probe:
        with _code_object_actual_entry_observer(originals) as actual:
            if role == 'model':
                prebound[0](decision, {'outcome': 'no_write'})
            else:
                prebound[1](family, 'M', 'D')
        _require(probe['counts'][role] == 0, 'guard:prebound_callable_actual_entry:patch_probe_bypassed')
        boundary = 'guard:code_object_actual_entry:counts:' + role + ':prebound'
        with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
            _assert_code_object_actual_entries(actual, (), originals, 'prebound')


@pytest.mark.parametrize('variant,role', (
    ('tuple_discarded_model', 'model'),
    ('tuple_removed_trace_model', 'model'),
    ('tuple_early_and_normal_model', 'model'),
    ('tuple_discarded_replay', 'persisted_replay'),
    ('partial_model', 'model'),
    ('partial_replay', 'persisted_replay'),
    ('dynamic_getattr_defining_module', 'model'),
    ('new_function_same_code', 'model'),
    ('duplicate_replay_discard_first', 'persisted_replay'),
    ('exact_replay_then_fresh_model', 'model'),
    ('exact_replay_then_fresh_guard', 'acceptance'),
))
def test_prebound_callable_actual_entry_hostile(guard, decision, variant, role):
    prebound = (_model_consistency_phase, _replay_family)
    targets = {'model': prebound[0], 'persisted_replay': prebound[1],
               'acceptance': _acceptance_guard_eligibility}
    family = _family({'branch': 'candidate_acceptance'})
    prepared = {'outcome': 'no_write'}
    with _code_object_actual_entry_observer(targets) as actual:
        if variant == 'tuple_discarded_model':
            prebound[0](decision, prepared)
        elif variant == 'tuple_removed_trace_model':
            trace = ['model_consistency_evaluated']
            prebound[0](decision, prepared)
            trace.pop()
            _require(not trace, 'guard:prebound_callable_actual_entry:removed_trace')
        elif variant == 'tuple_early_and_normal_model':
            prebound[0](decision, prepared)
            prebound[0](decision, prepared)
        elif variant == 'tuple_discarded_replay':
            prebound[1](family, 'M', 'D')
        elif variant == 'partial_model':
            partial(prebound[0], decision, prepared)()
        elif variant == 'partial_replay':
            partial(prebound[1], family, 'M', 'D')()
        elif variant == 'dynamic_getattr_defining_module':
            getattr(sys.modules[prebound[0].__module__], prebound[0].__name__)(decision, prepared)
        elif variant == 'new_function_same_code':
            FunctionType(prebound[0].__code__, prebound[0].__globals__, 'same_code')(decision, prepared)
        elif variant == 'duplicate_replay_discard_first':
            prebound[1](family, 'M', 'D')
            prebound[1](family, 'M', 'D')
        elif variant == 'exact_replay_then_fresh_model':
            prebound[1](family, 'M', 'D')
            prebound[0](decision, prepared)
        else:
            prebound[1](family, 'M', 'D')
            targets['acceptance'](guard, _posture(), {'audit_trace': (), 'outcome': 'durable_decision'})
    expected = (('model',) if variant == 'tuple_early_and_normal_model'
                else ('persisted_replay',) if variant in ('duplicate_replay_discard_first',
                                                         'exact_replay_then_fresh_model',
                                                         'exact_replay_then_fresh_guard') else ())
    boundary = 'guard:code_object_actual_entry:counts:' + role + ':' + variant
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_code_object_actual_entries(actual, expected, targets, variant)


@pytest.mark.parametrize('exit_kind', ('normal', 'target_exception', 'caller_exception'))
def test_list_reference_restoration(monkeypatch, decision, exit_kind):
    original = _model_consistency_phase
    registry = [original]
    monkeypatch.setitem(globals(), '_probe_list_registry', registry)
    expected_events = ('model_consistency_entered',)
    counts = {'model': 1}
    if exit_kind == 'target_exception':
        with pytest.raises(KeyError, match='outcome'):
            with _actual_call_probe(monkeypatch, {'model': original}, expected_events, counts, exit_kind) as probe:
                _require(registry[0] is probe['wrappers']['model'], 'guard:list_reference_restoration:patched')
                registry[0](decision, {})
    elif exit_kind == 'caller_exception':
        with pytest.raises(RuntimeError, match='caller_exit'):
            with _actual_call_probe(monkeypatch, {'model': original}, expected_events, counts, exit_kind) as probe:
                _require(registry[0] is probe['wrappers']['model'], 'guard:list_reference_restoration:patched')
                raise RuntimeError('caller_exit')
    else:
        with _actual_call_probe(monkeypatch, {'model': original}, expected_events, counts, exit_kind) as probe:
            _require(registry[0] is probe['wrappers']['model'], 'guard:list_reference_restoration:patched')
            registry[0](decision, {'outcome': 'no_write'})
    _require(registry[0] is original and registry[0] is not probe['wrappers']['model'],
             'guard:actual_entry:restoration:list')
    with _actual_call_probe(monkeypatch, {'model': original}, (), {'model': 0}, 'second_probe') as second:
        _require(registry[0] is second['wrappers']['model'] and second['wrappers']['model'] is not probe['wrappers']['model'],
                 'guard:list_reference_restoration:second_probe')
    _require(registry[0] is original, 'guard:actual_entry:restoration:list')


def test_list_reference_restoration_nested_probe_boundary(monkeypatch):
    original = _model_consistency_phase
    registry = [original]
    monkeypatch.setitem(globals(), '_probe_list_registry', registry)
    with _actual_call_probe(monkeypatch, {'model': original}, (), {'model': 0}, 'outer'):
        with pytest.raises(AssertionError, match='^guard:actual_entry:nested_probe$'):
            with _actual_call_probe(monkeypatch, {'model': original}, (), {'model': 0}, 'inner'):
                pass
    _require(registry[0] is original, 'guard:actual_entry:restoration:list')


@pytest.mark.parametrize('exit_kind', ('normal', 'exception'))
def test_code_object_probe_restoration(exit_kind):
    def target():
        return 'entered'

    before = (sys.getprofile(), threading.getprofile(), sys.gettrace(), threading.gettrace())
    chained = {'sys_profile': 0, 'thread_profile': 0, 'sys_trace': 0, 'thread_trace': 0}
    owner = threading.get_ident()

    def prior_profile(frame, event, arg):
        if event == 'call' and frame.f_code is target.__code__:
            chained['sys_profile' if threading.get_ident() == owner else 'thread_profile'] += 1

    def prior_trace(frame, event, arg):
        if event == 'call' and frame.f_code is target.__code__:
            chained['sys_trace' if threading.get_ident() == owner else 'thread_trace'] += 1
        return prior_trace

    sys.setprofile(prior_profile)
    threading.setprofile(prior_profile)
    sys.settrace(prior_trace)
    threading.settrace(prior_trace)
    try:
        if exit_kind == 'exception':
            with pytest.raises(RuntimeError, match='observer_body_exit'):
                with _code_object_actual_entry_observer({'target': target}) as actual:
                    target()
                    raise RuntimeError('observer_body_exit')
            expected = ('target',)
        else:
            with _code_object_actual_entry_observer({'target': target}) as actual:
                target()
                child = threading.Thread(target=target)
                child.start()
                child.join(timeout=5)
                _require(not child.is_alive(), 'guard:code_object_probe_restoration:thread_join')
            expected = ('target', 'target')
        _assert_code_object_actual_entries(actual, expected, {'target': target}, exit_kind)
        for name, getter, wanted in (
            ('sys_profile', sys.getprofile, prior_profile),
            ('thread_profile', threading.getprofile, prior_profile),
            ('sys_trace', sys.gettrace, prior_trace),
            ('thread_trace', threading.gettrace, prior_trace),
        ):
            _require(getter() is wanted, 'guard:code_object_probe_restoration:' + name)
        _require(chained['sys_profile'] >= 1 and chained['sys_trace'] >= 1,
                 'guard:code_object_probe_restoration:chained_callbacks')
        if exit_kind == 'normal':
            _require(chained['thread_profile'] >= 1 and chained['thread_trace'] >= 1,
                     'guard:code_object_probe_restoration:chained_thread_callbacks')
    finally:
        sys.setprofile(before[0])
        threading.setprofile(before[1])
        sys.settrace(before[2])
        threading.settrace(before[3])


def test_code_object_probe_restoration_nested_boundary():
    def target():
        return None
    with _code_object_actual_entry_observer({'target': target}):
        with pytest.raises(AssertionError, match='^guard:code_object_actual_entry:nested$'):
            with _code_object_actual_entry_observer({'target': target}):
                pass


CROSS_PROGRAM_OUTCOMES = {'program_A': 'durable_decision', 'program_B': 'no_write'}


@dataclass(frozen=True)
class _GuardPosture:
    lineage: str
    scope: str
    admission_ref: str
    admission_digest: str
    applicability: str
    active_authorities: int


# Independent standing-admission evidence for the finite scenario. The builder
# consumes this fixture; it cannot amend its expected relationship.
CANONICAL_GUARD_POSTURE = _GuardPosture(
    lineage='L', scope='S', admission_ref='A', admission_digest='admission_digest_A',
    applicability='admitted_direct_local_bootstrap', active_authorities=1,
)
GUARD_POSTURE_EXPECTED = ('L', 'S', 'A', 'admission_digest_A', 'admitted_direct_local_bootstrap', 1)


def _assert_guard_posture_fixture(posture):
    _require(type(posture) is _GuardPosture, 'guard:cross_program_scenario:canonical_admission_posture')
    _type_exact((posture.lineage, posture.scope, posture.admission_ref, posture.admission_digest,
                 posture.applicability, posture.active_authorities), GUARD_POSTURE_EXPECTED,
                boundary='guard:cross_program_scenario:canonical_admission_posture')


def _cross_program_scenario(posture=CANONICAL_GUARD_POSTURE):
    return (
        {'label': 'unrelated_program_A', 'program_ref': 'program_A',
         'lineage': posture.lineage, 'scope': posture.scope, 'admission': posture.admission_ref,
         'admission_digest': posture.admission_digest, 'applicability': posture.applicability,
         'active_authorities': posture.active_authorities,
         'basis': ('program_A', 'program_A:head', 'program_A:basis'),
         'attempt_candidate': ('program_A:attempt', 'program_A:candidate'),
         'mutation_ref': 'mutation_A', 'command_digest': 'digest_A'},
        {'label': 'unrelated_program_B', 'program_ref': 'program_B',
         'lineage': posture.lineage, 'scope': posture.scope, 'admission': posture.admission_ref,
         'admission_digest': posture.admission_digest, 'applicability': posture.applicability,
         'active_authorities': posture.active_authorities,
         'basis': ('program_B', 'program_B:head', 'program_B:basis'),
         'attempt_candidate': ('program_B:attempt', 'program_B:candidate'),
         'mutation_ref': 'mutation_B', 'command_digest': 'digest_B'},
    )


def _assert_command_admission_binding(command, posture, label):
    _require(type(command.get('admission')) is str and command['admission'] == posture.admission_ref,
             'guard:cross_program_scenario:command_admission_binding:' + label)
    _require(type(command.get('admission_digest')) is str and command['admission_digest'] == posture.admission_digest,
             'guard:cross_program_scenario:command_admission_binding:' + label + ':digest')
    _require(command.get('lineage') == posture.lineage and command.get('scope') == posture.scope and
             command.get('applicability') == posture.applicability and
             type(command.get('active_authorities')) is int and command['active_authorities'] == posture.active_authorities,
             'guard:cross_program_scenario:command_posture_binding:' + label)


def _assert_cross_program_scenario(scenario, posture=CANONICAL_GUARD_POSTURE):
    _assert_guard_posture_fixture(posture)
    _require(type(scenario) is tuple and len(scenario) == 2 and all(type(row) is dict for row in scenario),
             'guard:cross_program_scenario:shape')
    a, b = scenario
    _require(type(a.get('admission')) is str and type(b.get('admission')) is str and
             a['admission'] == b['admission'], 'guard:cross_program_scenario:shared_admission:ref')
    _require(type(a.get('admission_digest')) is str and type(b.get('admission_digest')) is str and
             a['admission_digest'] == b['admission_digest'], 'guard:cross_program_scenario:shared_admission:digest')
    _require(all(type(row.get('program_ref')) is str and row['program_ref'] for row in scenario) and a['program_ref'] != b['program_ref'],
             'guard:cross_program_scenario:program_identity_distinct')
    _type_exact((a['program_ref'], b['program_ref']), ('program_A', 'program_B'),
                boundary='guard:cross_program_scenario:fixed_programs')
    for role in ('lineage', 'scope'):
        _type_exact(tuple(row.get(role) for row in scenario), (getattr(posture, role),) * 2,
                    boundary='guard:cross_program_scenario:shared_' + role)
    _assert_command_admission_binding(a, posture, 'A')
    _assert_command_admission_binding(b, posture, 'B')
    for row in scenario:
        program = row['program_ref']
        _type_exact(row['basis'], (program, program + ':head', program + ':basis'),
                    boundary='guard:cross_program_scenario:program_basis_binding')
        _type_exact(row['attempt_candidate'], (program + ':attempt', program + ':candidate'),
                    boundary='guard:cross_program_scenario:attempt_candidate_binding')
    for role in ('mutation_ref', 'command_digest'):
        _require(all(type(row.get(role)) is str and row[role] for row in scenario) and a[role] != b[role],
                 'guard:cross_program_scenario:command_identity_distinct:' + role)
    _type_exact((a['mutation_ref'], b['mutation_ref'], a['command_digest'], b['command_digest']),
                ('mutation_A', 'mutation_B', 'digest_A', 'digest_B'),
                boundary='guard:cross_program_scenario:fixed_command_coordinates')


def test_cross_program_scenario_integrity():
    _assert_cross_program_scenario(_cross_program_scenario())


@pytest.mark.parametrize('case,boundary', (
    ('program', 'guard:cross_program_scenario:program_identity_distinct'),
    ('basis', 'guard:cross_program_scenario:program_basis_binding:/0:value'),
    ('command', 'guard:cross_program_scenario:command_identity_distinct:mutation_ref'),
    ('scope', 'guard:cross_program_scenario:shared_scope:/1:value'),
    ('same_program_attempt', 'guard:cross_program_scenario:program_identity_distinct'),
))
def test_cross_program_scenario_integrity_hostile(case, boundary):
    scenario = deepcopy(_cross_program_scenario()); a, b = scenario
    if case == 'program': b['program_ref'] = a['program_ref']
    elif case == 'basis': b['basis'] = a['basis']
    elif case == 'command': b['mutation_ref'] = a['mutation_ref']; b['command_digest'] = a['command_digest']
    elif case == 'scope': b['scope'] = 'other_scope'
    else:
        b['program_ref'] = a['program_ref']; b['basis'] = a['basis']; b['attempt_candidate'] = ('program_A:attempt2', 'program_A:candidate2')
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_cross_program_scenario(scenario)


@pytest.mark.parametrize('case,boundary', (
    ('b_ref_coupled_expectation', 'guard:cross_program_scenario:shared_admission:ref'),
    ('b_digest_coupled_expectation', 'guard:cross_program_scenario:shared_admission:digest'),
    ('b_ref_and_digest', 'guard:cross_program_scenario:shared_admission:ref'),
    ('different_foreign_facts', 'guard:cross_program_scenario:shared_admission:ref'),
    ('same_foreign_fact', 'guard:cross_program_scenario:command_admission_binding:A'),
    ('same_foreign_digest', 'guard:cross_program_scenario:command_admission_binding:A:digest'),
    ('foreign_b_posture', 'guard:cross_program_scenario:shared_admission:ref'),
))
def test_shared_admission_integrity_hostile(case, boundary):
    scenario = deepcopy(_cross_program_scenario()); a, b = scenario
    if case == 'b_ref_coupled_expectation':
        b['admission'] = b['expected_admission'] = 'foreign_B'
    elif case == 'b_digest_coupled_expectation':
        b['admission_digest'] = b['expected_admission_digest'] = 'foreign_digest_B'
    elif case == 'b_ref_and_digest':
        b['admission'] = 'foreign_B'; b['admission_digest'] = 'foreign_digest_B'
    elif case == 'different_foreign_facts':
        a['admission'] = 'foreign_A'; b['admission'] = 'foreign_B'
    elif case == 'same_foreign_fact':
        a['admission'] = b['admission'] = 'foreign'
    elif case == 'same_foreign_digest':
        a['admission_digest'] = b['admission_digest'] = 'foreign_digest'
    else:
        b['admission'] = 'foreign_B'
        b['lineage'] = CANONICAL_GUARD_POSTURE.lineage
        b['scope'] = CANONICAL_GUARD_POSTURE.scope
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_cross_program_scenario(scenario)


@pytest.mark.parametrize('case,boundary', (
    ('ref_A', 'guard:cross_program_scenario:command_admission_binding:A'),
    ('ref_B', 'guard:cross_program_scenario:command_admission_binding:B'),
    ('digest_A', 'guard:cross_program_scenario:command_admission_binding:A:digest'),
    ('digest_B', 'guard:cross_program_scenario:command_admission_binding:B:digest'),
))
def test_command_admission_binding_hostile(case, boundary):
    scenario = deepcopy(_cross_program_scenario())
    index = 0 if case.endswith('A') else 1
    key = 'admission_digest' if case.startswith('digest') else 'admission'
    scenario[index][key] = 'foreign'
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_command_admission_binding(scenario[index], CANONICAL_GUARD_POSTURE, 'A' if index == 0 else 'B')


def test_shared_admission_integrity_coupled_builder_and_relation_expectation():
    coupled = _GuardPosture('L', 'S', 'foreign', 'foreign_digest',
                            'admitted_direct_local_bootstrap', 1)
    scenario = _cross_program_scenario(coupled)
    with pytest.raises(AssertionError, match='^guard:cross_program_scenario:canonical_admission_posture:/2:value$'):
        _assert_cross_program_scenario(scenario, coupled)


def _assert_actual_call_source(text):
    tree = ast.parse(text)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    probe = functions['_actual_call_probe']
    defining_patch = ast.parse('patcher.setattr(defining_module, original.__name__, wrapped)').body[0].value
    _require(any(isinstance(node, ast.Call) and ast.dump(node, include_attributes=False) == ast.dump(defining_patch, include_attributes=False)
                 for node in ast.walk(probe)), 'guard:actual_entry:source:defining_module_patch')
    _require(any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(probe)) and
             "'guard:actual_entry:restoration'" in ast.unparse(probe), 'guard:actual_entry:source:restoration')
    recorder = functions['_record_actual_entry']
    increment = ast.parse("probe['counts'][role] += 1").body[0]
    _require(any(isinstance(node, ast.AugAssign) and
                 ast.dump(node, include_attributes=False) == ast.dump(increment, include_attributes=False)
                 for node in ast.walk(recorder)), 'guard:actual_entry:source:actual_counter')
    zero_condition = ast.parse('expected_counts[role] != 0').body[0].value
    _require(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_require' and
                 node.args and ast.dump(node.args[0], include_attributes=False) == ast.dump(zero_condition, include_attributes=False)
                 for node in ast.walk(recorder)), 'guard:actual_entry:source:zero_sentinel')
    wrapper = functions['_actual_entry_wrapper']
    wrapped = next(node for node in wrapper.body if isinstance(node, ast.FunctionDef))
    _require(len(wrapped.body) == 3 and isinstance(wrapped.body[1], ast.Expr) and
             isinstance(wrapped.body[1].value, ast.Call) and isinstance(wrapped.body[1].value.func, ast.Name) and
             wrapped.body[1].value.func.id == '_record_actual_entry' and isinstance(wrapped.body[2], ast.Return),
             'guard:actual_entry:source:record_before_delegate')
    runner = functions['_assert_actual_entry_case']
    _require('_actual_call_probe' in ast.unparse(runner) and
             "_type_exact(probe['counts'], expected_counts" in ast.unparse(runner) and
             "_type_exact(tuple(probe['events']), expected_events" in ast.unparse(runner),
             'guard:actual_entry:source:counts_and_order')
    direct = functions['test_actual_model_entry_defining_module_integrity']
    _require('sys.modules[_interpret_pre_model.__module__]' in ast.unparse(direct) and
             'defining_module_wrapped' in ast.unparse(direct) and "probe['counts']" in ast.unparse(direct),
             'guard:actual_entry:source:direct_integrity')
    scenario = functions['_assert_cross_program_scenario']
    _require(all(marker in ast.unparse(scenario) for marker in ('program_identity_distinct', 'program_basis_binding', 'command_identity_distinct', 'shared_')),
             'guard:actual_entry:source:scenario_coordinates')
    for name in ('test_actual_call_probe_hostile_alias_registry_and_restoration', 'test_cross_program_scenario_integrity_hostile'):
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'raises':
                _require(any(keyword.arg == 'match' for keyword in node.keywords), 'guard:actual_entry:source:exact_hostile_boundary')


def _assert_code_object_and_admission_source(text):
    tree = ast.parse(text)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    observer = functions['_code_object_actual_entry_observer']
    observer_text = ast.unparse(observer)
    _require('target.__code__' in observer_text and 'frame.f_code is code' in observer_text and
             "event == 'call'" in observer_text and 'observed[\'counts\'][role] += 1' in observer_text and
             'sys.setprofile(profile)' in observer_text and 'threading.setprofile(profile)' in observer_text,
             'guard:code_object_actual_entry:source:exact_frame_entry')
    _require(all(marker in observer_text for marker in (
        'sys.setprofile(previous_sys_profile)', 'threading.setprofile(previous_thread_profile)',
        'sys.settrace(previous_sys_trace)', 'threading.settrace(previous_thread_trace)')) and
             any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(observer)),
             'guard:code_object_actual_entry:source:callback_restoration')
    runner = ast.unparse(functions['_assert_actual_entry_case'])
    _require('_code_object_actual_entry_observer(originals)' in runner and
             '_assert_code_object_actual_entries(actual, code_events, originals, case)' in runner and
             "probe['counts'][role] == actual['counts'][role]" in runner,
             'guard:code_object_actual_entry:source:post_invocation_reconciliation')
    bypass = ast.unparse(functions['test_prebound_callable_actual_entry_bypasses_reference_probe'])
    variants = ast.unparse(functions['test_prebound_callable_actual_entry_hostile'])
    _require('prebound = (_model_consistency_phase, _replay_family)' in bypass and
             '_actual_call_probe(' in bypass and '_code_object_actual_entry_observer(' in bypass and
             'partial(' in variants and 'getattr(' in variants and 'FunctionType(' in variants,
             'guard:code_object_actual_entry:source:prebound_routes')
    probe = ast.unparse(functions['_actual_call_probe'])
    _require('if type(container) is dict else tuple(enumerate(container))' in probe and
             "kind == 'item' and type(owner) is list" in probe and 'owner[key] = original' in probe,
             'guard:actual_entry:source:list_restoration')
    list_test = ast.unparse(functions['test_list_reference_restoration'])
    _require("registry = [original]" in list_test and "registry[0] is probe['wrappers']['model']" in list_test and
             "registry[0] is original" in list_test and "'second_probe'" in list_test,
             'guard:actual_entry:source:list_dynamic_coverage')
    builder = ast.unparse(functions['_cross_program_scenario'])
    relation = ast.unparse(functions['_assert_cross_program_scenario'])
    binding = ast.unparse(functions['_assert_command_admission_binding'])
    _require(all('posture.' + field in builder for field in ('lineage', 'scope', 'admission_ref',
                                                              'admission_digest', 'applicability', 'active_authorities')) and
             "a['admission'] == b['admission']" in relation and
             "a['admission_digest'] == b['admission_digest']" in relation and
             "command['admission'] == posture.admission_ref" in binding and
             "command['admission_digest'] == posture.admission_digest" in binding and
             "_assert_command_admission_binding(a, posture, 'A')" in relation and
             "_assert_command_admission_binding(b, posture, 'B')" in relation and
             '_assert_guard_posture_fixture(posture)' in relation,
             'guard:cross_program_scenario:source:independent_admission_relation')
    behavior = functions['test_cross_program_ceiling_and_independent_lineages']
    loop = next(node for node in ast.walk(behavior) if isinstance(node, ast.For) and
                isinstance(node.target, ast.Tuple) and
                tuple(item.id for item in node.target.elts if isinstance(item, ast.Name)) == ('label', 'command'))
    _require(ast.dump(loop.body[0], include_attributes=False) ==
             ast.dump(ast.parse('_assert_command_admission_binding(command, posture, label)').body[0], include_attributes=False) and
             "scope_key = (command['lineage'], command['scope'], command['admission'], command['admission_digest'])" in ast.unparse(loop) and
             "p['claimed'] = scope_key in ledger" in ast.unparse(loop),
             'guard:cross_program_scenario:command_admission_binding:preledger_source')


def test_code_object_actual_entry_source_integrity():
    _assert_code_object_and_admission_source(Path(__file__).read_text())


@pytest.mark.parametrize('case,boundary', (
    ('code_identity', 'guard:code_object_actual_entry:source:exact_frame_entry'),
    ('count_reconciliation', 'guard:code_object_actual_entry:source:post_invocation_reconciliation'),
    ('list_restore', 'guard:actual_entry:source:list_restoration'),
    ('preledger', 'guard:cross_program_scenario:command_admission_binding:preledger_source'),
    ('shared_ref', 'guard:cross_program_scenario:source:independent_admission_relation'),
    ('binding_ref', 'guard:cross_program_scenario:source:independent_admission_relation'),
))
def test_code_object_actual_entry_source_hostile(case, boundary):
    source = Path(__file__).read_text()
    old, new = {
        'code_identity': ('frame.f_code is code', 'frame.f_code == code'),
        'count_reconciliation': ("probe['counts'][role] == actual['counts'][role]", 'True'),
        'list_restore': ('owner[key] = original', 'pass'),
        'preledger': ('_assert_command_admission_binding(command, posture, label)', 'pass'),
        'shared_ref': ("a['admission'] == b['admission']", 'True'),
        'binding_ref': ("command['admission'] == posture.admission_ref", 'True'),
    }[case]
    _require(old in source, 'guard:code_object_actual_entry:source:hostile_construction')
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_code_object_and_admission_source(source.replace(old, new, 1))


def test_actual_call_probe_source_integrity():
    _assert_actual_call_source(Path(__file__).read_text())


@pytest.mark.parametrize('case,boundary', (
    ('defining_patch', 'guard:actual_entry:source:defining_module_patch'),
    ('restoration', 'guard:actual_entry:source:restoration'),
    ('record', 'guard:actual_entry:source:record_before_delegate'),
    ('counts', 'guard:actual_entry:source:counts_and_order'),
    ('coordinates', 'guard:actual_entry:source:scenario_coordinates'),
))
def test_actual_call_probe_source_hostile(case, boundary):
    text = Path(__file__).read_text()
    old, new = {
        'defining_patch': ('patcher.setattr(defining_module, original.__name__, wrapped)', 'patcher.setattr(guard_module, original.__name__, wrapped)'),
        'restoration': ("'guard:actual_entry:restoration'", "'ignored_restoration'"),
        'record': ('_record_actual_entry(probe, role, stage, expected_events, expected_counts, case)\n        return original', 'original(*args, **kwargs)\n        return original'),
        'counts': ("_type_exact(probe['counts'], expected_counts", "_type_exact(expected_counts, expected_counts"),
        'coordinates': ("'guard:cross_program_scenario:program_identity_distinct'", "'label_only'"),
    }[case]
    _require(old in text, 'guard:actual_entry:source:hostile_construction')
    changed = text.replace(old, new, 1)
    with pytest.raises(AssertionError, match='^' + re.escape(boundary) + '$'):
        _assert_actual_call_source(changed)


# Fixed identities for the accepted local-commit status successor. The
# predecessor values are the exact 8704e6c source bytes, not values derived
# from the document currently under test.
_RW0_C2_STATUS_DOCUMENT_IDENTITIES = {
    '.docs/architecture.md': ((47673, 'f97ca75f31e4ba07960bc5ce3a163ea073647308edcadf6b907326b12e76c185'), (46550, 'b4c2842a7bbb7250773c61f32a393b5217fb92b9031135e721e591f9481d5b5a'), (1123, 'ee1a733b8cbcbc125dcb69e1914d4053394db7052dfcb90119c9ea82dabf4085')),
    '.docs/autonomous-software-development-operating-model.md': ((44606, '142d5de8ec88946797abee43c663656769aaa020ee004afd87ea5270b0eed70b'), (43426, '967b3923b3baaa4b13c4c4fdd6c3931cfedea87ed77b05616365250973abe268'), (1180, '3984c7dfdf027b7d8b65fb490f7e0c089936ef438cf567699595ea7cec3523fe')),
    '.docs/c2b-durable-development-state.md': ((1905508, '021017a920a4cc522ca8470f31aa0ebdc2f4888724b897efcbaf30e643ff4b6c'), (1903684, 'db3575b1e4e5af92b06e3c824c5edf37e68b6ce66bc0098c17d0967885cbf19d'), (1824, 'cb0022d57602d7f01b2248311f08772515647db528c08f7bc0121be37e608a91')),
    '.docs/c2b2-migration-0002.md': ((9910, '32b0a2b8c6f5844ba38c368529a646f7534382ec2e315dda98322b8a3c49f8ed'), (9016, '06694d621f29e47147da89a43a8272c40cb67503bf52adeaa4a00edff0b0b2fc'), (894, '9fe7b6a96e910b01f198363a0f4cbbd694343489fadf8656859e76c500f4d72c')),
    '.docs/rw0-c2-durable-progression-decision-semantic-contract.md': ((78615, '9b5681e2bf0baaa39f3a952d685eb2f8b53b36e885ae2ac35d33599fa66c6c5f'), (77504, 'e79085d0187d9609837346f689258cca5b48c5af0c451863c8bfc020c5fb61cd'), (1111, '702a1061bf3f2c4d0c3c8c6fab3c6773181052822a426e7896832521b71b4ac6')),
    '.docs/rw0-c2-physical-p0-p1-implementation.md': ((19787, '0521d72f3efd40ba98dbed46cd83188fed72885e8c6261c7a7e26f6b2f20cf09'), (17353, '8f8da7a1f0da21a30a5dad72b95e50e3122314a0ec295bd6d10979ffee06d437'), (2520, 'd50d033f463df885d476d1be9a411f15172fc12b2c51c6aeaf20ea7fcd768860')),
    '.docs/rw0-c2-private-value-versioning.md': ((219832, '94cab1875ff34d42ad2aebe8c62c8450a845116b19117970382e72a8069f830c'), (219007, '3ba06106f2cfe11df4f827fb2bf82d8138623522e559cb65e49cb4942aeeb4d4'), (825, '354368e0a34b0f33b87ce2ab4b0414cb298f1612388befc5b97e64f301917220')),
    '.docs/sqlite-bootstrap-and-migrations.md': ((39203, 'bb43419ac210f3cf79240fed0cdf65c350bf089aca27448f4d32ca75aca281f3'), (38375, 'df6811bd85835f6fe324c2e495e315c3a21f502920707e885819284643206704'), (828, '00fd81d6ac60563bd1b21e3dd581f6d48fce11da2ec69e1eb75a70e3c4b3a539')),
    '.docs/sqlite-operations-and-recovery.md': ((44035, '6c37bce23e6c06b7a7e52511a8bef16943dd10e3edac14307c274a9971e7fcd2'), (43072, '9edee2aaba5d0285b7cc0b83fb485479a34caaf41665e7ed0ae23abe8002a514'), (952, 'f4aeb9e1bd234d3318f6aae2040016d69900f102788307ce969941e59708a694')),
    '.docs/sqlite-schema-v1.md': ((26209, '1377bfff325ca86b1dea93a08612edbfe338e6ee39d0dab82322eb36d17dbd90'), (25374, 'f4dbbc8f10a6022957899e7e98f6afbe9890845ae917a4791f5890ba665a0a29'), (835, '6698529c198c538ab8b9025e0200b71b8f305d3126c6154420527e2da4cebf52')),
    '.docs/sqlite-state-backend-adr.md': ((35543, 'ab26abb8ccb2eef1b22a4fc3e90301031c49bea8e3fe904d06de6dd75c648ab4'), (34760, 'dd5e9a5491ee10a7eab7fa555712f1c57dc7d362eed28b4b381b3c8292503296'), (783, 'e60d1d9cc381da2fa782d0228bfbb6db19a90d0de7358cdbfd1d62625265ee41')),
    'AGENTS.md': ((74410, 'c8ccf0552265d172a659a30be898fffd35cc70fad4821a350c3a9bf00e8f6b5d'), (72746, 'b4fcb9789db884d1c7962d3196e6c6bac1fa6b6c968ab8a2493cc7301f569d77'), (1664, '35b0ef1755c05f0a58ca6b073dcfcbacb333d2a78e0725e9d72012b2aa725f03')),
    'README.md': ((50883, '97af30802aea371b231e6509df62743006218065b3decbeb3bcc3db94df98981'), (49820, '8a10258ae59c52a3bdb254975ac782fa6a7a6b0f0dbdbd7c9dbc79764f733760'), (1063, '9a10331a1876103db243e8bc7d4abc8a5c876bb00a7fea9abb4ab505a42dad55')),
}
# Explicitly authorized 0008 normal-terminal successor. Each pair pins the
# complete current document and the exact appended successor. Stripping it
# must recover the already pinned P0/P1 local-commit bytes above.
_RW0_NORMAL_TERMINAL_STATUS_IDENTITIES = {
    '.docs/architecture.md': ((48680, '382235ce4b8374e4af9c9e4c58f106bfad685d1e281130f49fad85ef10f62463'), (1007, '42f42c9dcfe176d4a95b3a204177c38c661e37be6f00aed94fbf377214b30053')),
    '.docs/autonomous-software-development-operating-model.md': ((45578, 'bfc134807c33a59d595121151193d3d6dfe76959eb964bd8d66a12a8a179c26c'), (972, '3af788a782a0f2e504128e3d5adcd7e64620430c3ddf58e780dda24a7abebb0a')),
    '.docs/c2b-durable-development-state.md': ((1906502, 'aeee29055e776d6c55f689d1de03cb0fa647e1c46e001d22ec8a7451859a54ed'), (994, 'b90b2b2b1f3cca2aee41db543d828b373e34f29c906514ad04466dd6b08ef0b1')),
    '.docs/c2b2-migration-0002.md': ((11408, 'ba9ecfe211c47810d9ec1b7d792a031783654665fb009c22217be4819646ccb4'), (1498, 'ca763e43cd47ad30f5320f34dd1ab09426025632930aadb7f8c9688d15a9d9f0')),
    '.docs/rw0-c2-durable-progression-decision-semantic-contract.md': ((79662, '579e89e87a9c4d8e5da53d6aa91ef331f1bce3d0e83e8a615ff87b4d2a66edc3'), (1047, '8a4361e7049d4b07349f87807c43d841fc2e763bf662fcf69c3586b8a75ad88d')),
    '.docs/rw0-c2-physical-p0-p1-implementation.md': ((20895, '5939195ff98198890e6a29ee9cf915597e96e364693478d2434f50236b184ef4'), (1108, 'aec04bc397687bda1fa0327109dcf95bbac21895e7f1c8e2516c873e64e7a718')),
    '.docs/rw0-c2-private-value-versioning.md': ((220832, '908e08d924300b94d2e3aa726a2575bdaab3a24784aa21630c96d35791d79468'), (1000, 'a5b6e5bd5964743bc3c5aede0d37a6bf8f7b75cc55ba73c2dca4be789e5f9cd6')),
    '.docs/sqlite-bootstrap-and-migrations.md': ((40363, '3514a6d100cbc647b6cc8e45a9e94456256d4431d1a29587feefa397e4932902'), (1160, 'b1eb7c0a10e66c586a38b5941c5e7fba7160fac3ed09da642bc0cd06eb724534')),
    '.docs/sqlite-operations-and-recovery.md': ((46103, 'b163068f9113e576db29b8b92503efbc5056dcd38bf1b4a5dee9388c16ad70a6'), (2068, 'a2475e04e1293ba95d7dd6802f539d7239f7e01822e10d1652ca4397a5d9b558')),
    '.docs/sqlite-schema-v1.md': ((27211, '2cf2b5e18e4eb9c45b0395556e4304465445d701936549221b40525da46378dd'), (1002, '6266edab744892004a76db1d79aae5829277cba328a0c4ac227930cd6a844c02')),
    '.docs/sqlite-state-backend-adr.md': ((36628, 'f94ac9a85674bae068abe5262198cf36c9c17567b9c9042db90debca23fd47e1'), (1085, 'aee0d57623196e106bf901006be9b9060be1815140720c758d61380c69bbb4ea')),
    'AGENTS.md': ((75552, '4d947ee8f6b20e40f6f20755ae3a28fd5603ca99dda97cb436fa35dd0db7c482'), (1142, '84f8d8ea0a360c9ed20ec654b0b6f6abf58578e2f39a3395f312ad4ea13a8110')),
    'README.md': ((51873, 'b1fff34a97decde7e14eb8f346b3568aee97cb539f7da1e9d4f7f2e9aab9f96f'), (990, '58d4e8e08df9f7cc6ee93722a25292f4f9c4d84ebc21a8fa4d7d65e74edc988a')),
}
_RW0_NORMAL_TERMINAL_OTHER_IDENTITIES = {
    '.docs/durable-state-model.md': ((45175, '3bd5597bff63d05f03fef0f841d2294cdfe087bad1d10d226fde3700f44797ad'), (1019, '03df0a095f3937751cbd0124ab650e65e0b31ca727a3791f1b18f5f84a191f9a')),
    '.docs/worker-execution-boundary.md': ((35488, 'e4029cd33dee5c1b81b5c74897620d69aaf90a28f8570bbf455882fda58763d4'), (972, '6d6af7a601682948db89982fa7e0ab609b5a4e6d34ee1040861bb74a619e1412')),
    '.docs/rw0-remote-worker-contact-phase-entry.md': ((62651, '97433cddf62d795c04680a611425dc1132094c784b41f1d564ce742c3d3b02b0'), (1032, 'ce5f018db674f72d072eb6a7f200bee578d23a7e1d7d1641249ea750482af763')),
    '.docs/software-development-progression-boundary.md': ((29615, 'd76f13ace3759ed6f7dc586142254b4aac092e8a177adad1b0435f96329aca92'), (961, '7c9cbc5f08da2e653823990937fcd2fce8eade9262cb464a920a0974901ae409')),
}


# Opening integration-tree predecessors and exact status-only successors.
# These are fixed literals from the verified bc10382e tree and this patch;
# no test derives an expected identity from the document under test.
_RW0_POST_MERGE_STATUS_IDENTITIES = {
    '.docs/architecture.md': ((51426, '2381e1afc3b22e6414beaf48c679109fbf5e8e8eb4f48aae68f43224c10178e5'),
        (54198, '99b0a3f2b3b542a33aef92d0a65f211cc1023f0ab66fa1c6e91e403e6a3ef2fb')),
    '.docs/authority-boundaries.md': ((41922, '4e8d0a5f499b31fc83e7144abd0a38c463983e2540ee8567ced9ebc08c9b0549'),
        (44694, '00bf49de620acd584c361e692609b1c4eed96fa5d840f252286b930a4b301a5a')),
    '.docs/autonomous-software-development-operating-model.md': ((48324, '18dc97e1092ad41d5d747d71cc468447597abae2ea6ab0ddb82fce854add34b7'),
        (51096, '2f44ff23e06e5cea2379662827b0723ad07d599d275c5710d9821ec0e4fa63d3')),
    '.docs/c2b-durable-development-state.md': ((1909248, 'bdf3ed6a8189dedd224c2d742884429aeda13d799ecf13a1fa16c2c1c991d274'),
        (1912020, '5f83b36c09133a943a3581390ab832705eec3ed042da8eb96648e212ae0dea27')),
    '.docs/c2b2-migration-0002.md': ((14154, 'cbacd025ffb8524b9769c75cf0ad2be026f5b6b7ed9730e754fa5704f864b71b'),
        (16926, '1b419f6531069c046df4c270eb4af05aa68b5dec867e4ec592c61c7a9683b2ac')),
    '.docs/durable-state-model.md': ((47921, '13523fdfa4dd5344dc4a95de7c090afc339a2516bd97b630e645940b913d3ed0'),
        (50693, '84a1fc957b36ee808a693e381b82a0ee0e1a43c49c8f3e08a06dbd82a76e77a6')),
    '.docs/rw0-b1-pure-phase-values.md': ((38882, '966dfe81ecba50b8e185dc47f69a463869485e552c6fa5001cfcbc9d4249108a'),
        (41654, '6c092734b4858ce44e4322c200dbfef168752927ba08c1b64db51ec4bd2f8a03')),
    '.docs/rw0-b2-wire-protocol.md': ((29964, '502a6bf83a994dfece29726d695b57722dc4e512b36f7d95eef12bee65032b65'),
        (32736, '117f23cf90721c99cb45c32e35b67a4f229d3ff1e7972db89dd43596efc76682')),
    '.docs/rw0-c2-durable-progression-decision-semantic-contract.md': ((82408, '7393061f61c4a783277be41e149b2ae9b3fc49a06ac5c1ee01e53f361aadc056'),
        (85180, '876923f251fc37a55e53716bd7216d89240f969bb8f4c328d75a78541c152c81')),
    '.docs/rw0-c2-first-live-proof-posture.md': ((22074, '1bf09d17266debd5b0758d8ac7e2592734bfae02e35a13d86ae5e8e778239cf1'),
        (24846, 'b8379c26992668d285bc4ead0d19c8b30e66c181f8d005a63c180eae7f9ca686')),
    '.docs/rw0-c2-physical-p0-p1-implementation.md': ((23641, '9b78a53abf6583a09dd3de207452ddbf6e5f5d655af027f44f309d5f4b5512b9'),
        (26413, '6505ace56cb53232e64e8be2da3bd2ca8aca2a8eda8b238d51c6f432353530be')),
    '.docs/rw0-c2-private-value-versioning.md': ((223578, '267220a7e81400b31bb33bbc71b2e2d79b673e62a24c6828e4d3de4886a209b6'),
        (226350, '3f5a78c3107c3021222eb185d5aecbed0994b823bb1025bec6aff7be4aed9b69')),
    '.docs/rw0-c2-scope-admission-provisioning-contract.md': ((29620, 'd99c216cdcf1fb72fab2a85746ce9f72b27f6d929f8f3294de2dbb96324ddd02'),
        (32392, 'e1457940a4228e2cacf04e69476d1f8b56928debdb7bc5505c48f3f604297966')),
    '.docs/rw0-d1-offline-process-and-capsule-spine.md': ((9442, '1b943647fdbbeec3e6f5d25da94591ced2fb385a5fb9813d921131c34f9e3753'),
        (12214, '7b2335ccafbb12d425f9abbe1051a0052ca338dbbe984bafad0604119c6951a5')),
    '.docs/rw0-remote-worker-contact-phase-entry.md': ((65397, '2021ae46e8dce5d40057d1cf84d69177db2a63953f488716322ea9f2d49cd7c2'),
        (68169, 'c3c9d4168bb41eac9e5e86f63e4bc2ea5731005586488fff0b3fcebc30316401')),
    '.docs/rw0-terminal-outcome-physical-closure.md': ((19889, '8dc761f3be97905fa980a31df04dcd3bc36e781b51af65ffa052050739ad953e'),
        (22661, '2a4d9d6ab013e3abbb828417e9cf4e74d45550102658be19452b56dba152f02e')),
    '.docs/software-development-progression-boundary.md': ((32361, 'ff4bf801de9101892a28ffb992d4ad620ab38065097d95e24cb17b33e35d4df7'),
        (35133, '181f48db9081381e739aee7d873aa1eaed4993c692494afacda6c5c120fe3676')),
    '.docs/sqlite-bootstrap-and-migrations.md': ((43109, '95feb34848d62ba55d3bac7a67d187f85db20b8144da6b282044e2fa3fb1dbc0'),
        (45881, '8c685e1e672747dc24c8dff2c765b268e1c76884bc752b40d9b122cec84d23bf')),
    '.docs/sqlite-operations-and-recovery.md': ((48849, '4c6030ecaa25fe6aba170e89973553ed4c3d6c548ecd6c3791b7795692e5d37e'),
        (51621, 'c06e2b08619f1f121f2bfeee3bd7b56120be0ae30ed4a682abf3449cffa4aef1')),
    '.docs/sqlite-schema-v1.md': ((29957, 'f302822cf32c9ff478c1c7f37351211e1fc97a47e8558b3b2ecd021648f57ea4'),
        (32729, '32f1f9d9994e2e2b9c4f5042ff2704cf8a5aa8aa05dd27782c595e145833b64b')),
    '.docs/sqlite-state-backend-adr.md': ((39374, '9c4ec4237034fca9ef292df6d0c12bbcc02df257d1d7658e725e4bfb268a27a9'),
        (42146, 'a008461489d16e82a39ede0fa9691d187df76de153be95014b2217d1d5128207')),
    '.docs/worker-execution-boundary.md': ((38234, 'deb4e0a9572ae43f1b80bf23a282e85b52b6adb329f0fe87fe5253e4cc66fa1f'),
        (41006, '75b7bc80bd90127fdda4773795ffc0e13e8b570b5aceb73be331555a717e0c9c')),
    '.docs/writer-session-authority.md': ((61686, 'd1c1468496d33ecc50410ac62abfb60c58129b3a7535f6856d9661f8980325a2'),
        (64458, '89f24e3c41467d33c04b84d6112e99268f3ab96d2af31d9fcb81ec8a6469c314')),
    'AGENTS.md': ((78298, '798429772e14d564701f93be43e8bc2da23893f05f4f99abc2f3a040e696e8c7'),
        (81070, 'caa39d06fa7622bfa93f6922c0a2c7d708b1728f1220cc5864585aa9ebed3fb7')),
    'README.md': ((54619, 'e54ea88e20143f0b1eaf612388adb31f8f5db63c9a5901db606a5641fa899f3f'),
        (57391, 'a29df64142da4deb5a9df702e8d85d9927d4ff1126b95f0e69da123a1a2d5f2d')),
}
_RW0_POST_MERGE_CROSS_STAGE_PATHS = frozenset({
    '.docs/rw0-b2-wire-protocol.md',
    '.docs/rw0-c2-scope-admission-provisioning-contract.md',
    '.docs/rw0-d1-offline-process-and-capsule-spine.md',
})
_RW0_POST_MERGE_OWNER = '.docs/rw0-terminal-outcome-physical-closure.md'
_RW0_POST_MERGE_BEGIN = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_BEGIN -->'
_RW0_POST_MERGE_END = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_POST_MERGE_STATUS_SUCCESSOR_END -->'


def _strip_rw0_anchor_0009_status(payload: bytes) -> bytes:
    begin = b'\n<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_BEGIN -->\n'
    end = b'<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_END -->\n'
    if begin not in payload:
        return payload
    _require(payload.count(begin) == payload.count(end) == 1 and payload.endswith(end),
             'guard:rw0_anchor_0009_status:markers')
    predecessor, body = payload.split(begin, 1)
    addition = begin + body
    for phrase in (b'0009_rw0_terminal_anchor_registry',
                   b'CURRENT UNCOMMITTED IMPLEMENTATION CANDIDATE',
                   b'artificial_offline_normal.v1', b'no physical cancel capability'):
        _require(phrase in addition, 'guard:rw0_anchor_0009_status:semantic')
    return predecessor
_RW0_POST_MERGE_ADDITION_IDENTITY = (
    2772, 'a3eb717cb1586c055b65c33b442903f6aa427a714093fff297c3079523893c52'
)
_RW0_POST_MERGE_BLOCK_IDENTITY = (
    2771, '563d2d78a16fd606290394b4132805b3195edce6dd6c9f3787e95aee55de865c'
)


def _rw0_post_merge_status_predecessor(
    relative_path: str, payload: bytes,
    *, boundary: str = 'guard:rw0_post_merge_status',
) -> tuple[bytes, bytes]:
    payload = _strip_rw0_anchor_0009_status(payload)
    expected_predecessor, expected_current = _RW0_POST_MERGE_STATUS_IDENTITIES[relative_path]
    begin = b'\n' + _RW0_POST_MERGE_BEGIN + b'\n'
    end = _RW0_POST_MERGE_END + b'\n'
    _require(type(payload) is bytes and
             payload.count(_RW0_POST_MERGE_BEGIN) == 1 and
             payload.count(_RW0_POST_MERGE_END) == 1 and
             payload.count(begin) == 1 and payload.count(end) == 1 and
             payload.index(begin) < payload.index(end),
             boundary + ':markers:' + relative_path)
    start = payload.index(begin)
    size, digest = _RW0_POST_MERGE_ADDITION_IDENTITY
    addition = payload[start:start + size]
    _require(len(addition) == size and addition.startswith(begin) and
             addition.endswith(end) and
             hashlib.sha256(addition).hexdigest() == digest and
             (len(addition[1:]), hashlib.sha256(addition[1:]).hexdigest()) ==
             _RW0_POST_MERGE_BLOCK_IDENTITY,
             boundary + ':addition_identity:' + relative_path)
    previous_end = (
        b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_CROSS_STAGE_STATUS_REPAIR_END -->\n'
        if relative_path in _RW0_POST_MERGE_CROSS_STAGE_PATHS else
        b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
    )
    tail = payload[start + size:]
    _require(payload[:start].endswith(previous_end) and
             (tail.startswith(b'\nStatus: uncommitted implementation candidate')
              if relative_path == _RW0_POST_MERGE_OWNER else tail == b''),
             boundary + ':placement:' + relative_path)
    predecessor = payload[:start] + tail
    _require((len(predecessor), hashlib.sha256(predecessor).hexdigest()) ==
             expected_predecessor,
             boundary + ':predecessor_identity:' + relative_path)
    _require((len(payload), hashlib.sha256(payload).hexdigest()) == expected_current,
             boundary + ':current_identity:' + relative_path)
    return predecessor, addition


def _assert_rw0_post_merge_status_semantics(addition: bytes) -> None:
    compact = b' '.join(addition.split())
    boundary = 'guard:rw0_post_merge_status:'
    required = (
        b'Classification: `CURRENT INTEGRATED CAPABILITY STATUS`',
        b'`trunk_dev` by squash commit `3be0096c163b456c9975326be3eb2c30d2b4bbd1`',
        b'sole parent `61d0330aba1160f7f5e7d9c541a325222d1c61e5`',
        b'integrated capability tree `bc10382edd1b2c097fc729e4e168d72e710391fe`',
        b'Git objects and refs own the current containing commit and publication truth',
        b'`artificial_offline_normal.v1` source',
        b'normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`',
        b'P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure remain separate private fenced transactions and facts',
        b'Migration `0008_rw0_terminal_outcome` remains the source/catalog suffix',
        b'P0 grants no current permission',
        b'P1 remains prior decision history rather than terminal truth',
        b'normal accept binds the immutable acceptance fact without mutation or replenishment',
        b'implementation staged-tree gate passed 9,568 / 9,568 tests',
        b'status staged-tree focused gate passed 5,655 / 5,655 tests',
        b'Independent artifact review accepted the exact status tree `bc10382edd1b2c097fc729e4e168d72e710391fe`',
        b'9,597-test selector-free FULL record was carried evidence on that tree and was not rerun during integration',
        b'No tests ran during the integration operation itself',
        b'not validation of this later status-only correction',
        b'earlier candidate-stage, local-commit-stage, and cross-stage status passages in this document are preserved historical evidence',
        b'uncommitted, only a local topic-branch commit, or followed by no push, PR, merge, or source publication are stage-local',
        b'no active-cancel terminal family or executable permission',
        b'no live supplier/custody, worker/provider, or physical remote contact',
        b'no ES/Bridge route',
        b'no Coordinator-owned product Git-effect or runtime publication authority',
        b'no service, queue, scheduler, deployment, or autonomous-runtime loop',
        b'Existing F03/F05 nonblocking provenance limits retain their recorded scope and are not repaired',
    )
    forbidden = (
        b'3be0096c163b456c9975326be3eb2c30d2b4bbd1 is permanently the current containing HEAD',
        b'9,597-test selector-free FULL record was rerun during integration',
        b'Tests ran during integration',
        b'candidate-stage status is current repository status',
        b'local-commit-stage status is current repository status',
        b'active-cancel terminal family is implemented',
        b'executable permission is granted',
        b'live supplier/custody is available',
        b'live worker/provider contact is active',
        b'ES/Bridge route is active',
        b'Coordinator owns product Git-effect authority',
        b'service, queue, scheduler, deployment, or autonomous runtime is active',
        b'F03/F05 were repaired',
    )
    for phrase in forbidden:
        _require(phrase not in compact, boundary + 'authority_overclaim')
    for phrase in required:
        _require(phrase in compact, boundary + 'semantic_required')


def test_rw0_post_merge_status_exact_25_document_successor() -> None:
    assert len(_RW0_POST_MERGE_STATUS_IDENTITIES) == 25
    assert len(_RW0_POST_MERGE_CROSS_STAGE_PATHS) == 3
    additions = []
    for relative_path in _RW0_POST_MERGE_STATUS_IDENTITIES:
        payload = (ROOT / relative_path).read_bytes()
        assert payload.count(
            b'\n<!-- RW0_TERMINAL_ANCHOR_0009_STATUS_SUCCESSOR_BEGIN -->\n') == 1
        predecessor, addition = _rw0_post_merge_status_predecessor(
            relative_path, payload)
        assert predecessor and addition
        _assert_rw0_post_merge_status_semantics(addition)
        additions.append(addition)
    assert len(set(additions)) == 1


@pytest.mark.parametrize('case,boundary', (
    ('missing', 'markers'), ('duplicate', 'markers'),
    ('truncated', 'markers'), ('moved', 'placement'),
    ('reordered', 'markers'), ('predecessor_mutation', 'predecessor_identity'),
    ('wrong_commit', 'addition_identity'), ('wrong_tree', 'addition_identity'),
    ('wrong_parent', 'addition_identity'),
))
def test_rw0_post_merge_status_exact_negative_specimens(case: str, boundary: str) -> None:
    path = 'AGENTS.md'
    current = _strip_rw0_anchor_0009_status((ROOT / path).read_bytes())
    predecessor, addition = _rw0_post_merge_status_predecessor(path, current)
    if case == 'missing':
        changed = predecessor
    elif case == 'duplicate':
        changed = current + addition
    elif case == 'truncated':
        changed = current[:-1]
    elif case == 'moved':
        changed = addition + predecessor
    elif case == 'reordered':
        changed = current.replace(_RW0_POST_MERGE_BEGIN, b'__POST_MERGE_TEMP__', 1).replace(
            _RW0_POST_MERGE_END, _RW0_POST_MERGE_BEGIN, 1).replace(
            b'__POST_MERGE_TEMP__', _RW0_POST_MERGE_END, 1)
    elif case == 'predecessor_mutation':
        changed = b'X' + predecessor[1:] + addition
    else:
        old = {
            'wrong_commit': b'3be0096c163b456c9975326be3eb2c30d2b4bbd1',
            'wrong_tree': b'bc10382edd1b2c097fc729e4e168d72e710391fe',
            'wrong_parent': b'61d0330aba1160f7f5e7d9c541a325222d1c61e5',
        }[case]
        changed = predecessor + addition.replace(old, b'0' * 40, 1)
    assert changed != current
    with pytest.raises(AssertionError, match='^guard:rw0_post_merge_status:' + boundary):
        _rw0_post_merge_status_predecessor(path, changed)


@pytest.mark.parametrize('case', (
    'current_head', 'full_rerun', 'integration_tests', 'candidate_current',
    'local_current', 'active_cancel', 'executable_permission',
    'live_supplier', 'live_worker', 'es_bridge', 'product_git',
    'service_runtime', 'f03_f05',
))
def test_rw0_post_merge_status_semantic_negative_specimens(case: str) -> None:
    _predecessor, addition = _rw0_post_merge_status_predecessor(
        'AGENTS.md', (ROOT / 'AGENTS.md').read_bytes())
    claim = {
        'current_head': b'3be0096c163b456c9975326be3eb2c30d2b4bbd1 is permanently the current containing HEAD',
        'full_rerun': b'9,597-test selector-free FULL record was rerun during integration',
        'integration_tests': b'Tests ran during integration',
        'candidate_current': b'candidate-stage status is current repository status',
        'local_current': b'local-commit-stage status is current repository status',
        'active_cancel': b'active-cancel terminal family is implemented',
        'executable_permission': b'executable permission is granted',
        'live_supplier': b'live supplier/custody is available',
        'live_worker': b'live worker/provider contact is active',
        'es_bridge': b'ES/Bridge route is active',
        'product_git': b'Coordinator owns product Git-effect authority',
        'service_runtime': b'service, queue, scheduler, deployment, or autonomous runtime is active',
        'f03_f05': b'F03/F05 were repaired',
    }[case]
    changed = addition.replace(_RW0_POST_MERGE_END,
                               claim + b'\n' + _RW0_POST_MERGE_END, 1)
    assert changed != addition
    with pytest.raises(AssertionError, match='^guard:rw0_post_merge_status:authority_overclaim$'):
        _assert_rw0_post_merge_status_semantics(changed)


# The later local-commit status is a fixed successor to the exact committed
# candidate-stage documents. These literals are frozen from the accepted edit,
# never derived from a document while a test is evaluating that document.
_RW0_LOCAL_TERMINAL_STATUS_IDENTITIES = {
    '.docs/architecture.md': ((51426, '2381e1afc3b22e6414beaf48c679109fbf5e8e8eb4f48aae68f43224c10178e5'),
        (48680, '382235ce4b8374e4af9c9e4c58f106bfad685d1e281130f49fad85ef10f62463')),
    '.docs/authority-boundaries.md': ((41922, '4e8d0a5f499b31fc83e7144abd0a38c463983e2540ee8567ced9ebc08c9b0549'),
        (39176, 'd98037d3f14a870d2a6ce974ae899962d5bad899f53b6a724a992b30e571291d')),
    '.docs/autonomous-software-development-operating-model.md': ((48324, '18dc97e1092ad41d5d747d71cc468447597abae2ea6ab0ddb82fce854add34b7'),
        (45578, 'bfc134807c33a59d595121151193d3d6dfe76959eb964bd8d66a12a8a179c26c')),
    '.docs/c2b-durable-development-state.md': ((1909248, 'bdf3ed6a8189dedd224c2d742884429aeda13d799ecf13a1fa16c2c1c991d274'),
        (1906502, 'aeee29055e776d6c55f689d1de03cb0fa647e1c46e001d22ec8a7451859a54ed')),
    '.docs/c2b2-migration-0002.md': ((14154, 'cbacd025ffb8524b9769c75cf0ad2be026f5b6b7ed9730e754fa5704f864b71b'),
        (11408, 'ba9ecfe211c47810d9ec1b7d792a031783654665fb009c22217be4819646ccb4')),
    '.docs/durable-state-model.md': ((47921, '13523fdfa4dd5344dc4a95de7c090afc339a2516bd97b630e645940b913d3ed0'),
        (45175, '3bd5597bff63d05f03fef0f841d2294cdfe087bad1d10d226fde3700f44797ad')),
    '.docs/rw0-b1-pure-phase-values.md': ((38882, '966dfe81ecba50b8e185dc47f69a463869485e552c6fa5001cfcbc9d4249108a'),
        (36136, '7957bb990607fa0b979a25956a288fc6313521856ea8ffe8931513bac50671e4')),
    '.docs/rw0-c2-durable-progression-decision-semantic-contract.md': ((82408, '7393061f61c4a783277be41e149b2ae9b3fc49a06ac5c1ee01e53f361aadc056'),
        (79662, '579e89e87a9c4d8e5da53d6aa91ef331f1bce3d0e83e8a615ff87b4d2a66edc3')),
    '.docs/rw0-c2-first-live-proof-posture.md': ((22074, '1bf09d17266debd5b0758d8ac7e2592734bfae02e35a13d86ae5e8e778239cf1'),
        (19328, 'ffd3ffac6329ea8f67f1796f4440bfe02ac1391cb35033bd818bbb8e4a5ee5b2')),
    '.docs/rw0-c2-physical-p0-p1-implementation.md': ((23641, '9b78a53abf6583a09dd3de207452ddbf6e5f5d655af027f44f309d5f4b5512b9'),
        (20895, '5939195ff98198890e6a29ee9cf915597e96e364693478d2434f50236b184ef4')),
    '.docs/rw0-c2-private-value-versioning.md': ((223578, '267220a7e81400b31bb33bbc71b2e2d79b673e62a24c6828e4d3de4886a209b6'),
        (220832, '908e08d924300b94d2e3aa726a2575bdaab3a24784aa21630c96d35791d79468')),
    '.docs/rw0-remote-worker-contact-phase-entry.md': ((65397, '2021ae46e8dce5d40057d1cf84d69177db2a63953f488716322ea9f2d49cd7c2'),
        (62651, '97433cddf62d795c04680a611425dc1132094c784b41f1d564ce742c3d3b02b0')),
    '.docs/rw0-terminal-outcome-physical-closure.md': ((19889, '8dc761f3be97905fa980a31df04dcd3bc36e781b51af65ffa052050739ad953e'),
        (17143, 'e29661b01c48dee59138a191e8b6ca005b672b86a9e46c33c78a4e458638ce38')),
    '.docs/software-development-progression-boundary.md': ((32361, 'ff4bf801de9101892a28ffb992d4ad620ab38065097d95e24cb17b33e35d4df7'),
        (29615, 'd76f13ace3759ed6f7dc586142254b4aac092e8a177adad1b0435f96329aca92')),
    '.docs/sqlite-bootstrap-and-migrations.md': ((43109, '95feb34848d62ba55d3bac7a67d187f85db20b8144da6b282044e2fa3fb1dbc0'),
        (40363, '3514a6d100cbc647b6cc8e45a9e94456256d4431d1a29587feefa397e4932902')),
    '.docs/sqlite-operations-and-recovery.md': ((48849, '4c6030ecaa25fe6aba170e89973553ed4c3d6c548ecd6c3791b7795692e5d37e'),
        (46103, 'b163068f9113e576db29b8b92503efbc5056dcd38bf1b4a5dee9388c16ad70a6')),
    '.docs/sqlite-schema-v1.md': ((29957, 'f302822cf32c9ff478c1c7f37351211e1fc97a47e8558b3b2ecd021648f57ea4'),
        (27211, '2cf2b5e18e4eb9c45b0395556e4304465445d701936549221b40525da46378dd')),
    '.docs/sqlite-state-backend-adr.md': ((39374, '9c4ec4237034fca9ef292df6d0c12bbcc02df257d1d7658e725e4bfb268a27a9'),
        (36628, 'f94ac9a85674bae068abe5262198cf36c9c17567b9c9042db90debca23fd47e1')),
    '.docs/worker-execution-boundary.md': ((38234, 'deb4e0a9572ae43f1b80bf23a282e85b52b6adb329f0fe87fe5253e4cc66fa1f'),
        (35488, 'e4029cd33dee5c1b81b5c74897620d69aaf90a28f8570bbf455882fda58763d4')),
    '.docs/writer-session-authority.md': ((61686, 'd1c1468496d33ecc50410ac62abfb60c58129b3a7535f6856d9661f8980325a2'),
        (58940, 'da98f0ec790a5ebe31660dc6a641366c1bb8740a527aeb6781af1e1d5627c163')),
    'AGENTS.md': ((78298, '798429772e14d564701f93be43e8bc2da23893f05f4f99abc2f3a040e696e8c7'),
        (75552, '4d947ee8f6b20e40f6f20755ae3a28fd5603ca99dda97cb436fa35dd0db7c482')),
    'README.md': ((54619, 'e54ea88e20143f0b1eaf612388adb31f8f5db63c9a5901db606a5641fa899f3f'),
        (51873, 'b1fff34a97decde7e14eb8f346b3568aee97cb539f7da1e9d4f7f2e9aab9f96f')),
}
_RW0_LOCAL_TERMINAL_SUFFIX = (2746, '123d4c562ecc39e492aa6636912abb2423b00a5de91a7e0858496d8f4d06064c')
_RW0_LOCAL_TERMINAL_OWNER_INSERT = (2746, 'da49cd43c77d08af6939f09588007ba42138599a68e9cea6435c782947fedd40')


_RW0_LOCAL_TERMINAL_BEGIN = b'\n<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->\n'
_RW0_LOCAL_TERMINAL_END = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
_RW0_LOCAL_TERMINAL_PRIOR_END = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->\n'
_RW0_LOCAL_TERMINAL_OWNER_PREFIX = b'# RW0 normal terminal outcome physical closure\n\n'


def _rw0_local_terminal_status_predecessor(relative_path: str, payload: bytes,
                                           *, boundary: str) -> tuple[bytes, bytes]:
    if _RW0_POST_MERGE_BEGIN in payload:
        payload, _post_merge_status = _rw0_post_merge_status_predecessor(
            relative_path, payload)
    current, expected_predecessor = _RW0_LOCAL_TERMINAL_STATUS_IDENTITIES[relative_path]
    if relative_path == '.docs/rw0-terminal-outcome-physical-closure.md':
        size, digest = _RW0_LOCAL_TERMINAL_OWNER_INSERT
        begin = _RW0_LOCAL_TERMINAL_BEGIN[1:]
        _require(payload.startswith(_RW0_LOCAL_TERMINAL_OWNER_PREFIX + begin) and
                 payload.count(begin) == payload.count(_RW0_LOCAL_TERMINAL_END) == 1 and
                 len(payload) >= len(_RW0_LOCAL_TERMINAL_OWNER_PREFIX) + size,
                 boundary + ':local_owner_placement')
        start = len(_RW0_LOCAL_TERMINAL_OWNER_PREFIX)
        addition = payload[start:start + size]
        _require(addition.endswith(_RW0_LOCAL_TERMINAL_END + b'\n') and
                 hashlib.sha256(addition).hexdigest() == digest,
                 boundary + ':local_owner_insert_identity')
        predecessor = payload[:start] + payload[start + size:]
    else:
        size, digest = _RW0_LOCAL_TERMINAL_SUFFIX
        _require(payload.count(_RW0_LOCAL_TERMINAL_BEGIN) ==
                 payload.count(_RW0_LOCAL_TERMINAL_END) == 1 and
                 payload.endswith(_RW0_LOCAL_TERMINAL_END) and
                 len(payload) >= size and
                 payload[-size:].startswith(_RW0_LOCAL_TERMINAL_BEGIN) and
                 payload[:-size].endswith(_RW0_LOCAL_TERMINAL_PRIOR_END),
                 boundary + ':local_append_placement:' + relative_path)
        addition = payload[-size:]
        _require(hashlib.sha256(addition).hexdigest() == digest,
                 boundary + ':local_append_identity:' + relative_path)
        predecessor = payload[:-size]
    _require((len(predecessor), hashlib.sha256(predecessor).hexdigest()) ==
             expected_predecessor,
             boundary + ':local_predecessor_identity:' + relative_path)
    _require((len(payload), hashlib.sha256(payload).hexdigest()) == current,
             boundary + ':local_current_identity:' + relative_path)
    return predecessor, addition


def _assert_rw0_local_terminal_status_semantics(status: bytes) -> None:
    compact = b' '.join(status.split())
    required = (
        b'cumulative independent audit accepted Git-compatible tree',
        b'after its current-ledger consistency repair',
        b'4691af58ae0ee3107b4e2e9b6b1508032944e357',
        b'd3fd741c872b26aa2dfe927ab6dccc638cdcf356',
        b'61d0330aba1160f7f5e7d9c541a325222d1c61e5',
        b'feat: add RW0 normal terminal closure',
        b'9,568 selector-free tests',
        b'zero failures, errors, skips, xfails, or xpasses',
        b'three known Python 3.13 multithreaded-fork deprecation warnings',
        b'no push, PR, merge, publication, deployment, service/runtime contact, or product effect',
        b'0008_rw0_terminal_outcome',
        b'normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`',
        b'P0 grants no current permission',
        b'P1 is prior decision history, not terminal truth',
        b'without mutation or replenishment',
        b'may shape-check the current global-stop singleton before writer fencing',
        b'receipt-present terminal read, replay, and recovery verify saved full head postimages',
        b'fresh receipt miss retains current-head, current-stop, recording, and disclosure checks',
        b'old whole-operation zero-current-stop-SELECT audit failure remains historical',
        b'Git objects and refs own commit and publication truth',
        b'evidence only', b'no executable permission, three cancel selectors',
        b'Existing F03/F05 nonblocking provenance limits retain their recorded scope',
        b'Candidate-stage status elsewhere in this document is preserved history',
    )
    for phrase in (b'grants executable permission', b'cancel selectors are implemented',
                   b'published to origin', b'product Git effect executed',
                   b'live supplier is qualified'):
        _require(phrase not in compact, 'guard:rw0_local_terminal_status:authority_overclaim')
    for phrase in required:
        _require(phrase in compact, 'guard:rw0_local_terminal_status:semantic_required')


def test_rw0_local_terminal_status_successor_preserves_all_committed_documents() -> None:
    assert len(_RW0_LOCAL_TERMINAL_STATUS_IDENTITIES) == 22
    for relative_path in _RW0_LOCAL_TERMINAL_STATUS_IDENTITIES:
        predecessor, addition = _rw0_local_terminal_status_predecessor(
            relative_path, (ROOT / relative_path).read_bytes(),
            boundary='guard:rw0_local_terminal_status')
        assert predecessor and addition
        _assert_rw0_local_terminal_status_semantics(addition)


@pytest.mark.parametrize('case,boundary', (
    ('omitted', 'local_append_placement'),
    ('duplicate', 'local_append_placement'),
    ('truncated', 'local_append_placement'),
    ('reordered', 'local_append_placement'),
    ('relocated_before_predecessor', 'local_append_placement'),
    ('historical_mutation', 'local_predecessor_identity'),
    ('wrong_commit', 'local_append_identity'),
    ('wrong_tree', 'local_append_identity'),
))
def test_rw0_local_terminal_status_exact_negative_controls(case: str, boundary: str) -> None:
    relative_path = 'AGENTS.md'
    current, _post_merge_status = _rw0_post_merge_status_predecessor(
        relative_path, (ROOT / relative_path).read_bytes())
    predecessor, addition = _rw0_local_terminal_status_predecessor(
        relative_path, current, boundary='guard:rw0_local_terminal_status')
    if case == 'omitted':
        mutant = predecessor
    elif case == 'duplicate':
        mutant = current + addition
    elif case == 'truncated':
        mutant = current[:-1]
    elif case == 'reordered':
        changed = addition.replace(b'_BEGIN', b'_TEMP', 1).replace(
            b'_END', b'_BEGIN', 1).replace(b'_TEMP', b'_END', 1)
        mutant = predecessor + changed
    elif case == 'relocated_before_predecessor':
        mutant = addition + predecessor
    elif case == 'historical_mutation':
        mutant = b'X' + predecessor[1:] + addition
    elif case == 'wrong_commit':
        mutant = current.replace(b'd3fd741c872b26aa2dfe927ab6dccc638cdcf356', b'0' * 40, 1)
    else:
        mutant = current.replace(b'4691af58ae0ee3107b4e2e9b6b1508032944e357', b'0' * 40, 1)
    assert mutant != current
    with pytest.raises(AssertionError, match='^guard:rw0_local_terminal_status:' + boundary):
        _rw0_local_terminal_status_predecessor(
            relative_path, mutant, boundary='guard:rw0_local_terminal_status')


def test_rw0_local_terminal_status_owner_placement_and_semantic_causality() -> None:
    owner = '.docs/rw0-terminal-outcome-physical-closure.md'
    current = (ROOT / owner).read_bytes()
    predecessor, addition = _rw0_local_terminal_status_predecessor(
        owner, current, boundary='guard:rw0_local_terminal_status')
    assert predecessor.startswith(b'# RW0 normal terminal outcome physical closure\n\nStatus: uncommitted')
    assert b'The later cumulative audit remains BLOCKED' in predecessor
    assert b'whole-operation zero-current-stop-SELECT requirement failed' in predecessor
    assert b'F01 and the O1 test counter' in predecessor
    moved = predecessor + addition
    with pytest.raises(AssertionError, match='^guard:rw0_local_terminal_status:local_owner_placement$'):
        _rw0_local_terminal_status_predecessor(
            owner, moved, boundary='guard:rw0_local_terminal_status')
    for old,new,diagnostic in (
        (b'd3fd741c872b26aa2dfe927ab6dccc638cdcf356', b'0' * 40, 'semantic_required'),
        (b'4691af58ae0ee3107b4e2e9b6b1508032944e357', b'0' * 40, 'semantic_required'),
        (b'no executable permission', b'grants executable permission', 'authority_overclaim'),
    ):
        changed = addition.replace(old, new, 1)
        assert changed != addition
        with pytest.raises(AssertionError, match='^guard:rw0_local_terminal_status:' + diagnostic + '$'):
            _assert_rw0_local_terminal_status_semantics(changed)


def _rw0_normal_terminal_status_predecessor(relative_path: str, payload: bytes,
                                            *, boundary: str,
                                            local_status_peeled: bool = False) -> bytes:
    if not local_status_peeled:
        payload, _local_status = _rw0_local_terminal_status_predecessor(
            relative_path, payload, boundary=boundary)
    fixed = (_RW0_NORMAL_TERMINAL_STATUS_IDENTITIES |
             _RW0_NORMAL_TERMINAL_OTHER_IDENTITIES)[relative_path]
    current, suffix = fixed
    _require((len(payload), hashlib.sha256(payload).hexdigest()) == current,
             boundary + ':current_identity:' + relative_path)
    suffix_size, suffix_hash = suffix
    begin = b'\n<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_BEGIN -->\n'
    end = b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_CURRENT_SUCCESSOR_END -->\n'
    _require(payload.count(begin) == payload.count(end) == 1 and
             payload.endswith(end) and payload[-suffix_size:].startswith(begin) and
             hashlib.sha256(payload[-suffix_size:]).hexdigest() == suffix_hash,
             boundary + ':append_identity:' + relative_path)
    return payload[:-suffix_size]

_RW0_C2_STATUS_BEGIN = b'\n<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->\n'
_RW0_C2_STATUS_END = b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
_RW0_C2_ACCEPTED_TREE = b'161ed4b544baf970cc26428b9805a106ea0f3edf'
_RW0_C2_LOCAL_COMMIT = b'8704e6c7988250598809f3a0daf88c3e11493488'
_RW0_C2_PHYSICAL_OLD_OPENING = b'''Status: uncommitted P0-to-P1 artificial-offline implementation candidate. The
exact saved and reopened P0 checkpoint and v2 work-head identity checkpoint
are complete. The prior work-head stop remains historical evidence below and
was superseded by the authorized v2 engineering decision. An independent audit
blocked the later 21-field basis candidate because stale-currentness block
replay could not reconstruct its candidate reason. The present basis-v2 repair
is another uncommitted candidate pending independent audit. The private fenced
P1 writer, readback, replay, and three-way recovery are present in source;
publication and live operation remain separate gates.'''
_RW0_C2_PHYSICAL_NEW_OPENING = b'''Status: independently accepted private artificial-offline P0\xe2\x86\x92P1 source,
locally committed as `8704e6c7988250598809f3a0daf88c3e11493488` at tree `161ed4b544baf970cc26428b9805a106ea0f3edf`; publication and live operation
remain separate gates. The exact P0/work-head checkpoints and blocked
21-field basis predecessor below remain historical evidence. The current
basis-v2, command-digest-v2, and disclosure/eligibility-split repairs were
accepted together by the independent artifact audit. The private fenced P1
writer, readback, replay, and three-way recovery are present in source.'''
_RW0_C2_OPERATIONS_OLD = (
    b'catalog (the uncommitted P0/P1 candidate extends the contiguous 0001\xe2\x80\x930005\n'
    b'  prefix through'
)
_RW0_C2_OPERATIONS_NEW = (
    b'catalog (the locally committed private P0/P1 source extends the contiguous 0001\xe2\x80\x930005\n'
    b'  prefix through'
)


def _rw0_c2_status_predecessor(relative_path: str, payload: bytes,
                               *, local_status_peeled: bool = False) -> tuple[bytes, bytes]:
    payload = _rw0_normal_terminal_status_predecessor(
        relative_path, payload, boundary='guard:rw0_c2_status',
        local_status_peeled=local_status_peeled)
    current, predecessor, suffix = _RW0_C2_STATUS_DOCUMENT_IDENTITIES[relative_path]
    _require((len(payload), hashlib.sha256(payload).hexdigest()) == current,
             'guard:rw0_c2_status:current_identity:' + relative_path)
    size, digest = suffix
    _require(payload.count(_RW0_C2_STATUS_BEGIN) == 1 and
             payload.count(_RW0_C2_STATUS_END) == 1 and
             payload.endswith(_RW0_C2_STATUS_END) and
             payload[-size:].startswith(_RW0_C2_STATUS_BEGIN) and
             hashlib.sha256(payload[-size:]).hexdigest() == digest,
             'guard:rw0_c2_status:append_identity:' + relative_path)
    status = payload[-size:]
    restored = payload[:-size]
    if relative_path == '.docs/rw0-c2-physical-p0-p1-implementation.md':
        _require(restored.count(_RW0_C2_PHYSICAL_NEW_OPENING) == 1,
                 'guard:rw0_c2_status:physical_replacement')
        restored = restored.replace(_RW0_C2_PHYSICAL_NEW_OPENING,
                                    _RW0_C2_PHYSICAL_OLD_OPENING, 1)
    elif relative_path == '.docs/sqlite-operations-and-recovery.md':
        _require(restored.count(_RW0_C2_OPERATIONS_NEW) == 1,
                 'guard:rw0_c2_status:operations_replacement')
        restored = restored.replace(_RW0_C2_OPERATIONS_NEW,
                                    _RW0_C2_OPERATIONS_OLD, 1)
    _require((len(restored), hashlib.sha256(restored).hexdigest()) == predecessor,
             'guard:rw0_c2_status:predecessor_identity:' + relative_path)
    return restored, status


def _assert_rw0_c2_status_semantics(status: bytes) -> None:
    compact = b' '.join(status.split())
    for token in (_RW0_C2_ACCEPTED_TREE, _RW0_C2_LOCAL_COMMIT):
        _require(token in compact, 'guard:rw0_c2_status:accepted_identity')
    _require(b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->' in status and
             b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->' in status,
             'guard:rw0_c2_status:marker_semantics')
    for forbidden in (b'committed to trunk_dev', b'published to origin',
                      b'production worker is ready', b'terminal outcome is recorded'):
        _require(forbidden not in compact, 'guard:rw0_c2_status:nonclaim')


def test_rw0_c2_status_successor_reconstructs_all_committed_predecessors() -> None:
    assert len(_RW0_C2_STATUS_DOCUMENT_IDENTITIES) == 13
    for relative_path in _RW0_C2_STATUS_DOCUMENT_IDENTITIES:
        payload = (ROOT / relative_path).read_bytes()
        predecessor, status = _rw0_c2_status_predecessor(relative_path, payload)
        assert predecessor and status
        _assert_rw0_c2_status_semantics(status)


def test_rw0_c2_status_successor_current_private_contract_and_nonclaims() -> None:
    physical = (ROOT / '.docs/rw0-c2-physical-p0-p1-implementation.md').read_bytes()
    _, status = _rw0_c2_status_predecessor(
        '.docs/rw0-c2-physical-p0-p1-implementation.md', physical)
    compact = b' '.join(status.split())
    for phrase in (
        b'P0 and P1 are separate fenced physical transactions',
        b'P0 records a verified admission act/fact',
        b'without current authority',
        b'one of five progression branches',
        b'only candidate acceptance records an acceptance fact',
        b'not terminal truth',
        b'Decision Basis v2',
        b'guarded-command-digest.v2.identity',
        b'historical work-head witness',
        b'Fresh universal disclosure',
        b'only for fresh candidate acceptance',
        b'F03 remains a nonblocking observation',
        b'F05 remains a nonblocking observation',
        b'Earlier full-ref and raw-index observation limits',
        b'No push, PR, merge, publication, deployment, or product effect',
        b'No live enrollment or custody supplier',
        b'production provider or worker',
        b'ES/Bridge route',
        b'product Git effect',
        b'service, queue, scheduler, deployment, or autonomous loop',
    ):
        _require(phrase in compact, 'guard:rw0_c2_status:physical_semantics:' + phrase.decode())
    operating = (ROOT / '.docs/autonomous-software-development-operating-model.md').read_bytes()
    _, operating_status = _rw0_c2_status_predecessor(
        '.docs/autonomous-software-development-operating-model.md', operating)
    assert b'9,473 collected/executed/JUnit/passed' in operating_status
    assert b'three known Python 3.13 fork' in operating_status


@pytest.mark.parametrize('case,boundary', (
    ('missing', 'current_identity'),
    ('duplicate', 'current_identity'),
    ('historical_change', 'current_identity'),
    ('status_overclaim', 'current_identity'),
))
def test_rw0_c2_status_successor_exact_negative_specimens(case, boundary) -> None:
    path = 'AGENTS.md'
    original = (ROOT / path).read_bytes()
    # These specimens target the older P0/P1 status predicate, so first peel
    # the later fixed local-commit block without changing the historical oracle.
    candidate_stage, _local_status = _rw0_local_terminal_status_predecessor(
        path, original, boundary='guard:rw0_local_terminal_status')
    _, suffix = _rw0_c2_status_predecessor(
        path, candidate_stage, local_status_peeled=True)
    changed = {
        'missing': candidate_stage[:-len(suffix)],
        'duplicate': candidate_stage + suffix,
        'historical_change': b'X' + candidate_stage[1:],
        'status_overclaim': candidate_stage.replace(b'No push, PR,\nmerge',
                                                   b'Yes push, PR,\nmerge', 1),
    }[case]
    assert changed != candidate_stage
    with pytest.raises(AssertionError, match='^guard:rw0_c2_status:' + boundary):
        _rw0_c2_status_predecessor(path, changed, local_status_peeled=True)


@pytest.mark.parametrize('old,new,boundary', (
    (b'8704e6c7988250598809f3a0daf88c3e11493488', b'4519630d0db967066beb21b4ace5004e76827716',
     'guard:rw0_c2_status:accepted_identity'),
    (b'No live enrollment\nor custody supplier', b'Live enrollment and custody supplier',
     'guard:rw0_c2_status:physical_semantics'),
    (b'F03 remains a nonblocking observation', b'F03 is closed',
     'guard:rw0_c2_status:physical_semantics'),
    (b'F05 remains a nonblocking observation', b'F05 is closed',
     'guard:rw0_c2_status:physical_semantics'),
))
def test_rw0_c2_status_successor_semantic_negative_specimens(old, new, boundary) -> None:
    physical = (ROOT / '.docs/rw0-c2-physical-p0-p1-implementation.md').read_bytes()
    _, status = _rw0_c2_status_predecessor(
        '.docs/rw0-c2-physical-p0-p1-implementation.md', physical)
    changed = status.replace(old, new, 1)
    assert changed != status and changed.count(_RW0_C2_STATUS_BEGIN) == 1
    with pytest.raises(AssertionError, match='^' + boundary):
        _assert_rw0_c2_status_semantics(changed)
        compact = b' '.join(changed.split())
        for phrase in (b'No live enrollment or custody supplier',
                       b'F03 remains a nonblocking observation',
                       b'F05 remains a nonblocking observation'):
            _require(phrase in compact, 'guard:rw0_c2_status:physical_semantics')


# The later terminal commit is a fixed cross-stage successor in three owners
# whose final P0/P1 status blocks were otherwise left as current global text.
# These current and predecessor identities are literals, never taken from the
# document being checked at test runtime.
_RW0_TERMINAL_CROSS_STAGE_REPAIR_IDENTITIES = {
    '.docs/rw0-b2-wire-protocol.md': (
        (29964, '502a6bf83a994dfece29726d695b57722dc4e512b36f7d95eef12bee65032b65'),
        (28130, '7fcfacb31c4506a536fc3890f6d71d6058040930c23b52481444ed4d18f4b345'),
    ),
    '.docs/rw0-d1-offline-process-and-capsule-spine.md': (
        (9442, '1b943647fdbbeec3e6f5d25da94591ced2fb385a5fb9813d921131c34f9e3753'),
        (7608, 'a98d6ff185bb698228c7266308f3a5ff5163b2e6f05a0746eb755d2df7e4436e'),
    ),
    '.docs/rw0-c2-scope-admission-provisioning-contract.md': (
        (29620, 'd99c216cdcf1fb72fab2a85746ce9f72b27f6d929f8f3294de2dbb96324ddd02'),
        (27786, '474067391e0b813d0e2b38ddbc725c34f40cb7672982a5857093767f83fdcf74'),
    ),
}
_RW0_TERMINAL_CROSS_STAGE_REPAIR_BEGIN = (
    b'\n<!-- RW0_NORMAL_TERMINAL_CLOSURE_CROSS_STAGE_STATUS_REPAIR_BEGIN -->\n'
)
_RW0_TERMINAL_CROSS_STAGE_REPAIR_END = (
    b'<!-- RW0_NORMAL_TERMINAL_CLOSURE_CROSS_STAGE_STATUS_REPAIR_END -->\n'
)
_RW0_TERMINAL_CROSS_STAGE_PREVIOUS_END = (
    b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->\n'
)
_RW0_TERMINAL_CROSS_STAGE_SUFFIX = (
    1834, 'b9ecf41b6f9a37944f45578b9905ce4cb0a0654fcb9f2a740c7d4f31d7db9ea0'
)


def _rw0_terminal_cross_stage_repair_predecessor(
    relative_path: str, payload: bytes,
) -> tuple[bytes, bytes]:
    if _RW0_POST_MERGE_BEGIN in payload:
        payload, _post_merge_status = _rw0_post_merge_status_predecessor(
            relative_path, payload)
    current, previous = _RW0_TERMINAL_CROSS_STAGE_REPAIR_IDENTITIES[relative_path]
    size, digest = _RW0_TERMINAL_CROSS_STAGE_SUFFIX
    boundary = 'guard:rw0_terminal_cross_stage_repair:'
    _require(type(payload) is bytes and len(payload) >= size and
             payload.count(_RW0_TERMINAL_CROSS_STAGE_REPAIR_BEGIN) == 1 and
             payload.count(_RW0_TERMINAL_CROSS_STAGE_REPAIR_END) == 1 and
             payload.endswith(_RW0_TERMINAL_CROSS_STAGE_REPAIR_END) and
             payload[-size:].startswith(_RW0_TERMINAL_CROSS_STAGE_REPAIR_BEGIN),
             boundary + 'structure:' + relative_path)
    predecessor, addition = payload[:-size], payload[-size:]
    _require(predecessor.endswith(_RW0_TERMINAL_CROSS_STAGE_PREVIOUS_END) and
             predecessor.count(_RW0_TERMINAL_CROSS_STAGE_PREVIOUS_END) == 1,
             boundary + 'placement:' + relative_path)
    _require(hashlib.sha256(addition).hexdigest() == digest,
             boundary + 'addition_identity:' + relative_path)
    _require((len(predecessor), hashlib.sha256(predecessor).hexdigest()) == previous,
             boundary + 'predecessor_identity:' + relative_path)
    _require((len(payload), hashlib.sha256(payload).hexdigest()) == current,
             boundary + 'current_identity:' + relative_path)
    return predecessor, addition


def _assert_rw0_terminal_cross_stage_repair_semantics(addition: bytes) -> None:
    compact = b' '.join(addition.split())
    boundary = 'guard:rw0_terminal_cross_stage_repair:'
    for forbidden in (
        b'Wire owns terminal closure', b'D1 owns terminal closure',
        b'P0 owns terminal closure', b'P0 grants current permission',
        b'published to origin', b'executable permission is granted',
        b'terminal cancellation profile is implemented',
    ):
        _require(forbidden not in compact, boundary + 'authority_overclaim')
    required = (
        b'immediately preceding `RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR` block',
        b'preserved P0/P1 local-commit-stage snapshot',
        b'future or absent describes that stage; it is not current global Coordinator status',
        b'P0 itself still creates no terminal fact',
        b'independently accepted normal-terminal source at Git tree',
        b'4691af58ae0ee3107b4e2e9b6b1508032944e357',
        b'd3fd741c872b26aa2dfe927ab6dccc638cdcf356',
        b'61d0330aba1160f7f5e7d9c541a325222d1c61e5',
        b'feat: add RW0 normal terminal closure',
        b'0008_rw0_terminal_outcome', b'current source/catalog suffix',
        b'artificial_offline_normal.v1',
        b'normal `accept`, `repair`, `replan`, `terminal_reject`, and `block`',
        b'P0 scope admission, P1 progression decision with its acceptance-only fact, and terminal closure are separate private fenced transactions and facts',
        b'P0 grants no current permission',
        b'P1 remains prior decision history rather than terminal truth',
        b'Wire, D1, and P0 retain their own bounded contracts',
        b'none gains terminal ownership, executable permission, live authority, or effect authority',
        b'No push, PR, merge, publication, deployment, live supplier/custody, worker/provider contact, ES/Bridge route, product Git effect, service, queue, scheduler, terminal cancellation profile, or autonomous loop follows',
        b'Git objects and refs own commit and publication truth',
        b'Audit, validation, provenance, reports, and status prose are evidence only',
    )
    for phrase in required:
        _require(phrase in compact, boundary + 'semantic_required')


def test_rw0_terminal_cross_stage_repair_reconstructs_exact_three_predecessors() -> None:
    additions = []
    for relative_path in _RW0_TERMINAL_CROSS_STAGE_REPAIR_IDENTITIES:
        predecessor, addition = _rw0_terminal_cross_stage_repair_predecessor(
            relative_path, (ROOT / relative_path).read_bytes())
        _require(predecessor and addition, 'guard:rw0_terminal_cross_stage_repair:presence')
        _assert_rw0_terminal_cross_stage_repair_semantics(addition)
        additions.append(addition)
        # The older six-owner P0/P1 check must still reach its exact prior
        # current identity, marker, insertion, and historical predecessor.
        _rw0_c2_current_drift_predecessor(relative_path, (ROOT / relative_path).read_bytes())
    assert len(additions) == 3 and additions[0] == additions[1] == additions[2]


@pytest.mark.parametrize('case', (
    'omitted', 'duplicate', 'truncated', 'reordered_marker',
    'before_prior', 'inside_prior', 'historical_mutation',
    'wrong_commit', 'wrong_tree', 'wrong_parent',
))
def test_rw0_terminal_cross_stage_repair_exact_negative_controls(case: str) -> None:
    path = '.docs/rw0-b2-wire-protocol.md'
    current, _post_merge_status = _rw0_post_merge_status_predecessor(
        path, (ROOT / path).read_bytes())
    predecessor, addition = _rw0_terminal_cross_stage_repair_predecessor(path, current)
    prior_begin = b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->'
    if case == 'omitted':
        mutant = predecessor
    elif case == 'duplicate':
        mutant = current + addition
    elif case == 'truncated':
        mutant = current[:-1]
    elif case == 'reordered_marker':
        mutant = current.replace(b'CROSS_STAGE_STATUS_REPAIR_BEGIN', b'CROSS_STAGE_STATUS_REPAIR_TEMP', 1).replace(
            b'CROSS_STAGE_STATUS_REPAIR_END', b'CROSS_STAGE_STATUS_REPAIR_BEGIN', 1).replace(
            b'CROSS_STAGE_STATUS_REPAIR_TEMP', b'CROSS_STAGE_STATUS_REPAIR_END', 1)
    elif case == 'before_prior':
        position = predecessor.index(prior_begin)
        mutant = predecessor[:position] + addition + predecessor[position:]
    elif case == 'inside_prior':
        position = predecessor.index(prior_begin) + len(prior_begin)
        mutant = predecessor[:position] + addition + predecessor[position:]
    elif case == 'historical_mutation':
        mutant = b'X' + predecessor[1:] + addition
    else:
        original, replacement = {
            'wrong_commit': (b'd3fd741c872b26aa2dfe927ab6dccc638cdcf356', b'0' * 40),
            'wrong_tree': (b'4691af58ae0ee3107b4e2e9b6b1508032944e357', b'0' * 40),
            'wrong_parent': (b'61d0330aba1160f7f5e7d9c541a325222d1c61e5', b'0' * 40),
        }[case]
        mutant = predecessor + addition.replace(original, replacement, 1)
    assert mutant != current
    with pytest.raises(AssertionError, match='^guard:rw0_terminal_cross_stage_repair:'):
        _rw0_terminal_cross_stage_repair_predecessor(path, mutant)


@pytest.mark.parametrize('case', (
    'wrong_commit', 'wrong_tree', 'wrong_parent', 'stage_reclassification',
    'wire_ownership', 'd1_ownership', 'p0_ownership', 'permission_overclaim',
))
def test_rw0_terminal_cross_stage_repair_isolated_semantic_negatives(case: str) -> None:
    _predecessor, addition = _rw0_terminal_cross_stage_repair_predecessor(
        '.docs/rw0-b2-wire-protocol.md',
        (ROOT / '.docs/rw0-b2-wire-protocol.md').read_bytes())
    replacements = {
        'wrong_commit': (b'd3fd741c872b26aa2dfe927ab6dccc638cdcf356', b'0' * 40),
        'wrong_tree': (b'4691af58ae0ee3107b4e2e9b6b1508032944e357', b'0' * 40),
        'wrong_parent': (b'61d0330aba1160f7f5e7d9c541a325222d1c61e5', b'0' * 40),
        'stage_reclassification': (b'it is not current global Coordinator status', b'it is current global Coordinator status'),
    }
    if case in replacements:
        old, new = replacements[case]
        mutant = addition.replace(old, new, 1)
    else:
        claim = {
            'wire_ownership': b'Wire owns terminal closure',
            'd1_ownership': b'D1 owns terminal closure',
            'p0_ownership': b'P0 owns terminal closure',
            'permission_overclaim': b'executable permission is granted',
        }[case]
        mutant = addition.replace(_RW0_TERMINAL_CROSS_STAGE_REPAIR_END,
                                  claim + b'\n' + _RW0_TERMINAL_CROSS_STAGE_REPAIR_END, 1)
    assert mutant != addition
    with pytest.raises(AssertionError, match='^guard:rw0_terminal_cross_stage_repair:(semantic_required|authority_overclaim)$'):
        _assert_rw0_terminal_cross_stage_repair_semantics(mutant)


# Fixed identities for the six independently reviewed current-drift repairs.
# Each predecessor is the exact a34d28... endpoint; these values are literals,
# never computed from the actual file under test at test runtime.
_RW0_C2_REPAIR_IDENTITIES = {'.docs/durable-state-model.md': {'anchor': '<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->',
                                  'current': (44156,
                                              '93d6fcd4a5db3c02ee73475ecff465cbec43bdcfda140cb3a6b85499ec4d393e'),
                                  'historical_literal': 'RW0-C2 physical decision persistence,',
                                  'insert': (2103,
                                             'f5f3f15fe39edaf4a5d124bec7b7a44e78c1af20981456ec2b5d68530bb73a13'),
                                  'offset': 42053,
                                  'owner_required': ('B1, Wire,',
                                                     'private P0/P1 physical persistence',
                                                     'RW0-E remain future'),
                                  'predecessor': (42053,
                                                  '7f9cba19f491322dd2fc0f1656ac6b76e698723a6700d1f9919d22b2196e9e80'),
                                  'side': 'after_shared_end'},
 '.docs/rw0-b2-wire-protocol.md': {'anchor': '<!-- RW0_D2_CURRENT_STATUS_END -->\n',
                                   'current': (28130,
                                               '7fcfacb31c4506a536fc3890f6d71d6058040930c23b52481444ed4d18f4b345'),
                                   'historical_literal': 'owns future durable facts',
                                   'insert': (2046,
                                              'a30da0de417c76ba5c2cfe16f8ae2421b0eb0aca3bd6183fa6b213b67a1ac388'),
                                   'offset': 26084,
                                   'owner_required': ('Wire remains pure representation/classification',
                                                      'owns no persistence',
                                                      'Physical transport'),
                                   'predecessor': (26084,
                                                   'ac1091f043f5fa6042ced1e919c740a08af975b7df1e5e97b66634f85cb68e69'),
                                   'side': 'after'},
 '.docs/rw0-c2-scope-admission-provisioning-contract.md': {'anchor': '<!-- '
                                                                     'RW0_C2_P0_PHYSICAL_CANDIDATE_SUCCESSOR_END '
                                                                     '-->\n',
                                                           'current': (27786,
                                                                       '474067391e0b813d0e2b38ddbc725c34f40cb7672982a5857093767f83fdcf74'),
                                                           'historical_literal': 'uncommitted candidate',
                                                           'insert': (2128,
                                                                      'e2656c3eb0fa34ba69b18a0b92cf033958f8f7796360a9bb039c37b46e2e3ca6'),
                                                           'offset': 25658,
                                                           'owner_required': ('four-table P0 private '
                                                                              'family',
                                                                              'separately attributable '
                                                                              'and usable before a '
                                                                              'program',
                                                                              'Live supplier/custody '
                                                                              'gate B remains open'),
                                                           'predecessor': (25658,
                                                                           '05648279930b7058fe1be7d86fe449213ed13b98ec37e226be50140e99c431b1'),
                                                           'side': 'after'},
 '.docs/rw0-d1-offline-process-and-capsule-spine.md': {'anchor': '',
                                                       'current': (7608,
                                                                   'a98d6ff185bb698228c7266308f3a5ff5163b2e6f05a0746eb755d2df7e4436e'),
                                                       'historical_literal': 'RW0-C2 persistence '
                                                                             'remains later.',
                                                       'insert': (1984,
                                                                  '62e13a702ca22af03cc657909b0a5534fc005f90ad0ac91d14ef002a47dd984e'),
                                                       'offset': 5624,
                                                       'owner_required': ('D1 still neither',
                                                                          'D1 capsule',
                                                                          'RW0-E'),
                                                       'predecessor': (5624,
                                                                       'b537fbe074717aacdfaefd2cf32cd22c46046034ae115453ddded4e2dc25201b'),
                                                       'side': 'eof'},
 '.docs/rw0-remote-worker-contact-phase-entry.md': {'anchor': '<!-- '
                                                              'COORDINATOR_RW0_PHASE_ENTRY_CONTRACT_END '
                                                              '-->',
                                                    'current': (61619,
                                                                '4cb9dc4fd900aa9507ca4840d55f35d76460ec936c86d357c32f3eb44df1b814'),
                                                    'historical_literal': 'Physical representation, '
                                                                          'provisioning, safe values, '
                                                                          'and mutation',
                                                    'insert': (2033,
                                                               '270f54b1f613caf3b7ef020a40f3112818d58a97782e11c305d6c7afeecf766d'),
                                                    'offset': 59536,
                                                    'owner_required': ('replay/readback, and recovery',
                                                                       'does not make a live accept '
                                                                       'writer callable',
                                                                       'Terminal-outcome persistence'),
                                                    'predecessor': (59586,
                                                                    'bee20ed00c7e6f86db3394351f0cbe29626413c635cd9a982416984b288e6fbd'),
                                                    'side': 'before'},
 '.docs/worker-execution-boundary.md': {'anchor': '<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END '
                                                  '-->',
                                        'current': (34516,
                                                    '1e58585fe3a561207abe0ac25f22d333eea4f31a59eca94ec753c64478c92e83'),
                                        'historical_literal': 'RW0-C2 physical decision persistence,',
                                        'insert': (2107,
                                                   '081f99a52ba627eccc6bb680fda5dc9439e42b7bc5d9c23304e12cac45fb83d3'),
                                        'offset': 32409,
                                        'owner_required': ('neither P0/P1 persistence nor live runtime',
                                                           'Physical worker transport',
                                                           'ES routing'),
                                        'predecessor': (32409,
                                                        '3cfc1208d96e1f59a81dcd70dce5d43d89f2cb70cc5af6eca453650c33742769'),
                                        'side': 'after_shared_end'}}
_RW0_C2_REPAIR_BEGIN = b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->'
_RW0_C2_REPAIR_END = b'<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->'


def _rw0_c2_current_drift_reconstruct_unsealed(relative_path: str, payload: bytes) -> tuple[bytes, bytes]:
    fixed = _RW0_C2_REPAIR_IDENTITIES[relative_path]
    start = fixed['offset']
    size, insert_sha = fixed['insert']
    _require(payload.count(_RW0_C2_REPAIR_BEGIN) == 1 and
             payload.count(_RW0_C2_REPAIR_END) == 1 and
             payload.index(_RW0_C2_REPAIR_BEGIN) < payload.index(_RW0_C2_REPAIR_END),
             'guard:rw0_c2_repair:markers:' + relative_path)
    anchor = fixed['anchor'].encode()
    if fixed['side'] == 'after_shared_end':
        _require(payload.count(anchor) == 1 and
                 payload.index(_RW0_C2_REPAIR_BEGIN) > payload.index(anchor) and
                 payload.index(_RW0_C2_REPAIR_BEGIN) == payload.index(anchor) + len(anchor) + 2,
                 'guard:rw0_c2_repair:location:' + relative_path)
    _require(start <= payload.index(_RW0_C2_REPAIR_BEGIN) <
             payload.index(_RW0_C2_REPAIR_END) < start + size,
             'guard:rw0_c2_repair:insertion_identity:' + relative_path)
    _require(len(payload) >= start + size,
             'guard:rw0_c2_repair:insertion_identity:' + relative_path)
    addition = payload[start:start + size]
    _require(hashlib.sha256(addition).hexdigest() == insert_sha,
             'guard:rw0_c2_repair:insertion_identity:' + relative_path)
    previous = payload[:start] + payload[start + size:]
    if fixed['side'] == 'before':
        _require(payload[start + size:].startswith(anchor),
                 'guard:rw0_c2_repair:location:' + relative_path)
    elif fixed['side'] == 'after_shared_end':
        _require(payload[:start].endswith(anchor + b'\n') and
                 addition.startswith(b'\n' + _RW0_C2_REPAIR_BEGIN) and
                 payload[start + size:] == b'' and
                 payload[:start] == previous,
                 'guard:rw0_c2_repair:location:' + relative_path)
    else:
        _require(payload[:start].endswith(anchor) if anchor else start == len(previous),
                 'guard:rw0_c2_repair:location:' + relative_path)
    expected = fixed['predecessor']
    _require((len(previous), hashlib.sha256(previous).hexdigest()) == expected,
             'guard:rw0_c2_repair:predecessor_identity:' + relative_path)
    _require(fixed['historical_literal'].encode() in previous,
             'guard:rw0_c2_repair:historical_passage:' + relative_path)
    return previous, addition


def _rw0_c2_current_drift_predecessor(relative_path: str, payload: bytes) -> tuple[bytes, bytes]:
    if relative_path in _RW0_TERMINAL_CROSS_STAGE_REPAIR_IDENTITIES:
        payload, _terminal_repair = _rw0_terminal_cross_stage_repair_predecessor(
            relative_path, payload)
    if relative_path in _RW0_NORMAL_TERMINAL_OTHER_IDENTITIES:
        payload = _rw0_normal_terminal_status_predecessor(
            relative_path, payload, boundary='guard:rw0_c2_repair')
    fixed = _RW0_C2_REPAIR_IDENTITIES[relative_path]
    _require((len(payload), hashlib.sha256(payload).hexdigest()) == fixed['current'],
             'guard:rw0_c2_repair:current_identity:' + relative_path)
    return _rw0_c2_current_drift_reconstruct_unsealed(relative_path, payload)


def _assert_rw0_c2_repair_status_semantics(relative_path: str, addition: bytes) -> None:
    compact = b' '.join(addition.split())
    _require(compact.count(_RW0_C2_REPAIR_BEGIN) == 1 and
             compact.count(_RW0_C2_REPAIR_END) == 1 and
             compact.index(_RW0_C2_REPAIR_BEGIN) < compact.index(_RW0_C2_REPAIR_END),
             'guard:rw0_c2_repair:markers:' + relative_path)
    for label, token in (
        ('publication', b'publication was performed'),
        ('p0_permission', b'P0 grants current permission'),
        ('terminal', b'terminal outcome is recorded'),
        ('live', b'live supplier is available'),
        ('es', b'ES route is active'),
        ('bridge', b'Bridge route is active'),
        ('product_git', b'product Git effect executed'),
        ('autonomy', b'autonomous loop is active'),
    ):
        _require(token not in compact, 'guard:rw0_c2_repair:nonclaim:' + label)
    for token in (
        b'161ed4b544baf970cc26428b9805a106ea0f3edf',
        b'8704e6c7988250598809f3a0daf88c3e11493488',
        b'4519630d0db967066beb21b4ace5004e76827716',
    ):
        _require(token in compact, 'guard:rw0_c2_repair:accepted_identity')
    required = (
        ('gate', b'9,473 collected/executed/JUnit/passed'),
        ('gate', b'three known Python 3.13 multithreaded-fork'),
        ('publication', b'That gate performed no push, upstream creation, PR, merge, publication,'),
        ('git_truth', b'Git objects and refs remain commit and publication truth'),
        ('evidence', b'are evidence only'),
        ('private', b'bounded private artificial-offline P0'),
        ('p0_permission', b'never current permission'),
        ('p1', b'one of five durable decision branches'),
        ('p1', b'only on `candidate_acceptance`'),
        ('terminal', b'not terminal truth, executable permission, live custody, runtime admission, or deployment authority'),
        ('mechanics', b'Decision Basis v2, guarded-command-digest v2'),
        ('mechanics', b'historical work-head witness, universal disclosure posture, and acceptance-only eligibility'),
        ('observations', b'F03 and F05 remain open nonblocking observations'),
        ('live', b'There is no live enrollment/custody supplier, terminal outcome, production provider/worker, ES/Bridge route, product Git effect, public service, queue, scheduler, deployment, or autonomous loop.'),
    )
    for label, token in required:
        _require(token in compact, 'guard:rw0_c2_repair:' + label)
    for token in _RW0_C2_REPAIR_IDENTITIES[relative_path]['owner_required']:
        _require(token.encode() in compact, 'guard:rw0_c2_repair:owner:' + relative_path)


def test_rw0_c2_current_drift_six_owner_local_successors_and_predecessors() -> None:
    assert len(_RW0_C2_REPAIR_IDENTITIES) == 6
    for relative_path in _RW0_C2_REPAIR_IDENTITIES:
        path = ROOT / relative_path
        metadata = path.lstat()
        _require(path.is_file() and not path.is_symlink() and
                 (metadata.st_mode & 0o7777) == 0o644,
                 'guard:rw0_c2_repair:regular_mode:' + relative_path)
        predecessor, addition = _rw0_c2_current_drift_predecessor(
            relative_path, path.read_bytes())
        _require(predecessor and addition, 'guard:rw0_c2_repair:presence:' + relative_path)
        _assert_rw0_c2_repair_status_semantics(relative_path, addition)
    # The previously accepted thirteen-document predecessor chain still runs
    # through its separate fixed-identity test above.


@pytest.mark.parametrize('case,boundary', (
    ('omitted', 'markers'), ('duplicate', 'markers'),
    ('reordered_marker', 'markers'), ('historical_mutation', 'predecessor_identity'),
))
def test_rw0_c2_current_drift_exact_negative_specimens(case: str, boundary: str) -> None:
    path = '.docs/durable-state-model.md'
    current = (ROOT / path).read_bytes()
    original = _rw0_normal_terminal_status_predecessor(
        path, current, boundary='guard:rw0_c2_repair')
    _previous, addition = _rw0_c2_current_drift_predecessor(path, current)
    offset = _RW0_C2_REPAIR_IDENTITIES[path]['offset']
    if case == 'omitted':
        changed = original[:offset] + original[offset + len(addition):]
    elif case == 'duplicate':
        changed = original[:offset] + addition + addition + original[offset + len(addition):]
    elif case == 'reordered_marker':
        changed_addition = addition.replace(_RW0_C2_REPAIR_BEGIN, b'__BEGIN__', 1).replace(
            _RW0_C2_REPAIR_END, _RW0_C2_REPAIR_BEGIN, 1).replace(
            b'__BEGIN__', _RW0_C2_REPAIR_END, 1)
        changed = original[:offset] + changed_addition + original[offset + len(addition):]
    else:
        changed = b'X' + original[1:]
    assert changed != original
    with pytest.raises(AssertionError, match='^guard:rw0_c2_repair:' + boundary):
        _rw0_c2_current_drift_reconstruct_unsealed(path, changed)


@pytest.mark.parametrize('path', (
    '.docs/durable-state-model.md',
    '.docs/worker-execution-boundary.md',
))
@pytest.mark.parametrize('case', ('before_end', 'inside_shared_body'))
def test_rw0_c2_current_drift_shared_architecture_map_placement_negatives(path: str, case: str) -> None:
    predecessor, addition = _rw0_c2_current_drift_predecessor(path, (ROOT / path).read_bytes())
    block = addition[1:]
    if case == 'before_end':
        position = predecessor.index(_RW0_C2_REPAIR_IDENTITIES[path]['anchor'].encode())
    else:
        begin = b'<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_BEGIN -->\n'
        position = predecessor.index(begin) + len(begin)
    changed = predecessor[:position] + block + b'\n' + predecessor[position:]
    _require(changed != (ROOT / path).read_bytes(), 'guard:rw0_c2_repair:negative_specimen')
    with pytest.raises(AssertionError, match='^guard:rw0_c2_repair:location:' + re.escape(path) + '$'):
        _rw0_c2_current_drift_reconstruct_unsealed(path, changed)


@pytest.mark.parametrize('case,boundary', (
    ('accepted_tree', 'accepted_identity'), ('local_commit', 'accepted_identity'),
    ('publication', 'nonclaim:publication'), ('p0_permission', 'nonclaim:p0_permission'),
    ('terminal', 'nonclaim:terminal'), ('live', 'nonclaim:live'),
    ('es', 'nonclaim:es'), ('bridge', 'nonclaim:bridge'),
    ('product_git', 'nonclaim:product_git'), ('autonomy', 'nonclaim:autonomy'),
))
def test_rw0_c2_current_drift_semantic_negative_specimens(case: str, boundary: str) -> None:
    path = '.docs/rw0-c2-scope-admission-provisioning-contract.md'
    _previous, addition = _rw0_c2_current_drift_predecessor(path, (ROOT / path).read_bytes())
    if case == 'accepted_tree':
        changed = addition.replace(b'161ed4b544baf970cc26428b9805a106ea0f3edf', b'0' * 40, 1)
    elif case == 'local_commit':
        changed = addition.replace(b'8704e6c7988250598809f3a0daf88c3e11493488', b'0' * 40, 1)
    else:
        claim = {
            'publication': b'publication was performed',
            'p0_permission': b'P0 grants current permission',
            'terminal': b'terminal outcome is recorded',
            'live': b'live supplier is available',
            'es': b'ES route is active',
            'bridge': b'Bridge route is active',
            'product_git': b'product Git effect executed',
            'autonomy': b'autonomous loop is active',
        }[case]
        changed = addition.replace(_RW0_C2_REPAIR_END, claim + b'\n' + _RW0_C2_REPAIR_END, 1)
    assert changed != addition
    with pytest.raises(AssertionError, match='^guard:rw0_c2_repair:' + boundary + '$'):
        _assert_rw0_c2_repair_status_semantics(path, changed)
