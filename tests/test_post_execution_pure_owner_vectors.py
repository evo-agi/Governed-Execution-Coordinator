"""Independent finite accepted-record inventory and precedence vectors."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest

import ge_nwp_coordinator._finite_backlog_risk_source_adapter as adapter
import ge_nwp_coordinator._post_execution_evidence_values as evidence
import ge_nwp_coordinator._post_execution_policy_values as policy
import ge_nwp_coordinator._rw0_c_decision_input_values as decision
from ge_nwp_coordinator._cognitive_proposal_row_values import (
    DevelopmentModelProposalEvidenceBindingRowValue,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkerObservationV1
from test_post_execution_pure_owner_values import (
    BRANCHES,
    CLASS_BY_V,
    _TEST_RECORDS,
    _canonical,
    _digest,
    _ordered_fixture,
    _reason,
    _sample,
    _seal,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ge_nwp_coordinator"

# Current D2 successor to the historical no-production-caller record. This
# independent literal was transcribed from the authenticated primary boundary
# test's CURRENT_D2_CONSUMERS and checked against the actual source imports.
# Pairs use a source basename and a package-qualified target module; the AST
# reports relative imports without that package prefix.
CURRENT_D2_EXTERNAL_IMPORT_PAIRS = frozenset({
    ("_rw0_d2_handback.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_rw0_d2a_evidence.py", "ge_nwp_coordinator._finite_backlog_risk_source_adapter"),
    ("_rw0_d2a_evidence.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_rw0_d2a_evidence.py", "ge_nwp_coordinator._post_execution_policy_values"),
    ("_rw0_d2a_handback.py", "ge_nwp_coordinator._finite_backlog_risk_source_adapter"),
    ("_rw0_d2a_handback.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_rw0_d2a_handback.py", "ge_nwp_coordinator._post_execution_policy_values"),
    ("_rw0_d2b_model_input.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_rw0_d2b_proposal.py", "ge_nwp_coordinator._post_execution_evidence_values"),
})
# The D2 nine-edge identity remains historical. The private post-D2 successor
# adds these five exact consumers; neither set admits public/state-store edges.
POST_D2_EXTERNAL_IMPORT_PAIRS = frozenset({
    ("_rw0_d2_post_execution_continuation.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_rw0_d2_post_execution_continuation.py", "ge_nwp_coordinator._section41_post_execution_proposal_family_projection"),
    ("_section41_post_execution_proposal_mutation_contracts.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_section41_post_execution_proposal_row_values.py", "ge_nwp_coordinator._post_execution_evidence_values"),
    ("_sqlite_section41_post_execution_proposal.py", "ge_nwp_coordinator._post_execution_evidence_values"),
})
CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS = (
    CURRENT_D2_EXTERNAL_IMPORT_PAIRS | POST_D2_EXTERNAL_IMPORT_PAIRS
)
_POST_EXECUTION_SUPPLIER_MODULES = frozenset({
    "_post_execution_evidence_values",
    "_post_execution_policy_values",
    "_finite_backlog_risk_source_adapter",
    "_section41_post_execution_proposal_family_projection",
    "_section41_post_execution_role_resolution",
    "_rw0_c_decision_input_values",
})
_V3G039_STATE_STORE_EDGE = (
    "state_store.py", "ge_nwp_coordinator._post_execution_evidence_values",
)


def _current_external_post_execution_import_pairs() -> frozenset[tuple[str, str]]:
    """Observe the same bounded ImportFrom forms as historical V3G039."""
    observed: set[tuple[str, str]] = set()
    for path in SOURCE.glob("*.py"):
        if path.stem in _POST_EXECUTION_SUPPLIER_MODULES:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target = node.module.removeprefix("ge_nwp_coordinator.")
                if target in _POST_EXECUTION_SUPPLIER_MODULES:
                    observed.add((path.name, f"ge_nwp_coordinator.{target}"))
    return frozenset(observed)


def _production_caller_inventory_violates(
    observed: frozenset[tuple[str, str]] | set[tuple[str, str]],
) -> bool:
    return frozenset(observed) != CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS


GOLDEN_RECORD_IDS = ('golden.owner.author-observation.000',
 'golden.owner.author-observation.001',
 'golden.owner.author-observation.002',
 'golden.owner.author-rank12.000.membership',
 'golden.owner.author-rank12.000.relation',
 'golden.owner.author-rank12.000.graph',
 'golden.owner.author-rank12.000.operands',
 'golden.owner.author-rank12.001.membership',
 'golden.owner.author-rank12.001.relation',
 'golden.owner.author-rank12.001.graph',
 'golden.owner.author-rank12.001.operands',
 'golden.owner.author-rank12.002.membership',
 'golden.owner.author-rank12.002.relation',
 'golden.owner.author-rank12.002.graph',
 'golden.owner.author-rank12.002.operands',
 'golden.owner.review-observation',
 'golden.owner.review-rank12.membership',
 'golden.owner.review-rank12.relation',
 'golden.owner.review-rank12.graph',
 'golden.owner.review-rank12.operands',
 'golden.owner.author-rank13.value',
 'golden.owner.author-rank13.membership',
 'golden.owner.author-rank13.relation',
 'golden.owner.author-rank13.graph',
 'golden.owner.author-rank13.operands',
 'golden.owner.rank14.value',
 'golden.owner.rank14.relation',
 'golden.owner.rank15.value',
 'golden.owner.rank15.relation',
 'golden.owner.rank15.graph',
 'golden.owner.rank15.membership',
 'golden.owner.global-stop.active',
 'golden.V38.primary',
 'golden.V39.primary',
 'golden.V40.primary',
 'golden.V41.primary',
 'golden.V42.primary',
 'golden.V43.primary',
 'golden.V44.primary',
 'golden.V40.n01.author-observation-locator.000',
 'golden.V40.n01.author-observation-locator.001',
 'golden.V40.n01.author-observation-locator.002',
 'golden.V41.n01.branch-assertion.000',
 'golden.V41.n01.branch-assertion.001',
 'golden.V41.n01.branch-assertion.002',
 'golden.V41.n01.branch-assertion.003',
 'golden.V41.n01.branch-assertion.004',
 'golden.V42.n01.branch-assertion.000',
 'golden.V42.n01.branch-assertion.001',
 'golden.V42.n01.branch-assertion.002',
 'golden.V42.n01.branch-assertion.003',
 'golden.V42.n01.branch-assertion.004',
 'golden.V12.validation.entry.000',
 'golden.V12.validation.entry.001',
 'golden.V12.validation.entry.002',
 'golden.V12.validation.entry.003',
 'golden.V12.validation.entry.004',
 'golden.V12.validation.entry.005',
 'golden.V13.validation.support-set',
 'golden.V12.review.entry.000',
 'golden.V12.review.entry.001',
 'golden.V12.review.entry.002',
 'golden.V12.review.entry.003',
 'golden.V12.review.entry.004',
 'golden.V12.review.entry.005',
 'golden.V12.review.entry.006',
 'golden.V13.review.support-set',
 'golden.V12.policy.entry.000',
 'golden.V12.policy.entry.001',
 'golden.V12.policy.entry.002',
 'golden.V12.policy.entry.003',
 'golden.V13.policy.support-set',
 'golden.V12.risk.entry.000',
 'golden.V12.risk.entry.001',
 'golden.V12.risk.entry.002',
 'golden.V12.risk.entry.003',
 'golden.V13.risk.support-set',
 'golden.V12.global-stop.entry.000',
 'golden.V12.global-stop.entry.001',
 'golden.V13.global-stop.support-set',
 'golden.V12.effect-ceiling.entry.000',
 'golden.V12.effect-ceiling.entry.001',
 'golden.V12.effect-ceiling.entry.002',
 'golden.V12.effect-ceiling.entry.003',
 'golden.V12.effect-ceiling.entry.004',
 'golden.V13.effect-ceiling.support-set',
 'golden.V12.reviewer-separation.entry.000',
 'golden.V12.reviewer-separation.entry.001',
 'golden.V13.reviewer-separation.support-set',
 'golden.V14.primary',
 'golden.V15.primary',
 'golden.V17.primary',
 'golden.V18.primary',
 'golden.V19.primary',
 'golden.V20.primary',
 'golden.V21.primary',
 'golden.V16.policy.entry.000',
 'golden.V16.policy.entry.001',
 'golden.V16.policy.entry.002',
 'golden.V16.policy.entry.003',
 'golden.V16.policy.entry.004',
 'golden.V16.risk.entry.000',
 'golden.V16.risk.entry.001',
 'golden.V16.risk.entry.002',
 'golden.V16.risk.entry.003',
 'golden.V16.risk.entry.004',
 'golden.V01.primary',
 'golden.V04.primary',
 'golden.V03.role-entry.05.candidate_capsule',
 'golden.V03.role-entry.06.worker_result',
 'golden.V03.role-entry.07.validation_result',
 'golden.V03.role-entry.08.independent_review',
 'golden.V03.role-entry.09.standing_policy',
 'golden.V03.role-entry.10.risk_lane',
 'golden.V03.role-entry.11.authority_currentness_attestation',
 'golden.V03.role-entry.12.global_stop',
 'golden.V03.role-entry.13.effect_ceiling',
 'golden.V05.primary',
 'golden.V06.projection-entry.000',
 'golden.V06.projection-entry.001',
 'golden.V06.projection-entry.002',
 'golden.V06.projection-entry.003',
 'golden.V06.projection-entry.004',
 'golden.V06.projection-entry.005',
 'golden.V06.projection-entry.006',
 'golden.V06.projection-entry.007',
 'golden.V06.projection-entry.008',
 'golden.V07.primary',
 'golden.V08.private-entry.000',
 'golden.V02.T1-input-context',
 'golden.V09.model-input-binding',
 'golden.V10.full-evidence-supply',
 'golden.V11.role-supply.05.candidate_capsule',
 'golden.V11.role-supply.06.worker_result',
 'golden.V11.role-supply.07.validation_result',
 'golden.V11.role-supply.08.independent_review',
 'golden.V11.role-supply.09.standing_policy',
 'golden.V11.role-supply.10.risk_lane',
 'golden.V11.role-supply.11.authority_currentness_attestation',
 'golden.V11.role-supply.12.global_stop',
 'golden.V11.role-supply.13.effect_ceiling',
 'golden.owner.source-invocation',
 'golden.owner.artifact-binding',
 'golden.owner.proposal-evidence-row.05.candidate_capsule',
 'golden.owner.proposal-evidence-row.06.worker_result',
 'golden.owner.proposal-evidence-row.07.validation_result',
 'golden.owner.proposal-evidence-row.08.independent_review',
 'golden.owner.proposal-evidence-row.09.standing_policy',
 'golden.owner.proposal-evidence-row.10.risk_lane',
 'golden.owner.proposal-evidence-row.11.authority_currentness_attestation',
 'golden.owner.proposal-evidence-row.12.global_stop',
 'golden.owner.proposal-evidence-row.13.effect_ceiling',
 'golden.owner.evidence-set',
 'golden.owner.proposal',
 'golden.owner.owner-family-graph',
 'golden.V22.primary',
 'golden.V23.projection-evidence.000',
 'golden.V23.projection-evidence.001',
 'golden.V23.projection-evidence.002',
 'golden.V23.projection-evidence.003',
 'golden.V23.projection-evidence.004',
 'golden.V23.projection-evidence.005',
 'golden.V23.projection-evidence.006',
 'golden.V23.projection-evidence.007',
 'golden.V23.projection-evidence.008',
 'golden.V24.role-resolution.05.candidate_capsule',
 'golden.V24.role-resolution.06.worker_result',
 'golden.V24.role-resolution.07.validation_result',
 'golden.V24.role-resolution.08.independent_review',
 'golden.V24.role-resolution.09.standing_policy',
 'golden.V24.role-resolution.10.risk_lane',
 'golden.V24.role-resolution.11.authority_currentness_attestation',
 'golden.V24.role-resolution.12.global_stop',
 'golden.V24.role-resolution.13.effect_ceiling',
 'golden.V25.primary',
 'golden.V27.primary',
 'golden.V27.active-stop-control',
 'golden.V29.primary',
 'golden.V31.primary',
 'golden.V32.primary',
 'golden.V32.active-stop',
 'golden.V33.primary',
 'golden.V34.primary',
 'golden.V26.closure-entry.000',
 'golden.V26.closure-entry.001',
 'golden.V26.closure-entry.002',
 'golden.V26.closure-entry.003',
 'golden.V26.closure-entry.004',
 'golden.V26.closure-entry.005',
 'golden.V26.closure-entry.006',
 'golden.V26.closure-entry.007',
 'golden.V28.external-coordinate.000',
 'golden.V28.external-coordinate.001',
 'golden.V28.external-coordinate.002',
 'golden.V28.external-coordinate.003',
 'golden.V28.external-coordinate.004',
 'golden.V30.currentness-component.000',
 'golden.V30.currentness-component.001',
 'golden.V30.currentness-component.002',
 'golden.V30.currentness-component.003',
 'golden.V30.currentness-component.004')
MALFORMED_RECORD_IDS = ('malformed.V3G001.host-module-substitution',
 'malformed.V3G002.host-artifact-profile-field-substitution',
 'malformed.V3G003.host-protocol-profile-field-substitution',
 'malformed.V3G004.global-stop-owner-module-substitution',
 'malformed.V3G005.global-stop-domain-digest-substitution',
 'malformed.V3G006.evidence-set-owner-module-substitution',
 'malformed.V3G007.validation-requirement-owner-module-substitution',
 'malformed.V3G008.review-requirement-owner-module-substitution',
 'malformed.V3G009.evidence-row-locator-substitution',
 'malformed.V3G010.non-temporal-relation-timestamp',
 'malformed.V3G011.temporal-relation-null-timestamp',
 'malformed.V3G012.rank12-cascade-stale',
 'malformed.V3G013.v40-nested-schema-id-absent',
 'malformed.V3G014.v40-nested-field-reorder',
 'malformed.V3G015.v40-nested-type-mismatch',
 'malformed.V3G016.exact-resupply-absent',
 'malformed.V3G017.exact-resupply-bytes-mismatch',
 'malformed.V3G018.candidate-manifest-absent',
 'malformed.V3G019.candidate-manifest-phase-substitution',
 'malformed.V3G020.membership-page-duplicate',
 'malformed.V3G021.membership-cursor-nonmonotonic',
 'malformed.V3G022.membership-page-reordered',
 'malformed.V3G023.membership-cursor-no-progress',
 'malformed.V3G024.membership-overflow',
 'malformed.V3G025.membership-premature-termination',
 'malformed.V3G026.membership-continuation-substitution',
 'malformed.V3G027.membership-capability-epoch-change',
 'malformed.V3G028.snapshot-rank1-membership-substitution',
 'malformed.V3G029.snapshot-rank15-membership-substitution',
 'malformed.V3G030.snapshot-external-source-substitution',
 'malformed.V3G031.snapshot-phase-k8-mismatch',
 'malformed.V3G032.snapshot-required-row-missing',
 'malformed.V3G033.snapshot-current-row-malformed',
 'malformed.V3G034.snapshot-unrelated-state-invariance',
 'malformed.V3G035.package-root-export-widening',
 'malformed.V3G036.state-store-method-widening',
 'malformed.V3G037.writer-session-method-widening',
 'malformed.V3G038.migration-sql-widening',
 'malformed.V3G039.production-caller-widening',
 'malformed.V3G040.direct-sqlite-authority-widening',
 'malformed.V3G041.io-authority-widening',
 'malformed.V3G042.reserved-v35-v37-import',
 'malformed.V3G043.forecast-reintroduced-current',
 'malformed.V3G044.opaque-digest-recovery-completeness',
 'malformed.attempt-fence-expiry-substitution',
 'malformed.candidate-git-sha256',
 'malformed.candidate-git-wrong-oid-width',
 'malformed.effect-fence-expiry-substitution',
 'malformed.finite-backlog-adapter-substitution',
 'malformed.global-stop-branch-mismatch',
 'malformed.policy-source-substitution',
 'malformed.profile-value-mismatch',
 'malformed.requirement-embedded-digest-substitution',
 'malformed.review-observation-kind',
 'malformed.review-source-kind',
 'malformed.review-source-outcome',
 'malformed.risk-source-substitution',
 'malformed.stale-superseded-identity',
 'malformed.unsupported-identity-authentication-claim',
 'malformed.v40-author-evidence-absent',
 'malformed.v40-author-invocation-conflict',
 'malformed.v40-candidate-lineage',
 'malformed.v40-capsule-lineage',
 'malformed.v40-delivery-reuse',
 'malformed.v40-effect-reuse',
 'malformed.v40-invocation-reuse',
 'malformed.v40-phase-lineage',
 'malformed.v40-wrong-review-role',
 'malformed.validation-observation-kind',
 'malformed.validation-source-kind',
 'malformed.validation-source-outcome',
 'malformed.wrong-context-namespace',
 'malformed.wrong-rank14-relation-identity',
 'malformed.wrong-role-digest',
 'malformed.wrong-role-ref',
 'malformed.wrong-role-schema',
 'malformed.wrong-work-spec-pair',
 'malformed.V4I001.contradictory-duplicate-host-identity-field',
 'malformed.V4I002.host-profile-substitution',
 'malformed.V4I003.host-relation-name-substitution',
 'malformed.V4I004.v26-entry-schema-id-omission',
 'malformed.V5C001.variable-list-fixed-cardinality-reintroduction',
 'malformed.V5C002.standing-policy-support-inventory-substitution',
 'malformed.V5C003.currentness-risk-component-collapse',
 'malformed.V5C004.snapshot-risk-source-collapse',
 'malformed.V5L003.underflow-rejection',
 'malformed.V5L004.overflow-rejection',
 'malformed.V5L005.reorder-rejection',
 'malformed.V5L006.duplicate-rejection',
 'malformed.V6R001.rank15-current-owner-cascade-stale',
 'malformed.V8R001.migration0003-evidence-row-self-digest-stale',
 'malformed.V9R001.v16-parent-bound-extra-field-rejection',
 'malformed.V11R001.v16-dispatched-reason-stale')
ASSURANCE_RECORD_IDS = ('assurance.A001',
 'assurance.A002',
 'assurance.A003',
 'assurance.A004',
 'assurance.A005',
 'assurance.A006',
 'assurance.A007',
 'assurance.A008',
 'assurance.A009',
 'assurance.A010',
 'assurance.A011',
 'assurance.A012',
 'assurance.A013',
 'assurance.A014',
 'assurance.A015',
 'assurance.A016',
 'assurance.A017',
 'assurance.A018',
 'assurance.A019',
 'assurance.A020',
 'assurance.A021',
 'assurance.A022',
 'assurance.A023',
 'assurance.A024',
 'assurance.A025',
 'assurance.A026',
 'assurance.A027',
 'assurance.A028',
 'assurance.A029',
 'assurance.A030',
 'assurance.A031',
 'assurance.A032',
 'assurance.A033',
 'assurance.A034',
 'assurance.A035',
 'assurance.A036',
 'assurance.A037',
 'assurance.A038',
 'assurance.A039',
 'assurance.A040',
 'assurance.A041',
 'assurance.A042',
 'assurance.A043',
 'assurance.A044',
 'assurance.A045',
 'assurance.A046',
 'assurance.A047',
 'assurance.A048',
 'assurance.A049',
 'assurance.A050',
 'assurance.A051',
 'assurance.A052',
 'assurance.A053',
 'assurance.A054',
 'assurance.A055',
 'assurance.A056',
 'assurance.A057',
 'assurance.A058',
 'assurance.A059',
 'assurance.A060',
 'assurance.A061',
 'assurance.A062',
 'assurance.A063',
 'assurance.V3G001.host-module-substitution',
 'assurance.V3G002.host-artifact-profile-field-substitution',
 'assurance.V3G003.host-protocol-profile-field-substitution',
 'assurance.V3G004.global-stop-owner-module-substitution',
 'assurance.V3G005.global-stop-domain-digest-substitution',
 'assurance.V3G006.evidence-set-owner-module-substitution',
 'assurance.V3G007.validation-requirement-owner-module-substitution',
 'assurance.V3G008.review-requirement-owner-module-substitution',
 'assurance.V3G009.evidence-row-locator-substitution',
 'assurance.V3G010.non-temporal-relation-timestamp',
 'assurance.V3G011.temporal-relation-null-timestamp',
 'assurance.V3G012.rank12-cascade-stale',
 'assurance.V3G013.v40-nested-schema-id-absent',
 'assurance.V3G014.v40-nested-field-reorder',
 'assurance.V3G015.v40-nested-type-mismatch',
 'assurance.V3G016.exact-resupply-absent',
 'assurance.V3G017.exact-resupply-bytes-mismatch',
 'assurance.V3G018.candidate-manifest-absent',
 'assurance.V3G019.candidate-manifest-phase-substitution',
 'assurance.V3G020.membership-page-duplicate',
 'assurance.V3G021.membership-cursor-nonmonotonic',
 'assurance.V3G022.membership-page-reordered',
 'assurance.V3G023.membership-cursor-no-progress',
 'assurance.V3G024.membership-overflow',
 'assurance.V3G025.membership-premature-termination',
 'assurance.V3G026.membership-continuation-substitution',
 'assurance.V3G027.membership-capability-epoch-change',
 'assurance.V3G028.snapshot-rank1-membership-substitution',
 'assurance.V3G029.snapshot-rank15-membership-substitution',
 'assurance.V3G030.snapshot-external-source-substitution',
 'assurance.V3G031.snapshot-phase-k8-mismatch',
 'assurance.V3G032.snapshot-required-row-missing',
 'assurance.V3G033.snapshot-current-row-malformed',
 'assurance.V3G034.snapshot-unrelated-state-invariance',
 'assurance.V3G035.package-root-export-widening',
 'assurance.V3G036.state-store-method-widening',
 'assurance.V3G037.writer-session-method-widening',
 'assurance.V3G038.migration-sql-widening',
 'assurance.V3G039.production-caller-widening',
 'assurance.V3G040.direct-sqlite-authority-widening',
 'assurance.V3G041.io-authority-widening',
 'assurance.V3G042.reserved-v35-v37-import',
 'assurance.V3G043.forecast-reintroduced-current',
 'assurance.V3G044.opaque-digest-recovery-completeness',
 'assurance.V4I001.contradictory-duplicate-host-identity-field',
 'assurance.V4I002.host-profile-substitution',
 'assurance.V4I003.host-relation-name-substitution',
 'assurance.V4I004.v26-entry-schema-id-omission',
 'assurance.V5C001.variable-list-fixed-cardinality-reintroduction',
 'assurance.V5C002.standing-policy-support-inventory-substitution',
 'assurance.V5C003.currentness-risk-component-collapse',
 'assurance.V5C004.snapshot-risk-source-collapse',
 'assurance.V5L001.fixed-min-boundaries',
 'assurance.V5L002.fixed-max-boundaries',
 'assurance.V5L003.underflow-rejection',
 'assurance.V5L004.overflow-rejection',
 'assurance.V5L005.reorder-rejection',
 'assurance.V5L006.duplicate-rejection',
 'assurance.V6R001.rank15-current-owner-cascade-stale',
 'assurance.V7G001.global-stop-active-applicability-split',
 'assurance.V8R001.migration0003-evidence-row-self-digest-stale',
 'assurance.V9R001.v16-parent-bound-extra-field-rejection',
 'assurance.V11R001.v16-dispatched-reason-stale')


def test_complete_finite_record_responsibility_inventory_is_literal_and_closed() -> None:
    assert len(GOLDEN_RECORD_IDS) == 201 == len(set(GOLDEN_RECORD_IDS))
    assert len(MALFORMED_RECORD_IDS) == 93 == len(set(MALFORMED_RECORD_IDS))
    assert len(ASSURANCE_RECORD_IDS) == 126 == len(set(ASSURANCE_RECORD_IDS))
    assert all(record.startswith("golden.") for record in GOLDEN_RECORD_IDS)
    assert all(record.startswith("malformed.") for record in MALFORMED_RECORD_IDS)
    assert all(record.startswith("assurance.") for record in ASSURANCE_RECORD_IDS)
    assert "malformed.V9R001.v16-parent-bound-extra-field-rejection" in MALFORMED_RECORD_IDS
    assert "assurance.V9R001.v16-parent-bound-extra-field-rejection" in ASSURANCE_RECORD_IDS
    assert not any("model-input-binding-unknown-extra-field" in record for record in MALFORMED_RECORD_IDS + ASSURANCE_RECORD_IDS)


def test_independent_canonical_bytes_and_domain_digest_anchor() -> None:
    value = {"branch": "candidate_acceptance", "result": "permit"}
    expected = b'{"branch":"candidate_acceptance","result":"permit"}'
    assert _canonical(value) == expected
    assert _digest("governed-execution.test.identity", value) == "5455b50d8ed141644eea3c591999f033a6fe4cf7c5770dd3da6d42ddf07e0f0c"


@pytest.mark.parametrize("extra", ("schema_id", "source_ref", "source_digest"))
def test_v9r001_child_unknown_field_precedes_parent_identity(extra: str) -> None:
    mapping = _sample("V32")
    child = dict(mapping["entries"][0])
    child[extra] = "0" * 64 if extra.endswith("digest") else "unexpected.1"
    mapping["entries"] = [child, *mapping["entries"][1:]]
    mapping["matrix_ref"] = "wrong-parent.1"
    mapping["matrix_digest"] = "0" * 64
    assert _reason(CLASS_BY_V["V32"], mapping) == "unknown_field"


@pytest.mark.parametrize(
    "v_number,index,stale",
    (
        ("V18", 3, "halt_only_risk_lane_not_applicable"),
        ("V31", 0, "current_evidence_permits"),
        ("V31", 3, "halt_only_checked"),
        ("V32", 0, "current_evidence_permits"),
        ("V32", 3, "halt_only_checked"),
        ("V33", 0, "current_evidence_permits"),
        ("V33", 3, "halt_only_checked"),
    ),
)
def test_v11r001_dispatched_reason_precedes_parent_identity(v_number: str, index: int, stale: str) -> None:
    mapping = _sample(v_number)
    entries = [dict(entry) for entry in mapping["entries"]]
    entries[index]["reason"] = stale
    mapping["entries"] = entries
    mapping["matrix_ref"] = "wrong-parent.1"
    mapping["matrix_digest"] = "0" * 64
    assert _reason(CLASS_BY_V[v_number], mapping) == "evaluation_contract_mismatch"


def test_parent_bound_v16_has_exactly_five_encoded_fields() -> None:
    mapping = _sample("V16")
    assert tuple(mapping) == ("branch", "applicability", "governed_effect_class", "result", "reason")
    assert not {"schema_id", "source_ref", "source_digest", "profile_ref", "profile_digest"} & set(mapping)


class _FrozenVectorViolation(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _capture_real_rejection(action: object) -> str:
    assert callable(action)
    try:
        action()
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception as caught:
        reason = getattr(caught, "reason", type(caught).__name__)
        assert type(reason) is str and reason
        return reason
    raise AssertionError("causal mutation was accepted")


def _source_owner_metadata_failure(
    base_record: str,
    candidate: dict[str, object],
) -> str | None:
    from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
        DevelopmentReviewRequirementEvidenceV1,
        DevelopmentValidationRequirementEvidenceV1,
    )
    from ge_nwp_coordinator._rw0_phase_entry_semantic_values import (
        RW0EffectHostQualificationV1,
        validate_host_qualification,
    )
    from ge_nwp_coordinator._sqlite_rw0_c1 import (
        _section41_owner_family_matches,
    )
    from ge_nwp_coordinator.global_stop import GlobalStopState

    expected_keys = set(_TEST_RECORDS[base_record])
    if set(candidate) - expected_keys == {"qualification_digest"}:
        return "source_owner_duplicate_identity_field"
    if set(candidate) != expected_keys:
        return "unknown_field"
    canonical = candidate["canonical_value"]
    try:
        if base_record == "source-owner.host-qualification":
            owner = RW0EffectHostQualificationV1.from_mapping(canonical)
            if candidate["owner_module"] != type(owner).__module__:
                return "source_owner_module_mismatch"
            if tuple(candidate["ordered_fields"]) != type(owner)._FIELDS:
                return "unknown_field"
            relation = candidate["relation_and_profile"]
            if relation["profile"] is not None:
                return "source_owner_profile_signature_mismatch"
            if relation["relation"] != validate_host_qualification.__name__:
                return "source_owner_relation_signature_mismatch"
            if (
                candidate["owner_id"] != type(owner).__name__
                or candidate["schema_id"] != owner.schema_id
            ):
                return "source_owner_mismatch"
            return None
        if base_record == "source-owner.global-stop":
            owner = GlobalStopState.from_dict(canonical)
            raw_digest = hashlib.sha256(_canonical(owner.to_dict())).hexdigest()
            if candidate["owner_module"] != type(owner).__module__:
                return "source_owner_module_mismatch"
            if candidate["identity_and_digest"]["digest_posture"] != (
                "raw_sha256_of_canonical_owner_mapping"
            ):
                return "digest_posture_mismatch"
            if (
                tuple(candidate["ordered_fields"])
                != tuple(type(owner).__dataclass_fields__)
                or owner.canonical_digest() != raw_digest
            ):
                return "source_owner_mismatch"
            return None
        if base_record == "source-owner.migration0003-evidence-set":
            identity = {
                name: canonical[name]
                for name in ("evidence_set_ref", "proposal_ref", "proposal_phase", "entries")
            }
            if candidate["owner_module"] != (
                _section41_owner_family_matches.__module__
            ):
                return "source_owner_module_mismatch"
            if evidence._domain_separated_digest(
                    "governed-execution.nwp-model-proposal-evidence-set.v1.identity",
                    identity,
            ) != canonical["evidence_set_digest"]:
                return "source_owner_mismatch"
            return None
        if base_record in {
            "source-owner.validation-requirement",
            "source-owner.review-requirement",
        }:
            owner_type = (
                DevelopmentValidationRequirementEvidenceV1
                if "validation" in base_record
                else DevelopmentReviewRequirementEvidenceV1
            )
            owner = owner_type(**canonical)
            if candidate["owner_module"] != owner_type.__module__:
                return "source_owner_module_mismatch"
            if (
                tuple(candidate["ordered_fields"]) != owner_type.__slots__
                or owner.safe_evidence_digest != canonical["safe_evidence_digest"]
            ):
                return "source_owner_mismatch"
            return None
        assert base_record == "source-owner.migration0003-evidence-row"
        owner = DevelopmentModelProposalEvidenceBindingRowValue(**canonical)
        migration = (
            SOURCE / "sqlite_migrations/0003_cognitive_proposal_and_selection_state.sql"
        ).read_text()
        primary_key = re.search(
            r"PRIMARY KEY\s*\(proposal_ref,\s*evidence_role,\s*ordinal\)",
            migration,
        )
        if candidate["owner_module"] != type(owner).__module__:
            return "source_owner_module_mismatch"
        if candidate["identity_and_digest"]["locator_fields"] != [
            "proposal_ref", "evidence_role", "ordinal"
        ]:
            return "row_locator_mismatch"
        if (
            tuple(candidate["ordered_fields"]) != type(owner)._COLUMNS
            or primary_key is None
        ):
            return "source_owner_mismatch"
        return None
    except Exception:
        return "source_owner_mismatch"


def _execute_source_owner_metadata_mutation(record_id: str) -> str:
    record = _TEST_RECORDS[record_id]
    base_record = record["base_record"]
    descriptor = record["mutated_canonical_value"]
    baseline = deepcopy(_TEST_RECORDS[base_record])
    mutated = deepcopy(baseline)
    pointer = descriptor["json_pointer"]
    if pointer == "/owner_module":
        assert mutated["owner_module"] == descriptor["from"]
        mutated["owner_module"] = descriptor["to"]
    elif pointer.startswith("/ordered_fields/"):
        field = pointer.rsplit("/", 1)[1]
        index = mutated["ordered_fields"].index(field)
        assert mutated["ordered_fields"][index] == descriptor["from"]
        mutated["ordered_fields"][index] = descriptor["to"]
    elif pointer == "/identity_and_digest/digest_posture":
        assert mutated["identity_and_digest"]["digest_posture"] == descriptor["from"]
        mutated["identity_and_digest"]["digest_posture"] = descriptor["to"]
    elif pointer == "/identity_and_digest/locator_fields":
        assert mutated["identity_and_digest"]["locator_fields"] == descriptor["from"]
        mutated["identity_and_digest"]["locator_fields"] = descriptor["to"]
    elif pointer == "/qualification_digest":
        assert descriptor["from"] == "absent" and "qualification_digest" not in mutated
        mutated["qualification_digest"] = descriptor["to"]
    elif pointer == "/relation_and_profile/profile":
        assert mutated["relation_and_profile"]["profile"] == descriptor["from"]
        mutated["relation_and_profile"]["profile"] = descriptor["to"]
    else:
        assert pointer == "/relation_and_profile/relation"
        assert mutated["relation_and_profile"]["relation"] == descriptor["from"]
        mutated["relation_and_profile"]["relation"] = descriptor["to"]
    assert _source_owner_metadata_failure(base_record, baseline) is None
    observed = _source_owner_metadata_failure(base_record, mutated)
    assert observed is not None
    assert _source_owner_metadata_failure(base_record, deepcopy(baseline)) is None
    return observed


def _execute_relation_or_cascade_mutation(record_id: str) -> str:
    from ge_nwp_coordinator._rw0_c1_mutation_contracts import membership_digest
    from ge_nwp_coordinator._rw0_c1_row_values import (
        MEMBERSHIP_COLUMNS,
        RELATION_COLUMNS,
        rw0_c1_row_value_from_tuple,
    )
    from test_post_execution_pure_owner_relations import _reviewer_separation_action

    descriptor = _TEST_RECORDS[record_id]["mutated_canonical_value"]
    if record_id.endswith("non-temporal-relation-timestamp"):
        baseline = deepcopy(_TEST_RECORDS["golden.owner.author-rank12.000.relation"])
        assert rw0_c1_row_value_from_tuple(
            "rw0_relation_bindings", tuple(baseline[name] for name in RELATION_COLUMNS)
        )
        mutated = deepcopy(baseline)
        mutated["evaluated_at"] = descriptor["to"]
        _capture_real_rejection(lambda: rw0_c1_row_value_from_tuple(
            "rw0_relation_bindings", tuple(mutated[name] for name in RELATION_COLUMNS)
        ))
        assert baseline["evaluated_at"] is None and mutated["evaluated_at"] is not None
        assert rw0_c1_row_value_from_tuple(
            "rw0_relation_bindings", tuple(baseline[name] for name in RELATION_COLUMNS)
        )
        return "relation_mismatch"
    if record_id.endswith("temporal-relation-null-timestamp"):
        baseline = _sample("V40")
        assert _reviewer_separation_action(baseline)
        mutated = deepcopy(baseline)
        mutated["evaluated_at"] = None
        _capture_real_rejection(lambda: _reviewer_separation_action(mutated))
        assert baseline["evaluated_at"] is not None and mutated["evaluated_at"] is None
        assert _reviewer_separation_action(baseline)
        return "relation_mismatch"
    baseline = deepcopy(_TEST_RECORDS["golden.owner.author-rank12.000.membership"])
    identity = {
        name: baseline[name]
        for name in MEMBERSHIP_COLUMNS
        if name != "membership_digest"
    }
    baseline["membership_digest"] = membership_digest(identity)
    assert rw0_c1_row_value_from_tuple(
        "rw0_evidence_memberships", tuple(baseline[name] for name in MEMBERSHIP_COLUMNS)
    )
    mutated = deepcopy(baseline)
    mutated["relation_set_digest"] = descriptor["to"]
    _capture_real_rejection(lambda: rw0_c1_row_value_from_tuple(
        "rw0_evidence_memberships", tuple(mutated[name] for name in MEMBERSHIP_COLUMNS)
    ))
    assert mutated["relation_set_digest"] != baseline["relation_set_digest"]
    assert rw0_c1_row_value_from_tuple(
        "rw0_evidence_memberships", tuple(baseline[name] for name in MEMBERSHIP_COLUMNS)
    )
    return "cascade_identity_mismatch"


def _execute_nested_or_resupply_mutation(record_id: str) -> str:
    from test_post_execution_pure_owner_relations import (
        _evidence_supply_action,
        _evidence_supply_owner_inputs,
        _section41_owner_inputs,
    )
    import ge_nwp_coordinator._section41_post_execution_role_resolution as resolution

    if record_id.startswith("malformed.V3G013") or record_id.startswith("malformed.V3G014") or record_id.startswith("malformed.V3G015"):
        baseline = _sample("V40")
        assert CLASS_BY_V["V40"].from_mapping(baseline)
        mutated = deepcopy(baseline)
        locator = mutated["author_observation_locators"][0]
        if record_id.startswith("malformed.V3G013"):
            del locator["schema_id"]
        elif record_id.startswith("malformed.V3G014"):
            mutated["author_observation_locators"][0] = {
                name: locator[name] for name in reversed(tuple(locator))
            }
        else:
            locator["ordinal"] = "0"
        _capture_real_rejection(lambda: CLASS_BY_V["V40"].from_mapping(mutated))
        assert CLASS_BY_V["V40"].from_mapping(baseline)
        return "nested_contract_mismatch"
    if record_id.startswith("malformed.V3G016"):
        owners = _section41_owner_inputs()
        supply = _evidence_supply_owner_inputs()
        family = tuple(
            CLASS_BY_V["V24"].from_mapping(_sample("V24", index))
            for index in range(9)
        )
        arguments = dict(
            requested_role="candidate_capsule", family=family,
            projection=owners["projection"], input_context=owners["context"],
            evidence_supply=CLASS_BY_V["V10"].from_mapping(_sample("V10")),
            evidence_role_values=supply["role_values"],
            evidence_support_values=supply["support_values"],
            evidence_rows=owners["evidence_rows"],
            section41_value=owners["rank15_value"],
            section41_membership_row=owners["rank15_membership"],
        )
        assert resolution.section41_post_execution_role_resolution(
            _sample("V24"), **arguments
        )
        arguments["evidence_role_values"] = ()
        _capture_real_rejection(lambda: resolution.section41_post_execution_role_resolution(
            _sample("V24"), **arguments
        ))
        assert arguments["evidence_role_values"] == ()
        return "no_decision"
    if record_id.startswith("malformed.V3G017"):
        baseline = _sample("V10")
        assert _evidence_supply_action(baseline)
        mutated = deepcopy(baseline)
        mutated["role_supplies"][0]["typed_canonical_value"][
            "repository_ref"
        ] = "repository-substituted.1"
        mutated = _seal("V10", mutated)
        _capture_real_rejection(lambda: _evidence_supply_action(mutated))
        assert _evidence_supply_action(baseline)
        return "basis_conflict"
    if record_id.startswith("malformed.V3G018"):
        baseline = _sample("V07")
        assert CLASS_BY_V["V07"].from_mapping(baseline)
        mutated = deepcopy(baseline)
        mutated["entries"][0] = None
        _capture_real_rejection(lambda: CLASS_BY_V["V07"].from_mapping(mutated))
        assert CLASS_BY_V["V07"].from_mapping(baseline)
        return "no_decision"
    assert record_id.startswith("malformed.V3G019")
    baseline = _sample("V07")
    private_manifest = CLASS_BY_V["V07"].from_mapping(baseline)
    safe_projection = CLASS_BY_V["V05"].from_mapping(_sample("V05"))
    context = CLASS_BY_V["V02"].from_mapping(_sample("V02"))
    assert evidence.validate_post_execution_model_input_binding(
        _sample("V09"), input_context=context, safe_projection=safe_projection,
        private_manifest=private_manifest,
    )
    mutated = deepcopy(baseline)
    mutated["proposal_phase"] = "pre_execution_planning"
    mutated = _seal("V07", mutated)
    _capture_real_rejection(lambda: evidence.validate_post_execution_model_input_binding(
        _sample("V09"), input_context=context, safe_projection=safe_projection,
        private_manifest=CLASS_BY_V["V07"].from_mapping(mutated),
    ))
    assert CLASS_BY_V["V07"].from_mapping(baseline) == private_manifest
    return "basis_conflict"


_MEMBERSHIP_PAGE_MALFORMED_IDS = MALFORMED_RECORD_IDS[19:27]


def _membership_page_transcript_digest(pages: tuple[object, ...]) -> str:
    digest = hashlib.sha256(b"membership-page-transcript.v1\0")
    digest.update(len(pages).to_bytes(8, "big"))
    for page_index, page in enumerate(pages):
        assert type(page) is decision._MembershipPage
        assert type(page.rows) is tuple
        page_bytes = _canonical({
            "capability_epoch": page.capability_epoch,
            "cursor": page.cursor,
            "next_cursor": page.next_cursor,
            "page_index": page_index,
            "rows": [row.to_mapping() for row in page.rows],
        })
        digest.update(len(page_bytes).to_bytes(8, "big"))
        digest.update(page_bytes)
    return digest.hexdigest()


def _accepted_membership_pages(
    rows: tuple[object, ...],
    *,
    capability_epoch: str,
) -> tuple[object, ...]:
    assert 1 <= len(rows) <= 65536
    cursor = (0, "0")
    pages: list[object] = []
    for start in range(0, len(rows), 256):
        page_rows = rows[start:start + 257]
        next_cursor = None
        if len(page_rows) == 257:
            next_cursor = (
                page_rows[255].kind_rank,
                page_rows[255].membership_ref,
            )
        pages.append(decision._MembershipPage(
            capability_epoch, cursor, page_rows, next_cursor
        ))
        if next_cursor is not None:
            cursor = next_cursor
    return tuple(pages)


def _membership_closure_candidate(rows: tuple[object, ...]) -> object:
    mapping = _sample("V25")
    mapping["entries"] = [row.to_mapping() for row in rows]
    mapping["entry_count"] = len(rows)
    return CLASS_BY_V["V25"].from_mapping(_seal("V25", mapping))


def _capture_membership_rejection(action: object) -> str:
    assert callable(action)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        action()
    assert caught.value.__cause__ is None
    return caught.value.reason


def _execute_membership_page_mutation(record_id: str) -> str:
    from test_post_execution_pure_owner_relations import _synthetic_closure_entry

    assert record_id in _MEMBERSHIP_PAGE_MALFORMED_IDS
    suffix = record_id.split(".", 2)[1]
    shared_closure_bytes = _canonical(_sample("V25"))
    shared_entry_bytes = tuple(_canonical(_sample("V26", index)) for index in range(8))
    overflow_row = None
    if suffix in {"V3G020", "V3G022"}:
        rows = tuple(
            CLASS_BY_V["V26"].from_mapping(_sample("V26", index))
            for index in range(8)
        )
        capability_epoch = "epoch.1"
    elif suffix == "V3G024":
        generated = tuple(_synthetic_closure_entry(index) for index in range(65537))
        rows = generated[:65536]
        overflow_row = generated[65536]
        capability_epoch = "epoch.overflow"
    else:
        rows = tuple(_synthetic_closure_entry(index) for index in range(258))
        capability_epoch = "epoch.1"

    positive = _membership_closure_candidate(rows)
    positive_digest = hashlib.sha256(_canonical(positive.to_mapping())).hexdigest()
    baseline_pages = _accepted_membership_pages(
        rows, capability_epoch=capability_epoch
    )
    baseline_transcript_digest = _membership_page_transcript_digest(baseline_pages)
    baseline_result = decision.rw0_c_decision_membership_closure(
        positive, pages=baseline_pages
    )
    assert baseline_result is positive

    if suffix == "V3G020":
        page = baseline_pages[0]
        hostile_rows = (page.rows[0], page.rows[0], *page.rows[2:])
        hostile_pages = (decision._MembershipPage(
            page.capability_epoch, page.cursor, hostile_rows, page.next_cursor
        ),)
        assert hostile_rows[1] is page.rows[0]
        assert hostile_rows[:1] + hostile_rows[2:] == page.rows[:1] + page.rows[2:]
    elif suffix == "V3G021":
        first, second = baseline_pages
        hostile_pages = (first, decision._MembershipPage(
            second.capability_epoch, (0, "0"), second.rows, second.next_cursor
        ))
        assert hostile_pages[0] is first
        assert hostile_pages[1].cursor < second.cursor
        assert (
            hostile_pages[1].capability_epoch,
            hostile_pages[1].rows,
            hostile_pages[1].next_cursor,
        ) == (second.capability_epoch, second.rows, second.next_cursor)
    elif suffix == "V3G022":
        page = baseline_pages[0]
        hostile_rows = (page.rows[1], page.rows[0], *page.rows[2:])
        hostile_pages = (decision._MembershipPage(
            page.capability_epoch, page.cursor, hostile_rows, page.next_cursor
        ),)
        assert hostile_rows[:2] == tuple(reversed(page.rows[:2]))
        assert hostile_rows[2:] == page.rows[2:]
    elif suffix == "V3G023":
        first, second = baseline_pages
        hostile_pages = (decision._MembershipPage(
            first.capability_epoch, first.cursor, first.rows, first.cursor
        ), second)
        assert hostile_pages[0].next_cursor == hostile_pages[0].cursor
        assert (
            hostile_pages[0].capability_epoch,
            hostile_pages[0].cursor,
            hostile_pages[0].rows,
        ) == (first.capability_epoch, first.cursor, first.rows)
        assert hostile_pages[1] is second
    elif suffix == "V3G024":
        assert overflow_row is not None
        terminal = baseline_pages[-1]
        overflow_cursor = (
            terminal.rows[-1].kind_rank,
            terminal.rows[-1].membership_ref,
        )
        hostile_pages = baseline_pages[:-1] + (
            decision._MembershipPage(
                terminal.capability_epoch,
                terminal.cursor,
                terminal.rows + (overflow_row,),
                overflow_cursor,
            ),
            decision._MembershipPage(
                terminal.capability_epoch,
                overflow_cursor,
                (overflow_row,),
                None,
            ),
        )
        assert hostile_pages[:-2] == baseline_pages[:-1]
        assert hostile_pages[-2].rows[:-1] == terminal.rows
        assert hostile_pages[-2].rows[-1] is overflow_row
        assert hostile_pages[-1].rows == (overflow_row,)
    elif suffix == "V3G025":
        assert len(baseline_pages) == 2
        hostile_pages = baseline_pages[:-1]
        assert hostile_pages[0] is baseline_pages[0]
        assert hostile_pages[0].next_cursor is not None
    elif suffix == "V3G026":
        first, second = baseline_pages
        hostile_pages = (first, decision._MembershipPage(
            second.capability_epoch,
            (second.cursor[0], "foreign-membership.1"),
            second.rows,
            second.next_cursor,
        ))
        assert hostile_pages[0] is first
        assert hostile_pages[1].cursor != second.cursor
        assert (
            hostile_pages[1].capability_epoch,
            hostile_pages[1].rows,
            hostile_pages[1].next_cursor,
        ) == (second.capability_epoch, second.rows, second.next_cursor)
    else:
        assert suffix == "V3G027"
        first, second = baseline_pages
        hostile_pages = (first, decision._MembershipPage(
            "epoch.2", second.cursor, second.rows, second.next_cursor
        ))
        assert hostile_pages[0] is first
        assert hostile_pages[1].capability_epoch != second.capability_epoch
        assert (
            hostile_pages[1].cursor,
            hostile_pages[1].rows,
            hostile_pages[1].next_cursor,
        ) == (second.cursor, second.rows, second.next_cursor)

    hostile_transcript_digest = _membership_page_transcript_digest(hostile_pages)
    assert hostile_transcript_digest != baseline_transcript_digest
    actual_reason = _capture_membership_rejection(
        lambda: decision.rw0_c_decision_membership_closure(
            positive, pages=hostile_pages
        )
    )

    restored_pages = _accepted_membership_pages(
        rows, capability_epoch=capability_epoch
    )
    assert restored_pages == baseline_pages
    assert _membership_page_transcript_digest(restored_pages) == baseline_transcript_digest
    restored_result = decision.rw0_c_decision_membership_closure(
        positive, pages=restored_pages
    )
    assert restored_result is positive
    assert hashlib.sha256(_canonical(restored_result.to_mapping())).hexdigest() == positive_digest
    assert _canonical(_sample("V25")) == shared_closure_bytes
    assert tuple(_canonical(_sample("V26", index)) for index in range(8)) == shared_entry_bytes
    return actual_reason


def _current_snapshot_action(candidate: object, chain: dict[str, object]) -> object:
    return decision.rw0_c_decision_current_snapshot(
        candidate,
        lineage_context=chain["lineage"],
        input_context=chain["context"],
        membership_closure=chain["closure"],
        selected_authority_membership=chain["entries"][0],
        selected_section41_membership=chain["entries"][-1],
        global_stop_snapshot=chain["stop"],
        source_effect_ceiling=chain["ceiling"],
        external_sources=chain["sources"],
    )


def _execute_snapshot_mutation(record_id: str) -> str:
    from test_post_execution_pure_owner_relations import _decision_chain

    chain = _decision_chain()
    baseline = _sample("V27")
    assert _current_snapshot_action(baseline, chain)
    if record_id.startswith("malformed.V3G034"):
        unrelated_extra_row = {"table": "unrelated", "row_ref": "unrelated.1"}
        assert unrelated_extra_row not in chain.values()
        assert _current_snapshot_action(baseline, chain) == chain["snapshot"]
        return "bounded_snapshot_unchanged"
    mutated = deepcopy(baseline)
    descriptor = _TEST_RECORDS[record_id]["mutated_canonical_value"]
    pointer = descriptor["json_pointer"]
    if pointer == "/external_current_sources/0/source_digest":
        mutated["external_sources"][0]["source_digest"] = "f" * 64
    else:
        field = pointer.removeprefix("/")
        mutated[field] = descriptor["to"]
    if mutated.get("work_item_revision_ref") is not None:
        mutated = _seal("V27", mutated)
    _capture_real_rejection(lambda: _current_snapshot_action(mutated, chain))
    assert _current_snapshot_action(baseline, chain)
    return "basis_conflict"


def _execute_static_boundary_mutation(record_id: str) -> str:
    """Mutate a concrete source/path/allocation inventory and run its checker."""

    descriptor = _TEST_RECORDS[record_id]["mutated_canonical_value"]
    if record_id.startswith("malformed.V3G035"):
        tree = ast.parse((SOURCE / "__init__.py").read_text())
        baseline = {
            alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        violates = lambda names: any(
            "PostExecutionReviewerSeparation" in name for name in names
        )
        assert violates(baseline) is descriptor["from"]
        mutated = set(baseline)
        mutated.add("PostExecutionReviewerSeparationEvaluationV1")
        assert violates(mutated) is descriptor["to"]
        assert not violates(baseline)
        return "implementation_boundary_violation"
    if record_id.startswith(("malformed.V3G036", "malformed.V3G037")):
        tree = ast.parse((SOURCE / "state_store.py").read_text())
        class_name = "StateStore" if record_id.startswith("malformed.V3G036") else "WriterSession"
        baseline = {
            node.name
            for parent in tree.body
            if isinstance(parent, ast.ClassDef) and parent.name == class_name
            for node in parent.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        violates = lambda names: any(
            "post_execution" in name or "rw0_c" in name for name in names
        )
        assert violates(baseline) is descriptor["from"]
        mutated = set(baseline)
        mutated.add("apply_post_execution_decision")
        assert violates(mutated) is descriptor["to"]
        assert not violates(baseline)
        return "implementation_boundary_violation"
    if record_id.startswith("malformed.V3G038"):
        baseline = tuple(
            path.name for path in sorted((SOURCE / "sqlite_migrations").glob("*.sql"))
        )
        expected = (
            "0001_initial.sql", "0002_development_program_and_effect_state.sql",
            "0003_cognitive_proposal_and_selection_state.sql",
            "0004_rw0_c1_durable_evidence.sql",
            "0005_section41_post_execution_proposal_family.sql",
        )
        violates = lambda names: tuple(names) != expected
        assert not violates(baseline)
        mutated = (*baseline, "0006_post_execution_decision.sql")
        assert violates(mutated) is descriptor["to"]
        assert not violates(baseline)
        return "implementation_boundary_violation"
    if record_id.startswith("malformed.V3G039"):
        baseline = _current_external_post_execution_import_pairs()
        violates = _production_caller_inventory_violates
        assert violates(baseline) is descriptor["from"]
        mutated = set(baseline)
        mutated.add(_V3G039_STATE_STORE_EDGE)
        assert violates(mutated) is descriptor["to"]
        assert not violates(baseline)
        return "implementation_boundary_violation"
    if record_id.startswith(("malformed.V3G040", "malformed.V3G041")):
        tree = ast.parse((SOURCE / "_post_execution_evidence_values.py").read_text())
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        forbidden = {"sqlite3", "pathlib", "socket", "subprocess", "urllib", "requests"}
        if record_id.startswith("malformed.V3G040"):
            violates = lambda names: bool(names & {"sqlite3"})
            assert violates(imported) is descriptor["from"]
            mutated = set(imported)
            mutated.add("sqlite3")
            assert violates(mutated) is descriptor["to"]
            assert not violates(imported)
            return "implementation_boundary_violation"
        assert not imported & forbidden
        base_record = deepcopy(_TEST_RECORDS[
            "value-schema.V40.postexecutionreviewerseparationevaluationv1"
        ])
        assert base_record["local_semantic_action"] == descriptor["from"]
        mutated = deepcopy(base_record)
        mutated["local_semantic_action"] = descriptor["to"]
        violates = lambda allocation, names: (
            allocation["local_semantic_action"] != descriptor["from"]
            or bool(names & forbidden)
        )
        assert not violates(base_record, imported)
        assert violates(mutated, imported)
        assert not violates(base_record, imported)
        return "implementation_boundary_violation"
    if record_id.startswith(("malformed.V3G042", "malformed.V3G043")):
        baseline = {
            value._V_NUMBER for value in CLASS_BY_V.values()
            if isinstance(getattr(value, "_V_NUMBER", None), str)
        }
        violates = lambda numbers: bool({"V35", "V36", "V37"} & numbers)
        assert violates(baseline) is descriptor["from"]
        mutated = set(baseline)
        mutated.add("V35")
        assert violates(mutated) is descriptor["to"]
        assert not violates(baseline)
        return "future_owner_not_frozen"
    assert record_id.startswith("malformed.V3G044")
    baseline = deepcopy(_TEST_RECORDS["remaining-seam.S002"])
    assert baseline["insufficiency_rule"] == descriptor["from"]
    required = tuple(baseline["future_obligation"]["required_retention"])
    def recovery_incomplete(seam: dict[str, object]) -> bool:
        obligation = seam["future_obligation"]
        return (
            seam["insufficiency_rule"]
            != "opaque_aggregate_digests_alone_are_insufficient"
            or tuple(obligation["required_retention"]) != required
            or obligation["retention_posture"]
            != "full_safe_values_or_immutable_locators"
        )
    assert not recovery_incomplete(baseline)
    mutated = deepcopy(baseline)
    mutated["insufficiency_rule"] = descriptor["to"]
    assert recovery_incomplete(mutated)
    assert not recovery_incomplete(baseline)
    return "future_recovery_incomplete"


def _execute_remaining_profile_mutation(record_id: str) -> str:
    if record_id.startswith("malformed.V4I004"):
        baseline = _sample("V26")
        assert CLASS_BY_V["V26"].from_mapping(baseline)
        mutated = deepcopy(baseline)
        del mutated["schema_id"]
        _capture_real_rejection(lambda: CLASS_BY_V["V26"].from_mapping(mutated))
        assert CLASS_BY_V["V26"].from_mapping(baseline)
        return "nested_profile_field_order_mismatch"
    if record_id.startswith("malformed.V5C001"):
        spec = next(
            item for item in CLASS_BY_V["V11"]._FIELD_SPECS
            if item["name"] == "support_canonical_values"
        )
        assert "cardinality" not in spec and spec["rule"]["maximum"] == 16
        mutated = deepcopy(spec)
        mutated["cardinality"] = 0
        def variable_list_contract_failure(candidate: dict[str, object]) -> bool:
            return "cardinality" in candidate
        assert not variable_list_contract_failure(spec)
        assert variable_list_contract_failure(mutated)
        assert not variable_list_contract_failure(spec)
        return "variable_list_contract_contradiction"
    if record_id.startswith("malformed.V5C002"):
        baseline = _sample("V10")
        assert CLASS_BY_V["V10"].from_mapping(baseline)
        mutated = deepcopy(baseline)
        mutated["role_supplies"][4]["support_value_count"] = 5
        mutated["role_supplies"][4]["support_canonical_values"].append(
            deepcopy(mutated["role_supplies"][4]["support_canonical_values"][0])
        )
        _capture_real_rejection(lambda: CLASS_BY_V["V10"].from_mapping(mutated))
        assert CLASS_BY_V["V10"].from_mapping(baseline)
        return "support_inventory_mismatch"
    if record_id.startswith("malformed.V5C003"):
        baseline = _sample("V29")
        assert CLASS_BY_V["V29"].from_mapping(baseline)
        mutated = deepcopy(baseline)
        mutated["components"] = mutated["components"][:4]
        mutated["component_count"] = 4
        _capture_real_rejection(lambda: CLASS_BY_V["V29"].from_mapping(mutated))
        assert CLASS_BY_V["V29"].from_mapping(baseline)
        return "currentness_component_contract_mismatch"
    assert record_id.startswith("malformed.V5C004")
    baseline = _sample("V27")
    assert CLASS_BY_V["V27"].from_mapping(baseline)
    mutated = deepcopy(baseline)
    mutated["external_sources"] = mutated["external_sources"][:4]
    mutated["external_source_count"] = 4
    _capture_real_rejection(lambda: CLASS_BY_V["V27"].from_mapping(mutated))
    assert CLASS_BY_V["V27"].from_mapping(baseline)
    return "snapshot_source_contract_mismatch"


def _execute_metadata_mutation(record_id: str) -> str:
    record = _TEST_RECORDS[record_id]
    descriptor = record["mutated_canonical_value"]
    base = deepcopy(_TEST_RECORDS[record["base_record"]])
    current_hash = hashlib.sha256(_canonical(base)).hexdigest()
    superseded_hashes = {
        "source-owner.migration0003-evidence-set": (
            "d2f87b8c38e9aa3a6c1c3a99f6d8b23cb7468b83812491e3b72341fc59abe2c3",
            "53d7d6957899c9a4a70037941fb41e11c94493438a53c2fcebcc62911e7eb04c",
        ),
        "golden.V10.full-evidence-supply": (
            "bb69d28ed28267c9affeb256ea02e8d05ff1f8e49c1a912bfc896030e851d0a5",
            "a51e693d35d7d6d6eab1bfa553f01a49141ff0fb1603ead7abb692b695d806b3",
        ),
        "golden.V27.primary": (
            "a6b8ef18013f3e635fc05a10958097bd439bb1b2bfe2f70da6ed5eb6d8647e8e",
            "b1fead4f4d647b1b5e5ebe3de6406598d69eb40d17691b85849f9c452f312538",
        ),
    }
    if current_hash != record["base_payload_sha256"]:
        assert superseded_hashes[record["base_record"]] == (
            record["base_payload_sha256"], current_hash
        )
    assert descriptor["from"] != descriptor["to"]
    assert descriptor["operation"] in {"replace", "remove", "add"}
    assert descriptor["json_pointer"].startswith("/")

    if record_id.startswith((
        "malformed.V3G001", "malformed.V3G002", "malformed.V3G003",
        "malformed.V3G004", "malformed.V3G005", "malformed.V3G006",
        "malformed.V3G007", "malformed.V3G008", "malformed.V3G009",
        "malformed.V4I001", "malformed.V4I002", "malformed.V4I003",
    )):
        observed = _execute_source_owner_metadata_mutation(record_id)
    elif record_id.startswith(("malformed.V3G010", "malformed.V3G011", "malformed.V3G012")):
        observed = _execute_relation_or_cascade_mutation(record_id)
    elif record_id.startswith((
        "malformed.V3G013", "malformed.V3G014", "malformed.V3G015",
        "malformed.V3G016", "malformed.V3G017", "malformed.V3G018",
        "malformed.V3G019",
    )):
        observed = _execute_nested_or_resupply_mutation(record_id)
    elif record_id.startswith(tuple(f"malformed.V3G{number:03d}" for number in range(20, 28))):
        observed = _execute_membership_page_mutation(record_id)
    elif record_id.startswith(tuple(f"malformed.V3G{number:03d}" for number in range(28, 35))):
        observed = _execute_snapshot_mutation(record_id)
    elif record_id.startswith(tuple(f"malformed.V3G{number:03d}" for number in range(35, 45))):
        observed = _execute_static_boundary_mutation(record_id)
    else:
        observed = _execute_remaining_profile_mutation(record_id)
    assert type(observed) is str and observed
    return observed


def _v_number_for_schema_record(schema_record_id: str) -> str:
    match = re.fullmatch(r"value-schema\.(V(?:\d+|(?:40|41|42)\.n01))\..+", schema_record_id)
    assert match is not None
    return match.group(1)


def _two_valid_list_items(v_number: str, field: str, mapping: dict[str, object]) -> list[object]:
    current = deepcopy(mapping[field])
    assert type(current) is list
    if len(current) >= 2:
        return current[:2]
    if field in {"source_evidence_refs", "result_set_evidence_refs"}:
        return ["evidence.alpha", "evidence.beta"]
    if field == "allowed_risk_lanes":
        return ["risk.alpha", "risk.standard"]
    if field == "allowed_branches":
        return [BRANCHES[0][0], BRANCHES[1][0]]
    if field in {
        "allowed_effect_classes", "attempt_allowed_effect_classes",
        "authority_allowed_effect_classes",
    }:
        return ["author_candidate", "review_candidate"]
    raise AssertionError((v_number, field, current))


def _list_case_base(v_number: str, field: str) -> dict[str, object]:
    if v_number == "V11" and field == "support_canonical_values":
        return _sample("V11", 7)
    if v_number == "V13" and field == "entries":
        return _ordered_fixture("V13", _TEST_RECORDS["golden.V13.global-stop.support-set"])
    return _sample(v_number)


def _execute_list_contract_family(record_id: str) -> str:
    record = _TEST_RECORDS[record_id]
    operation = record["mutated_canonical_value"]["operation"]
    cases = record["mutated_canonical_value"]["finite_cases"]
    assert len(cases) == record.get("expected_case_count", len(cases))
    for case in cases:
        v_number = _v_number_for_schema_record(case["schema_record_id"])
        field = case["field"]
        mapping = _list_case_base(v_number, field)
        original = _canonical(mapping)
        mutated = deepcopy(mapping)
        if operation == "underflow":
            mutated[field] = []
        elif operation == "overflow":
            mutated[field] = [None] * case["length"]
        else:
            pair = _two_valid_list_items(v_number, field, mapping)
            mutated[field] = list(reversed(pair)) if operation == "reorder" else [pair[0], pair[0]]
        if operation in {"reorder", "duplicate"} and field == "entries" and "entry_count" in mutated:
            mutated["entry_count"] = len(mutated[field])
        if operation in {"reorder", "duplicate"} and field == "support_canonical_values":
            mutated["support_value_count"] = len(mutated[field])
        assert _canonical(mutated) != original
        with pytest.raises(evidence._PostExecutionContractViolation) as caught:
            CLASS_BY_V[v_number].from_mapping(mutated)
        if operation in {"underflow", "overflow"}:
            assert caught.value.reason in {"invalid_cardinality", "relation_mismatch", "evaluation_contract_mismatch"}
        elif operation == "duplicate":
            assert caught.value.reason in {
                "duplicate_entry", "invalid_reference", "relation_mismatch",
                "evaluation_contract_mismatch",
            }
        else:
            assert caught.value.reason in {
                "invalid_field_value", "source_owner_mismatch", "relation_mismatch",
                "evaluation_contract_mismatch",
            }
        assert _canonical(mapping) == original
    expected = {
        "underflow": "reject_underflow", "overflow": "reject_overflow",
        "reorder": "reject_reorder", "duplicate": "reject_duplicate",
    }[operation]
    assert record["expected_rejection"] == expected
    return expected


def _ordered_invalid_candidate(v_number: str, payload: dict[str, object]) -> dict[str, object]:
    cls = CLASS_BY_V[v_number]
    if tuple(payload) == cls._FIELDS:
        return deepcopy(payload)
    if set(payload) == set(cls._FIELDS):
        return _ordered_fixture(v_number, payload)
    return deepcopy(payload)


_ORDINARY_FIRST_FAILURE_BY_EXPECTED_REJECTION = {
    "expired_fence_denial": "evaluation_contract_mismatch",
    "current_sha1_domain_rejection": "relation_mismatch",
    "current_40_hex_oid_rejection": "invalid_field_value",
    "expired_effect_fence_denial": "evaluation_contract_mismatch",
    "adapter_generic_interface_mismatch": "invalid_schema_id",
    "stop_branch_matrix_conflict": "evaluation_contract_mismatch",
    "policy_source_identity_mismatch": "invalid_digest",
    "profile_value_mismatch": "invalid_profile_pair",
    "requirement_safe_identity_mismatch": "invalid_reference",
    "current_observation_matrix_rejection": "invalid_field_value",
    "risk_source_identity_mismatch": "source_owner_mismatch",
    "stale_superseded_identity": "unknown_field",
    "unknown_field_and_unsupported_claim": "unknown_field",
    "unknown/author_source_evidence_absent": "invalid_cardinality",
    "conflict/author_source_evidence_conflict": "source_owner_mismatch",
    "conflict/cross_lineage_conflict": "invalid_reference",
    "not_separate/review_delivery_identity_reused": "evaluation_contract_mismatch",
    "not_separate/review_effect_identity_reused": "evaluation_contract_mismatch",
    "not_separate/review_source_invocation_reused": "evaluation_contract_mismatch",
    "conflict/same_phase_closure_conflict": "invalid_reference",
    "conflict/source_role_conflict": "invalid_field_value",
    "schema_or_reference_mismatch": "invalid_reference",
    "current_relation_spec_mismatch": "current_relation_spec_mismatch",
    "role_digest_mismatch": "relation_mismatch",
    "role_ref_mismatch": "relation_mismatch",
    "role_schema_mismatch": "source_owner_mismatch",
    "work_spec_pair_mismatch": "invalid_reference",
}


def _rank14_relation_spec_failure(payload: dict[str, object]) -> str | None:
    expected = (
        "governed-execution.nwp-rw0-c1-wire-process-result-relation.v1"
    )
    if payload["relation_schema_id"] != expected:
        return "current_relation_spec_mismatch"
    return None


def _execute_ordinary_semantic_malformed(record_id: str) -> str:
    record = _TEST_RECORDS[record_id]
    payload = deepcopy(record["mutated_canonical_value"])
    base = record["base_record"]
    actual_reason: str | None = None
    try:
        if base == "WorkerObservationV1":
            WorkerObservationV1.from_mapping(payload)
        elif base == "rank14":
            actual_reason = _rank14_relation_spec_failure(payload)
        else:
            v_number = base if base in CLASS_BY_V else "V32" if base.startswith("golden.V32") else None
            assert v_number is not None, record_id
            candidate = _ordered_invalid_candidate(v_number, payload)
            if v_number == "V40":
                from test_post_execution_pure_owner_relations import (
                    _reviewer_separation_action,
                )
                _reviewer_separation_action(candidate)
            elif v_number == "V17":
                policy.validate_post_execution_standing_policy_matrix_relation(
                    candidate, policy_source=CLASS_BY_V["V41"].from_mapping(_sample("V41"))
                )
            elif v_number == "V18":
                policy.validate_post_execution_risk_lane_matrix_relation(
                    candidate,
                    risk_policy=CLASS_BY_V["V42"].from_mapping(_sample("V42")),
                    source_profile=CLASS_BY_V["V43"].from_mapping(_sample("V43")),
                    source_binding=CLASS_BY_V["V44"].from_mapping(_sample("V44")),
                )
            elif v_number == "V19":
                adapter.finite_backlog_risk_source_projection(
                    candidate,
                    evaluated_at="2026-09-30T11:59:53Z",
                    expires_at="2026-10-01T01:30:00Z",
                )
            elif v_number in {"V21", "V32", "V33"}:
                from test_post_execution_pure_owner_relations import (
                    _active_stop_snapshot,
                    _decision_chain,
                    _source_ceiling_action_inputs,
                )
                if v_number == "V21":
                    _baseline, attempt, effect, authority, matrix, support = _source_ceiling_action_inputs()
                    evidence.evaluate_post_execution_source_effect_ceiling(
                        candidate, attempt_fence=attempt, effect_fence=effect,
                        authority_observation=authority, standing_policy_matrix=matrix,
                        support_set=support,
                    )
                elif v_number == "V32":
                    stop, _state = _active_stop_snapshot()
                    snapshot = CLASS_BY_V["V27"].from_mapping(_sample("V27", 1))
                    decision.evaluate_rw0_c_decision_time_global_stop_branches(
                        candidate, snapshot=snapshot, global_stop_snapshot=stop
                    )
                else:
                    chain = _decision_chain()
                    decision.evaluate_rw0_c_decision_time_source_effect_ceiling_branches(
                        candidate,
                        snapshot=chain["snapshot"],
                        source_effect_ceiling=chain["ceiling"],
                        lineage_context=chain["lineage"],
                    )
            elif v_number == "V03":
                role_entries = [
                    CLASS_BY_V["V03"].from_mapping(_sample("V03", index))
                    for index in range(9)
                ]
                role_entries[0] = CLASS_BY_V["V03"].from_mapping(candidate)
                evidence.construct_post_execution_semantic_review_input(
                    _sample("V02"),
                    lineage_context=CLASS_BY_V["V01"].from_mapping(_sample("V01")),
                    role_entries=tuple(role_entries),
                    safe_projection=CLASS_BY_V["V05"].from_mapping(_sample("V05")),
                    private_manifest=CLASS_BY_V["V07"].from_mapping(_sample("V07")),
                )
            else:
                CLASS_BY_V[v_number].from_mapping(candidate)
    except evidence._PostExecutionContractViolation as caught:
        actual_reason = caught.reason
    except Exception as caught:  # current owner values use their own closed exception types
        actual_reason = getattr(caught, "reason", type(caught).__name__)
    assert actual_reason is not None, record_id
    expected_rejection = record["expected_rejection"]
    assert type(expected_rejection) is str and expected_rejection
    assert actual_reason == _ORDINARY_FIRST_FAILURE_BY_EXPECTED_REJECTION[expected_rejection]
    return expected_rejection


def _execute_v9_parent_bound_unknown_fields() -> str:
    record = _TEST_RECORDS["malformed.V9R001.v16-parent-bound-extra-field-rejection"]
    base = record["valid_base_entry"]
    base_bytes = _canonical(base)
    for mutation in record["mutations"]:
        assert set(mutation["mutated_entry"]) - set(base) == {mutation["added_key"]}
        parent = _sample("V32", 1)
        parent["entries"] = [deepcopy(mutation["mutated_entry"]), *parent["entries"][1:]]
        parent["matrix_ref"] = "wrong-parent.1"
        parent["matrix_digest"] = "0" * 64
        assert _reason(CLASS_BY_V["V32"], parent) == "unknown_field"
        restored = deepcopy(mutation["mutated_entry"])
        del restored[mutation["added_key"]]
        assert _canonical(restored) == base_bytes
    return record["expected_rejection"]


def _execute_v11_parent_dispatch_reasons() -> str:
    record = _TEST_RECORDS["malformed.V11R001.v16-dispatched-reason-stale"]
    for case in record["cases"]:
        base_record = case["base_record"]
        v_number = base_record.split(".")[1]
        parent = _ordered_fixture(v_number, _TEST_RECORDS[base_record])
        index = next(
            index for index, child in enumerate(parent["entries"])
            if child == case["base_child"]
        )
        original = _canonical(parent["entries"][index])
        parent["entries"][index] = _ordered_fixture("V16", case["mutated_child"])
        parent["matrix_ref"] = "wrong-parent.1"
        parent["matrix_digest"] = "0" * 64
        assert _reason(CLASS_BY_V[v_number], parent) == "evaluation_contract_mismatch"
        assert hashlib.sha256(original).hexdigest() == case["restored_child_raw_sha256"]
    return record["expected_rejection"]


def _execute_v8_current_row_self_digest_mutations() -> str:
    record = _TEST_RECORDS["malformed.V8R001.migration0003-evidence-row-self-digest-stale"]
    for mutation in record["mutations"]:
        base = deepcopy(_TEST_RECORDS[mutation["base_record"]])
        base_bytes = _canonical(base)
        assert base["evidence_binding_digest"] == mutation["from"]
        base["evidence_binding_digest"] = mutation["to"]
        with pytest.raises(Exception):
            DevelopmentModelProposalEvidenceBindingRowValue(**base)
        base["evidence_binding_digest"] = mutation["from"]
        restored = DevelopmentModelProposalEvidenceBindingRowValue(**base)
        assert restored.to_mapping() == base
        assert _canonical(base) == base_bytes
    return record["expected_rejection"]


def _execute_v6_rank15_cascade_mutations() -> str:
    from ge_nwp_coordinator._rw0_c1_row_values import (
        MEMBERSHIP_COLUMNS,
        RELATION_COLUMNS,
        rw0_c1_row_value_from_tuple,
    )
    from ge_nwp_coordinator._rw0_c1_semantic_values import (
        RW0C1Section41PostExecutionProposalFamilyMemberV1,
    )
    import ge_nwp_coordinator._section41_post_execution_proposal_family_projection as projection
    from test_post_execution_pure_owner_relations import _section41_owner_inputs

    record = _TEST_RECORDS["malformed.V6R001.rank15-current-owner-cascade-stale"]
    owners = _section41_owner_inputs()

    def project(**overrides: object) -> object:
        values = dict(owners)
        values.update(overrides)
        return projection.section41_post_execution_proposal_family_projection(
            _sample("V22"), input_context=values["context"],
            source_invocation_row=values["source"], artifact_binding_row=values["artifact"],
            proposal_row=values["proposal_row"], evidence_rows=values["evidence_rows"],
            private_reader_tuples=values["reader_rows"], owner_locators=values["owner_locators"],
            rank15_value=values["rank15_value"], rank15_relation_row=values["rank15_relation"],
            rank15_admission_graph=values["rank15_graph"],
            rank15_membership_row=values["rank15_membership"],
            admitted_by_mutation_ref=values["rank15_graph"]["admitted_by_mutation_ref"],
        )

    for mutation in record["mutations"][:4]:
        pointer = mutation["json_pointer"]
        if pointer == "/owner_family_graph_digest":
            mapping = deepcopy(_TEST_RECORDS["golden.owner.rank15.value"])
            mapping.pop("schema_id")
            mapping["owner_family_graph_digest"] = mutation["to"]
            try:
                value = RW0C1Section41PostExecutionProposalFamilyMemberV1(**mapping)
            except Exception:
                pass
            else:
                with pytest.raises(evidence._PostExecutionContractViolation):
                    project(rank15_value=value)
        elif pointer == "/value_digest":
            graph = deepcopy(owners["rank15_graph"])
            graph["value_digest"] = mutation["to"]
            with pytest.raises(evidence._PostExecutionContractViolation):
                project(rank15_graph=graph)
        else:
            relation_mapping = deepcopy(_TEST_RECORDS["golden.owner.rank15.relation"])
            relation_mapping[pointer.removeprefix("/")] = mutation["to"]
            with pytest.raises(Exception):
                rw0_c1_row_value_from_tuple(
                    "rw0_relation_bindings",
                    tuple(relation_mapping[name] for name in RELATION_COLUMNS),
                )

    mutation = record["mutations"][4]
    graph = deepcopy(owners["rank15_graph"])
    graph["admitted_by_mutation_ref"] = mutation["to"]
    with pytest.raises(evidence._PostExecutionContractViolation):
        project(rank15_graph=graph)

    membership_mapping = deepcopy(_TEST_RECORDS["golden.owner.rank15.membership"])
    membership_mapping["admitted_by_mutation_ref"] = mutation["to"]
    with pytest.raises(Exception):
        rw0_c1_row_value_from_tuple(
            "rw0_evidence_memberships",
            tuple(membership_mapping[name] for name in MEMBERSHIP_COLUMNS),
        )
    return record["expected_rejection"]


def _execute_malformed_record(record_id: str) -> str:
    record = _TEST_RECORDS[record_id]
    if "base_payload_sha256" in record:
        observed = _execute_metadata_mutation(record_id)
    elif record_id.startswith("malformed.V5L"):
        observed = _execute_list_contract_family(record_id)
    elif record_id.startswith("malformed.V6R001"):
        observed = _execute_v6_rank15_cascade_mutations()
    elif record_id.startswith("malformed.V8R001"):
        observed = _execute_v8_current_row_self_digest_mutations()
    elif record_id.startswith("malformed.V9R001"):
        observed = _execute_v9_parent_bound_unknown_fields()
    elif record_id.startswith("malformed.V11R001"):
        observed = _execute_v11_parent_dispatch_reasons()
    else:
        observed = _execute_ordinary_semantic_malformed(record_id)
    if record_id in _MEMBERSHIP_PAGE_MALFORMED_IDS:
        assert record["expected_rejection"] == "basis_conflict"
        return observed
    assert observed == record["expected_rejection"]
    return observed


@pytest.mark.parametrize("record_id", MALFORMED_RECORD_IDS)
def test_each_of_93_malformed_controls_executes_its_causal_mutation(record_id: str) -> None:
    assert len(MALFORMED_RECORD_IDS) == 93
    _execute_malformed_record(record_id)


def test_v4_membership_paging_actions_are_reachable_and_exactly_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    production_action = decision.rw0_c_decision_membership_closure
    trace: list[tuple[int, str]] = []

    def traced_action(value: object, *, pages: tuple[object, ...]) -> object:
        trace.append((id(value), _membership_page_transcript_digest(pages)))
        return production_action(value, pages=pages)

    monkeypatch.setattr(decision, "rw0_c_decision_membership_closure", traced_action)
    for record_id in _MEMBERSHIP_PAGE_MALFORMED_IDS:
        trace.clear()
        actual_reason = _execute_malformed_record(record_id)
        assert type(actual_reason) is str and actual_reason
        assert len(trace) == 3
        assert trace[0][0] == trace[1][0] == trace[2][0]
        assert trace[0][1] == trace[2][1]
        assert trace[1][1] != trace[0][1]


def test_malformed_causality_path_has_no_test_authored_semantic_self_raise() -> None:
    tree = ast.parse(Path(__file__).read_text())
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    forbidden_functions: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        call = node.exc
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "_FrozenVectorViolation"
        ):
            continue
        parent = parents[node]
        while not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = parents[parent]
        forbidden_functions.append(parent.name)
    assert forbidden_functions == ["pairs"]
    assert all(
        not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        or node.name != "_metadata_first_failure"
        for node in ast.walk(tree)
    )
    metadata_node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_execute_metadata_mutation"
    )
    assert "expected_rejection" not in ast.unparse(metadata_node)
    membership_node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_execute_membership_page_mutation"
    )
    membership_returns = [
        node for node in ast.walk(membership_node)
        if isinstance(node, ast.Return)
    ]
    assert len(membership_returns) == 1
    assert membership_node.body[-1] is membership_returns[0]
    assert isinstance(membership_returns[0].value, ast.Name)
    assert membership_returns[0].value.id == "actual_reason"
    membership_calls = [
        node for node in ast.walk(membership_node)
        if isinstance(node, ast.Call)
    ]
    action_calls = [
        node for node in membership_calls
        if isinstance(node.func, ast.Attribute)
        and node.func.attr == "rw0_c_decision_membership_closure"
    ]
    capture_calls = [
        node for node in membership_calls
        if isinstance(node.func, ast.Name)
        and node.func.id == "_capture_membership_rejection"
    ]
    assert len(action_calls) == 3
    assert len(capture_calls) == 1
    assert action_calls[0].lineno < capture_calls[0].lineno < action_calls[-1].lineno
    assert membership_returns[0].lineno > action_calls[-1].lineno
    assert not any(isinstance(node, ast.Raise) for node in ast.walk(membership_node))
    assert "expected_rejection" not in ast.unparse(membership_node)
    assert all(
        not isinstance(node, ast.Constant) or node.value != "basis_conflict"
        for node in ast.walk(membership_node)
    )


V3_CAUSAL_ASSURANCE_ACTIONS = {
    "assurance.V3.v22-fully-resealed-model-contract-mismatch": (
        "test_v22_fully_resealed_source_proposal_model_contract_mismatch_rejects_causally"
    ),
}


@pytest.mark.parametrize("assurance_id", tuple(V3_CAUSAL_ASSURANCE_ACTIONS))
def test_v3_causal_assurance_registry_executes_production_path(
    assurance_id: str,
) -> None:
    import test_post_execution_pure_owner_relations as relation_tests

    action = getattr(relation_tests, V3_CAUSAL_ASSURANCE_ACTIONS[assurance_id])
    action()


def _artifact_json_without_duplicate_keys(raw: str) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise _FrozenVectorViolation("duplicate_json_key")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _value: (_ for _ in ()).throw(
        _FrozenVectorViolation("nonfinite_number")
    ))


def _execute_artifact_assurance(assurance_id: str) -> None:
    payload = {"case": "finite", "value": 1}
    canonical = _canonical(payload)
    raw_sha = hashlib.sha256(canonical).hexdigest()
    domain = _digest("governed-execution.test-record.v1", payload)
    records = [
        {"record_index": 0, "record_id": "r.0", "payload_raw_sha256": raw_sha},
        {"record_index": 1, "record_id": "r.1", "payload_raw_sha256": raw_sha},
    ]

    if assurance_id == "A002":
        with pytest.raises(_FrozenVectorViolation):
            _artifact_json_without_duplicate_keys('{"case":"finite","case":"other","value":1}')
    elif assurance_id == "A003":
        noncanonical = b'{"value": 1, "case": "finite"}'
        assert _canonical(_artifact_json_without_duplicate_keys(noncanonical.decode())) != noncanonical
    elif assurance_id == "A004":
        assert len(canonical) != len(canonical) + 1
    elif assurance_id == "A005":
        assert raw_sha != "0" * 64
    elif assurance_id == "A006":
        assert domain != _digest("governed-execution.other-domain.v1", payload)
    elif assurance_id == "A007":
        mutated = deepcopy(records)
        mutated[1]["record_index"] = 2
        assert [item["record_index"] for item in mutated] != list(range(len(mutated)))
    elif assurance_id == "A008":
        mutated = deepcopy(records)
        mutated[1]["record_id"] = mutated[0]["record_id"]
        assert len({item["record_id"] for item in mutated}) != len(mutated)
    elif assurance_id == "A009":
        ordered = [(item["record_id"], item["payload_raw_sha256"]) for item in records]
        mutated = deepcopy(ordered)
        mutated.reverse()
        assert mutated != ordered
    elif assurance_id == "A010":
        aggregate = hashlib.sha256(_canonical(records)).hexdigest()
        assert aggregate != hashlib.sha256(_canonical(records[:-1])).hexdigest()
    elif assurance_id == "A011":
        assert len(records) != len(records) + 1
    elif assurance_id == "A012":
        assert canonical.endswith(b"\n") is False
        assert (canonical + b"\n").endswith(b"\n") is True
    elif assurance_id == "A013":
        assert not canonical.startswith(b"\xef\xbb\xbf")
        assert (b"\xef\xbb\xbf" + canonical).startswith(b"\xef\xbb\xbf")
    else:
        assert assurance_id == "A014"
        with pytest.raises((_FrozenVectorViolation, json.JSONDecodeError)):
            _artifact_json_without_duplicate_keys('{"value":NaN}')
        assert type(_artifact_json_without_duplicate_keys('{"value":1.5}')["value"]) is float


def _execute_positive_rank14_owner() -> None:
    from ge_nwp_coordinator._rw0_c1_semantic_values import (
        RW0C1MemberLocatorV1,
        RW0C1WireProcessResultClassificationBindingV1,
    )

    payload = deepcopy(_TEST_RECORDS["golden.owner.rank14.value"])
    expected = deepcopy(payload)
    payload.pop("schema_id")
    payload.pop("wire_profile_ref")
    payload.pop("wire_profile_digest")
    for name in ("result_membership", "request_membership"):
        if payload[name] is not None:
            payload[name] = RW0C1MemberLocatorV1(**payload[name])
    for name in ("adapter_observations", "process_observations"):
        payload[name] = tuple(RW0C1MemberLocatorV1(**item) for item in payload[name])
    assert RW0C1WireProcessResultClassificationBindingV1(**payload).to_mapping() == expected


def _execute_v40_negative(malformed_suffix: str) -> None:
    _execute_malformed_record(f"malformed.{malformed_suffix}")


def _execute_assurance_a(record_id: str) -> None:
    assurance_id = record_id.removeprefix("assurance.")
    if assurance_id == "A001":
        for v_number, cls in CLASS_BY_V.items():
            mapping = _sample(v_number)
            mapping["unexpected"] = "value"
            assert _reason(cls, mapping) == "unknown_field"
        _execute_v9_parent_bound_unknown_fields()
    elif "A002" <= assurance_id <= "A014":
        _execute_artifact_assurance(assurance_id)
    elif assurance_id == "A015":
        assert CLASS_BY_V["V04"].from_mapping(_sample("V04")).base_git_object_format == "sha1"
    elif assurance_id == "A016":
        _execute_malformed_record("malformed.candidate-git-sha256")
        _execute_malformed_record("malformed.candidate-git-wrong-oid-width")
    elif assurance_id == "A017":
        value = CLASS_BY_V["V38"].from_mapping(_sample("V38"))
        assert value.requirement_evidence_safe_digest != value.requirement_digest
    elif assurance_id == "A018":
        _execute_malformed_record("malformed.requirement-embedded-digest-substitution")
    elif assurance_id == "A019":
        _execute_positive_rank14_owner()
    elif assurance_id == "A020":
        _execute_malformed_record("malformed.wrong-rank14-relation-identity")
    elif assurance_id == "A021":
        value = policy.validate_post_execution_standing_policy_attestation(_sample("V41"))
        assert "permission" not in value.to_mapping()
    elif assurance_id == "A022":
        value = policy.validate_post_execution_risk_policy_attestation(_sample("V42"))
        assert "permission" not in value.to_mapping()
    elif assurance_id == "A023":
        tree = ast.parse((SOURCE / "_post_execution_policy_values.py").read_text())
        assert not any(
            isinstance(node, ast.ImportFrom)
            and node.module == "_finite_backlog_risk_source_adapter"
            for node in ast.walk(tree)
        )
    elif assurance_id == "A024":
        proposed = {
            "_post_execution_evidence_values", "_post_execution_policy_values",
            "_rw0_c_decision_input_values",
        }
        for name in ("_sqlite_rw0_c1.py", "_worker_execution_semantic_values.py", "__init__.py"):
            tree = ast.parse((SOURCE / name).read_text())
            imported = {
                node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            assert proposed.isdisjoint(imported)
    elif assurance_id in {"A025", "A026", "A027"}:
        from test_post_execution_pure_owner_relations import (
            _reviewer_separation_action,
        )
        value = _reviewer_separation_action(_sample("V40"))
        assert (value.review_source_kind, value.author_source_kind, value.status) == (
            "independent_reviewer", "worker", "separate"
        )
    elif assurance_id == "A028":
        _execute_v40_negative("v40-invocation-reuse")
    elif assurance_id == "A029":
        _execute_v40_negative("v40-author-invocation-conflict")
    elif assurance_id == "A030":
        _execute_v40_negative("v40-effect-reuse")
    elif assurance_id == "A031":
        _execute_v40_negative("v40-delivery-reuse")
    elif assurance_id in {"A032", "A033"}:
        _execute_v40_negative("v40-wrong-review-role")
    elif assurance_id == "A034":
        _execute_v40_negative("v40-phase-lineage")
    elif assurance_id == "A035":
        _execute_v40_negative("v40-candidate-lineage")
        _execute_v40_negative("v40-capsule-lineage")
    elif assurance_id == "A036":
        _execute_v40_negative("v40-author-evidence-absent")
    elif assurance_id == "A037":
        _execute_v40_negative("v40-author-invocation-conflict")
    elif assurance_id == "A038":
        _execute_v40_negative("v40-phase-lineage")
    elif assurance_id == "A039":
        _execute_v40_negative("unsupported-identity-authentication-claim")
    elif assurance_id == "A040":
        _execute_v40_negative("stale-superseded-identity")
    elif assurance_id == "A041":
        from test_post_execution_pure_owner_relations import (
            _reviewer_separation_action,
        )
        value = evidence.validate_independent_review_disposition(
            _sample("V15"), review_result_set=CLASS_BY_V["V39"].from_mapping(_sample("V39")),
            reviewer_separation=_reviewer_separation_action(_sample("V40")),
        )
        assert value.result == "passed"
    elif assurance_id in {"A042", "A043", "A044"}:
        suffix = {"A042": "v40-author-evidence-absent", "A043": "v40-invocation-reuse", "A044": "v40-wrong-review-role"}[assurance_id]
        _execute_v40_negative(suffix)
    elif assurance_id == "A045":
        record_ids = sorted(key for key in _TEST_RECORDS if key.startswith("golden.V13."))
        values = [CLASS_BY_V["V13"].from_mapping(_ordered_fixture("V13", _TEST_RECORDS[key])) for key in record_ids]
        assert len(values) == 7 and all(value.entries for value in values)
    elif assurance_id == "A046":
        from test_post_execution_pure_owner_relations import _evidence_supply_action
        assert _evidence_supply_action(_sample("V10")).role_supply_count == 9
    elif assurance_id == "A047":
        from test_post_execution_pure_owner_relations import _section41_owner_inputs
        owners = _section41_owner_inputs()
        assert len(owners["evidence_rows"]) == 9 and len(owners["owner_locators"]) == 12
    elif assurance_id == "A048":
        mapping = CLASS_BY_V["V05"].from_mapping(_sample("V05")).to_mapping()
        assert "typed_canonical_value" not in json.dumps(mapping, sort_keys=True)
    elif assurance_id == "A049":
        _execute_v40_negative("stale-superseded-identity")
    elif assurance_id == "A050":
        assert all(v_number not in CLASS_BY_V for v_number in ("V35", "V36", "V37"))
    elif assurance_id == "A051":
        for v_number in ("V17", "V18", "V31", "V32", "V33"):
            mapping = CLASS_BY_V[v_number].from_mapping(_sample(v_number)).to_mapping()
            assert "authorization" not in mapping and "permission" not in mapping
    elif assurance_id == "A052":
        profile, binding = adapter.finite_backlog_risk_source_projection(
            _sample("V19"), evaluated_at="2026-09-30T11:59:53Z", expires_at="2026-10-01T01:30:00Z"
        )
        assert profile.external_authority_claim is False
        assert binding.source_value_schema_id == CLASS_BY_V["V19"]._SCHEMA_ID
    elif assurance_id == "A053":
        from test_post_execution_pure_owner_relations import _decision_chain
        chain = _decision_chain()
        candidate = _sample("V27")
        candidate["work_item_revision_ref"] = "work-item-revision-advanced.1"
        candidate = _seal("V27", candidate)
        with pytest.raises(evidence._PostExecutionContractViolation):
            decision.rw0_c_decision_current_snapshot(
                candidate, input_context=chain["context"],
                lineage_context=chain["lineage"], membership_closure=chain["closure"],
                selected_authority_membership=chain["entries"][0],
                selected_section41_membership=chain["entries"][-1],
                global_stop_snapshot=chain["stop"], source_effect_ceiling=chain["ceiling"],
                external_sources=chain["sources"],
            )
    elif assurance_id == "A054":
        from test_post_execution_pure_owner_relations import _decision_chain
        chain = _decision_chain()
        snapshot_mapping = chain["snapshot"].to_mapping()
        snapshot_mapping["external_sources"][0]["source_available"] = False
        unavailable_snapshot = CLASS_BY_V["V27"].from_mapping(_seal("V27", snapshot_mapping))
        mapping = _sample("V29")
        mapping["snapshot_ref"] = unavailable_snapshot.snapshot_ref
        mapping["snapshot_digest"] = unavailable_snapshot.snapshot_digest
        mapping["components"][0]["result"] = "unknown"
        mapping["components"][0]["reason"] = "source_unavailable"
        mapping["result"] = "unknown"
        mapping["reason"] = "component_source_unknown"
        mapping = _seal("V29", mapping)
        currentness = decision.evaluate_rw0_c_proposal_evidence_currentness(
            mapping, projection=chain["projection"], snapshot=unavailable_snapshot,
            proposal_evidence=tuple(
                CLASS_BY_V[v_number].from_mapping(_sample(v_number))
                for v_number in ("V14", "V15", "V17", "V18")
            ),
            proposal_sources=chain["sources"],
        )
        assert currentness.result == "unknown"
    elif assurance_id in {"A055", "A059"}:
        from test_post_execution_pure_owner_relations import _active_stop_snapshot
        stop, _state = _active_stop_snapshot()
        snapshot = CLASS_BY_V["V27"].from_mapping(_sample("V27", 1))
        matrix = decision.evaluate_rw0_c_decision_time_global_stop_branches(
            _sample("V32", 1), snapshot=snapshot, global_stop_snapshot=stop
        )
        assert matrix.entries[0].result == "deny"
        assert matrix.entries[-1].result == "permit"
    elif assurance_id == "A056":
        _execute_malformed_record("malformed.attempt-fence-expiry-substitution")
    elif assurance_id == "A057":
        from test_post_execution_pure_owner_relations import _decision_chain
        chain = _decision_chain()
        candidate = _sample("V34")
        candidate.update(
            model_recommendation="repair_candidate", mapped_branch="candidate_repair",
            result="inconsistent", reason="mapped_branch_differs_from_authoritative_branch",
        )
        candidate = _seal("V34", candidate)
        value = decision.evaluate_rw0_c_recommendation_consistency(
            candidate, projection=chain["projection"], snapshot=chain["snapshot"],
            proposal_currentness=chain["currentness"], authority_matrix=chain["authority_matrix"],
            global_stop_matrix=chain["stop_matrix"], source_effect_ceiling_matrix=chain["ceiling_matrix"],
            authoritative_branch="candidate_acceptance", lineage_context=chain["lineage"],
            input_context=chain["context"], membership_closure=chain["closure"],
            selected_authority_membership=chain["entries"][0], global_stop_snapshot=chain["stop"],
            source_effect_ceiling=chain["ceiling"],
        )
        assert value.result == "inconsistent"
    elif assurance_id == "A058":
        combined = "\n".join((SOURCE / name).read_text() for name in (
            "_post_execution_evidence_values.py", "_post_execution_policy_values.py",
            "_finite_backlog_risk_source_adapter.py", "_section41_post_execution_proposal_family_projection.py",
            "_section41_post_execution_role_resolution.py", "_rw0_c_decision_input_values.py",
        ))
        assert "Independent_Audit_Report" not in combined and "Canonical_Audit_Package" not in combined
    elif assurance_id == "A060":
        for rank, role in enumerate((
            "candidate_capsule", "worker_result", "validation_result", "independent_review",
            "standing_policy", "risk_lane", "authority_currentness_attestation", "global_stop", "effect_ceiling",
        ), 5):
            payload = _TEST_RECORDS[f"golden.owner.proposal-evidence-row.{rank:02d}.{role}"]
            assert DevelopmentModelProposalEvidenceBindingRowValue(**payload).to_mapping() == payload
    elif assurance_id in {"A061", "A063"}:
        from test_post_execution_pure_owner_relations import _section41_owner_inputs
        owners = _section41_owner_inputs()
        assert owners["projection"].owner_family_graph_digest == owners["rank15_value"].owner_family_graph_digest
        assert owners["rank15_graph"]["membership_ref"] == owners["rank15_membership"].to_mapping()["membership_ref"]
    else:
        assert assurance_id == "A062"
        for v_number in ("V17", "V18", "V31", "V32", "V33"):
            value = CLASS_BY_V[v_number].from_mapping(_sample(v_number))
            assert len(value.entries) == 5


def _execute_non_a_assurance(record_id: str) -> None:
    suffix = record_id.removeprefix("assurance.")
    paired = f"malformed.{suffix}"
    if paired in _TEST_RECORDS:
        _execute_malformed_record(paired)
        return
    if suffix == "V5L001.fixed-min-boundaries":
        for v_number, field in (("V13", "entries"), ("V17", "allowed_branches"), ("V40", "author_observation_locators")):
            spec = next(item for item in CLASS_BY_V[v_number]._FIELD_SPECS if item["name"] == field)
            assert spec["rule"]["minimum"] >= 1
        return
    if suffix == "V5L002.fixed-max-boundaries":
        for v_number, field in (("V11", "support_canonical_values"), ("V25", "entries"), ("V40", "author_observation_locators")):
            spec = next(item for item in CLASS_BY_V[v_number]._FIELD_SPECS if item["name"] == field)
            assert spec["rule"]["maximum"] in {3, 16, 65536}
        return
    assert suffix == "V7G001.global-stop-active-applicability-split"
    from test_post_execution_pure_owner_relations import _active_stop_snapshot
    stop, _state = _active_stop_snapshot()
    snapshot = CLASS_BY_V["V27"].from_mapping(_sample("V27", 1))
    matrix = decision.evaluate_rw0_c_decision_time_global_stop_branches(
        _sample("V32", 1), snapshot=snapshot, global_stop_snapshot=stop
    )
    assert tuple(item.result for item in matrix.entries) == ("deny", "deny", "deny", "permit", "permit")


@pytest.mark.parametrize("record_id", ASSURANCE_RECORD_IDS)
def test_each_of_126_assurances_executes_its_named_responsibility(record_id: str) -> None:
    assert len(ASSURANCE_RECORD_IDS) == 126
    record = _TEST_RECORDS[record_id]
    assert record["assurance_id"] == record_id.split(".", 1)[1].split(".", 1)[0]
    if record_id.startswith("assurance.A"):
        _execute_assurance_a(record_id)
    else:
        _execute_non_a_assurance(record_id)


def _primary_literal_current_d2_pairs(source_text: str) -> frozenset[tuple[str, str]]:
    """Project only the primary test's literal; never use it as this vector's oracle."""
    tree = ast.parse(source_text)
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "CURRENT_D2_CONSUMERS"
            for target in node.targets
        )
    )
    assert isinstance(assignment.value, ast.Dict)
    pairs: list[tuple[str, str]] = []
    targets: set[str] = set()
    for target_node, consumers_node in zip(
        assignment.value.keys, assignment.value.values, strict=True,
    ):
        target_file = ast.literal_eval(target_node)
        assert type(target_file) is str
        targets.add(Path(target_file).stem)
        assert (
            isinstance(consumers_node, ast.Call)
            and isinstance(consumers_node.func, ast.Name)
            and consumers_node.func.id == "frozenset"
            and not consumers_node.keywords
            and len(consumers_node.args) <= 1
        )
        consumers = (
            ast.literal_eval(consumers_node.args[0])
            if consumers_node.args else ()
        )
        for source_path in consumers:
            assert type(source_path) is str
            pairs.append((Path(source_path).name, f"ge_nwp_coordinator.{Path(target_file).stem}"))
    assert targets == _POST_EXECUTION_SUPPLIER_MODULES
    assert len(pairs) == len(set(pairs))
    return frozenset(pairs)


def test_v3g039_current_d2_nine_and_post_d2_five_edges_match_source_and_primary_literal() -> None:
    assert len(CURRENT_D2_EXTERNAL_IMPORT_PAIRS) == 9
    assert len(POST_D2_EXTERNAL_IMPORT_PAIRS) == 5
    assert CURRENT_D2_EXTERNAL_IMPORT_PAIRS.isdisjoint(POST_D2_EXTERNAL_IMPORT_PAIRS)
    assert len(CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS) == 14
    observed = _current_external_post_execution_import_pairs()
    assert observed == CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS
    assert not _production_caller_inventory_violates(observed)
    primary_source = (
        ROOT / "tests/test_post_execution_pure_owner_boundaries.py"
    ).read_text()
    assert _primary_literal_current_d2_pairs(primary_source) == CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS


def test_v3g039_rejects_empty_missing_substituted_and_extra_caller_edges() -> None:
    baseline = CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS
    removed = next(iter(sorted(baseline)))
    missing = baseline - {removed}
    wrong_same_count = missing | {
        ("_rw0_d2a_offline.py", "ge_nwp_coordinator._post_execution_evidence_values")
    }
    unknown_extra = baseline | {
        ("unlisted.py", "ge_nwp_coordinator._post_execution_policy_values")
    }
    state_store_extra = baseline | {_V3G039_STATE_STORE_EDGE}
    assert len(wrong_same_count) == len(baseline)
    assert len(baseline) == len(set(baseline)) == 14
    assert not _production_caller_inventory_violates(baseline)
    for hostile in (frozenset(), missing, wrong_same_count, unknown_extra, state_store_extra):
        assert hostile != baseline
        assert _production_caller_inventory_violates(hostile)


def test_v3g039_refuses_one_sided_primary_literal_drift() -> None:
    original = (ROOT / "tests/test_post_execution_pure_owner_boundaries.py").read_text()
    old = '"src/ge_nwp_coordinator/_rw0_d2a_evidence.py"'
    new = '"src/ge_nwp_coordinator/state_store.py"'
    assert old in original and new not in original
    assert _primary_literal_current_d2_pairs(original) == CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS
    changed = original.replace(old, new, 1)
    assert changed != original
    assert _primary_literal_current_d2_pairs(changed) != CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS
    assert _current_external_post_execution_import_pairs() == CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS


def test_v3g039_original_malformed_and_assurance_routes_use_current_predicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operative = _production_caller_inventory_violates
    calls: list[tuple[frozenset[tuple[str, str]], bool]] = []

    def observed_predicate(pairs: frozenset[tuple[str, str]] | set[tuple[str, str]]) -> bool:
        result = operative(pairs)
        calls.append((frozenset(pairs), result))
        return result

    monkeypatch.setitem(globals(), "_production_caller_inventory_violates", observed_predicate)
    test_each_of_93_malformed_controls_executes_its_causal_mutation(
        "malformed.V3G039.production-caller-widening"
    )
    test_each_of_126_assurances_executes_its_named_responsibility(
        "assurance.V3G039.production-caller-widening"
    )
    expected = [
        (CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS, False),
        (CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS | {_V3G039_STATE_STORE_EDGE}, True),
        (CURRENT_POST_EXECUTION_EXTERNAL_IMPORT_PAIRS, False),
    ]
    assert calls == expected * 2
