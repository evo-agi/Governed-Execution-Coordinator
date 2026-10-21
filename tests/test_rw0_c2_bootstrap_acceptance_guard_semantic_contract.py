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
    ('fencing_before_receipt', 'Universal lineage/admission/continuity/sole-active posture is part of the command and writer admission/fencing prefix, before receipt lookup.'),
    ('replay_before_eligibility', 'Command-local grammar/basis and writer fencing precede receipt-first replay and collision checks, then authoritative branch derivation and acceptance-only eligibility, construction/application of the atomic family, capability invalidation, one commit attempt, and readback-only uncertainty resolution.'),
    ('implementation', 'Physical representation, provisioning, readers, writers, safe values, migration treatment, and runtime remain unimplemented and unselected.'),
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
    candidates = [paragraph for paragraph in paragraphs if paragraph.startswith('Universal lineage/admission/continuity/sole-active posture')]
    _require(len(candidates) == 1, 'guard_ordering_integrity:fencing_before_receipt')
    sentences = re.split(r'(?<=\.) ', candidates[0])
    _require(sentences[0] == 'Universal lineage/admission/continuity/sole-active posture is part of the command and writer admission/fencing prefix, before receipt lookup.',
             'guard_ordering_integrity:fencing_before_receipt')
    _require(sentences[1] == 'Replay does not reevaluate fresh claimed status.', 'guard_ordering_integrity:replay_before_eligibility')
    chain = re.fullmatch(r'(.+) precede (.+), then (.+), (.+), (.+), (.+), and (.+)\.', sentences[2])
    _require(chain is not None, 'guard_ordering_integrity:replay_before_eligibility')
    stages = chain.groups()
    _require(stages[0] == 'Command-local grammar/basis and writer fencing', 'guard_ordering_integrity:fencing_before_receipt')
    _require(stages[1] == 'receipt-first replay and collision checks' and stages[2] == 'authoritative branch derivation and acceptance-only eligibility',
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
    _require(not any(p.name.startswith('0005') for p in source.rglob('*')), 'guard:migration_absent')
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
    exact = ('guard_ordering_integrity:' if boundary in ('fencing_before_receipt', 'replay_before_eligibility') else 'guard:prose:') + boundary
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
        text = (ROOT / relative).read_text()
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
        text = text.replace('Command-local grammar/basis and writer fencing\nprecede receipt-first replay and\ncollision checks', 'Receipt-first replay and collision disclosure precede\ncommand-local grammar/basis and writer fencing', 1)
    elif case == 'replay':
        text = text.replace('receipt-first replay and\ncollision checks, then authoritative branch derivation and acceptance-only\neligibility', 'authoritative branch derivation and acceptance-only eligibility, then receipt-first replay and collision checks', 1)
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
