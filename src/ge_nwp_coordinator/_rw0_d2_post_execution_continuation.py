"""Parent-owned artificial D2 to Section 41/C1 post proposal continuation."""

from __future__ import annotations

from dataclasses import dataclass, replace
import typing

from ._cognitive_proposal_semantic_values import PreExecutionModelProposalV1
from ._post_execution_evidence_values import (
    _domain_separated_digest,
)
from ._rw0_c1_mutation_contracts import section41_owner_family_graph_digest
from ._rw0_c1_semantic_values import (
    RW0C1AdmitEvidenceCommandV1, RW0C1AdmitEvidenceResultV1,
    RW0C1ConflictV1, RW0C1OwnerRowLocatorV1,
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
    evidence_admission_recovery_selector,
)
from ._rw0_d2_handback import RW0D2OfflineRun
from ._rw0_d2_offline import run_rw0_d2_offline
from ._rw0_d1_offline import D1ArtificialFixture
from ._rw0_d2a_evidence import _resolve_d2_checked_layout, _seal_post_value
from ._section41_post_execution_proposal_family_projection import (
    Section41PostExecutionProjectionEvidenceEntryV2,
    Section41PostExecutionProposalFamilyProjectionV2,
    section41_post_execution_proposal_family_projection,
)
from ._section41_post_execution_proposal_mutation_contracts import (
    PostExecutionProposalConflictV1,
    RecordPostExecutionProposalCommandV1, RecordPostExecutionProposalResultV1,
    prepare_record_command,
)
from ._sqlite_section41_post_execution_proposal import (
    CheckedPostExecutionProposalFamilyV1,
)
from ._worker_execution_semantic_values import WorkSpecV1
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_writer_session import acquire_sqlite_writer_session

__all__: tuple[str, ...] = ()

_ROLE_ORDER = (
    "candidate_capsule", "worker_result", "validation_result",
    "independent_review", "standing_policy", "risk_lane",
    "authority_currentness_attestation", "global_stop", "effect_ceiling",
)


def _owner_locators(
    checked: CheckedPostExecutionProposalFamilyV1,
) -> tuple[RW0C1OwnerRowLocatorV1, ...]:
    rows = (checked.source, checked.artifact, checked.proposal, *checked.evidence)
    specifications = (
        ("source_invocation", "development_model_source_invocation",
         "source_invocation_ref", "source_invocation_digest"),
        ("artifact_binding", "development_private_proposal_artifact_binding",
         "artifact_ref", "artifact_binding_digest"),
        ("model_proposal", "development_model_proposal",
         "proposal_ref", "proposal_digest"),
        *((role, "development_model_proposal_evidence_binding",
           "proposal_ref", "evidence_binding_digest") for role in _ROLE_ORDER),
    )
    return tuple(
        RW0C1OwnerRowLocatorV1(
            role=role, owner_role=owner_role,
            row_ref=getattr(row, ref_field),
            row_digest=getattr(row, digest_field),
            subrole=(role if index >= 3 else None),
            ordinal=(0 if index >= 3 else None),
        )
        for index, (row, (role, owner_role, ref_field, digest_field)) in enumerate(
            zip(rows, specifications, strict=True)
        )
    )


def _rank15_command(
    checked: CheckedPostExecutionProposalFamilyV1,
    phase: object,
) -> RW0C1AdmitEvidenceCommandV1:
    source, artifact, proposal = checked.source, checked.artifact, checked.proposal
    locators = _owner_locators(checked)
    value_ref = "section41-post-family." + checked.command.proposal_digest[:32]
    value = RW0C1Section41PostExecutionProposalFamilyMemberV1(
        value_ref=value_ref,
        phase_basis_ref=checked.command.phase_basis_ref,
        phase_basis_digest=checked.command.phase_basis_digest,
        source_invocation_ref=source.source_invocation_ref,
        source_invocation_digest=source.source_invocation_digest,
        artifact_ref=artifact.artifact_ref,
        artifact_digest=artifact.artifact_digest,
        artifact_binding_digest=artifact.artifact_binding_digest,
        proposal_ref=proposal.proposal_ref,
        proposal_digest=proposal.proposal_digest,
        model_contract_ref=source.model_contract_ref,
        model_contract_digest=source.model_contract_digest,
        model_configuration_ref=source.model_configuration_ref,
        model_configuration_digest=source.model_configuration_digest,
        context_schema_id=checked.input_context.schema_id,
        context_ref=checked.input_context.input_context_ref,
        context_digest=checked.input_context.input_context_digest,
        safe_projection_schema_id=artifact.safe_projection_schema_id,
        safe_projection_digest=artifact.safe_projection_digest,
        evidence_set_ref=proposal.evidence_set_ref,
        evidence_set_digest=proposal.evidence_set_digest,
        evidence_binding_count=9,
        recommendation=proposal.recommendation,
        reason_code=proposal.reason_code,
        proposal_created_at=proposal.proposal_created_at,
        owner_family_graph_digest=section41_owner_family_graph_digest(locators),
    )
    return RW0C1AdmitEvidenceCommandV1(
        mutation_ref=checked.receipt.c1_mutation_ref,
        phase_basis_ref=checked.command.phase_basis_ref,
        phase_basis_digest=checked.command.phase_basis_digest,
        expected_program_head_revision=phase.value("expected_program_head_revision"),
        expected_program_head_digest=phase.value("expected_program_head_digest"),
        expected_work_item_head_revision=phase.value("expected_work_item_head_revision"),
        expected_work_item_head_digest=phase.value("expected_work_item_head_digest"),
        preassigned_membership_ref=checked.receipt.c1_membership_ref,
        kind_rank=15, evidence_value=value,
        owner_row_locators=locators,
    )


def _admission_graph(family: object) -> dict[str, object]:
    member = family.membership
    relations = tuple(item.binding for item in family.relations.relations)
    return {
        "schema_id": "governed-execution.nwp-rw0-c1-evidence-admission-graph.v1",
        "phase_basis_ref": member.value("phase_basis_ref"),
        "phase_basis_digest": member.value("phase_basis_digest"),
        "membership_ref": member.value("membership_ref"),
        "kind_rank": member.value("kind_rank"),
        "value_ref": member.value("value_ref"),
        "value_digest": member.value("value_digest"),
        "value_schema_id": member.value("value_schema_id"),
        "scope_binding_digest": member.value("scope_binding_digest"),
        "relation_set_digest": member.value("relation_set_digest"),
        "relations": [{
            name: relation.value(name)
            for name in (
                "relation_ref", "relation_digest", "relation_rank",
                "operand_set_digest", "evaluated_at",
            )
        } for relation in relations],
        "admitted_by_mutation_ref": member.value("admitted_by_mutation_ref"),
        "admitted_at": member.value("admitted_at"),
    }


def _project(
    checked: CheckedPostExecutionProposalFamilyV1,
    c1_family: object,
) -> Section41PostExecutionProposalFamilyProjectionV2:
    source, artifact, proposal = checked.source, checked.artifact, checked.proposal
    context = checked.input_context
    locators = _owner_locators(checked)
    entries = []
    for row in checked.evidence:
        cls = Section41PostExecutionProjectionEvidenceEntryV2
        entry_identity = {
            "schema_id": cls._SCHEMA_ID,
            "proposal_ref": row.proposal_ref,
            "proposal_phase": row.proposal_phase,
            "evidence_set_ref": row.evidence_set_ref,
            "evidence_role": row.evidence_role,
            "role_rank": row.role_rank,
            "ordinal": row.ordinal,
            "evidence_ref": row.evidence_ref,
            "evidence_digest": row.evidence_digest,
            "required_for_selection": row.required_for_selection,
            "evidence_bound_at": row.evidence_bound_at,
            "source_binding_schema_id": row.schema_id,
            "source_binding_digest": row.evidence_binding_digest,
        }
        entries.append(cls.from_mapping({
            **entry_identity,
            "projection_evidence_entry_digest": _domain_separated_digest(
                cls._DIGEST["domain"], entry_identity,
            ),
        }))
    cls = Section41PostExecutionProposalFamilyProjectionV2
    expected = _seal_post_value(cls, {
        "schema_id": cls._SCHEMA_ID,
        "profile_ref": cls._PROFILE_PAIR[0],
        "profile_digest": cls._PROFILE_PAIR[1],
        "proposal_phase": source.proposal_phase,
        "source_invocation_ref": source.source_invocation_ref,
        "source_invocation_digest": source.source_invocation_digest,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "artifact_binding_digest": artifact.artifact_binding_digest,
        "proposal_ref": proposal.proposal_ref,
        "proposal_digest": proposal.proposal_digest,
        "model_contract_ref": source.model_contract_ref,
        "model_contract_digest": source.model_contract_digest,
        "model_configuration_ref": source.model_configuration_ref,
        "model_configuration_digest": source.model_configuration_digest,
        "input_context_schema_id": context.schema_id,
        "input_context_ref": context.input_context_ref,
        "input_context_digest": context.input_context_digest,
        "lineage_context_schema_id": context.lineage_context_schema_id,
        "lineage_context_ref": context.lineage_context_ref,
        "lineage_context_digest": context.lineage_context_digest,
        "safe_projection_schema_id": artifact.safe_projection_schema_id,
        "safe_projection_digest": artifact.safe_projection_digest,
        "evidence_set_ref": proposal.evidence_set_ref,
        "evidence_set_digest": proposal.evidence_set_digest,
        "evidence_binding_count": 9,
        "evidence_bindings": [item.to_mapping() for item in entries],
        "owner_family_graph_digest": section41_owner_family_graph_digest(locators),
        "recommendation": proposal.recommendation,
        "reason_code": proposal.reason_code,
        "source_invocation_started_at": source.source_invocation_started_at,
        "source_invocation_completed_at": source.source_invocation_completed_at,
        "artifact_validated_at": artifact.artifact_validated_at,
        "evidence_bound_at": checked.evidence[0].evidence_bound_at,
        "proposal_created_at": proposal.proposal_created_at,
        "projection_evaluated_at": proposal.proposal_created_at,
    })
    return section41_post_execution_proposal_family_projection(
        expected, input_context=context,
        source_invocation_row=source,
        artifact_binding_row=artifact,
        proposal_row=proposal,
        evidence_rows=checked.evidence,
        private_reader_tuples=checked.private_reader_tuples,
        owner_locators=locators,
        rank15_value=c1_family.evidence_value,
        rank15_relation_row=c1_family.relations.relations[0].binding,
        rank15_admission_graph=_admission_graph(c1_family),
        rank15_membership_row=c1_family.membership,
        admitted_by_mutation_ref=c1_family.admission_result.mutation_ref,
    )


@dataclass(frozen=True, slots=True, repr=False)
class PostD2ContinuationResultV1:
    status: str
    reason: str
    proposal_result: RecordPostExecutionProposalResultV1 | None = None
    admission_result: RW0C1AdmitEvidenceResultV1 | None = None
    projection: Section41PostExecutionProposalFamilyProjectionV2 | None = None
    cleanup_complete: bool | None = None

    def __post_init__(self) -> None:
        if (type(self.status) is not str
                or self.status not in {
                    "stopped", "proposal_not_recorded", "proposal_uncertain",
                    "proposal_recorded_verification_failed",
                    "proposal_recorded_not_admitted", "admission_uncertain",
                    "admitted_verification_failed", "projected",
                    "cleanup_unresolved",
                }
                or type(self.reason) is not str or not self.reason
                or (self.cleanup_complete is not None
                    and type(self.cleanup_complete) is not bool)
                or (self.status == "cleanup_unresolved")
                != (self.cleanup_complete is False)
                or (self.proposal_result is not None
                    and type(self.proposal_result) is not RecordPostExecutionProposalResultV1)
                or (self.admission_result is not None
                    and type(self.admission_result) is not RW0C1AdmitEvidenceResultV1)
                or (self.projection is not None
                    and type(self.projection) is not Section41PostExecutionProposalFamilyProjectionV2)
                or (self.status == "projected") != (self.projection is not None)
                or (self.status == "projected"
                    and (self.proposal_result is None or self.admission_result is None))):
            raise ValueError("invalid_post_d2_continuation_result") from None


def continue_open_rw0_d2_run(run: RW0D2OfflineRun) -> PostD2ContinuationResultV1:
    """Borrow one original open D2 run; the caller retains disposal ownership."""
    if type(run) is not RW0D2OfflineRun:
        raise ValueError("invalid_post_execution_run")
    run._require_open_owner()
    if run.handback.status != "preadmission_ready":
        return PostD2ContinuationResultV1("stopped", run.handback.reason)
    command, encoded = prepare_record_command(run)
    location = run._d1_run.location
    a_result = None
    try:
        with acquire_sqlite_writer_session(location) as writer:
            a_result = writer._record_post_execution_proposal(command, run, encoded)
    except SQLiteMutationStoreError as error:
        if error.error_class != SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value:
            return PostD2ContinuationResultV1("stopped", "proposal_record_failed")
        try:
            with acquire_sqlite_writer_session(location) as writer:
                recovery = writer._recover_post_execution_proposal(command)
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            return PostD2ContinuationResultV1("proposal_uncertain", "recovery_unavailable")
        if recovery.classification == "definitely_not_committed":
            return PostD2ContinuationResultV1(
                "proposal_not_recorded", "definitely_not_committed",
            )
        if recovery.classification != "committed_exact":
            return PostD2ContinuationResultV1("proposal_uncertain", recovery.classification)
        a_result = recovery.result
    if type(a_result) is PostExecutionProposalConflictV1:
        return PostD2ContinuationResultV1("stopped", a_result.reason)
    if type(a_result) is not RecordPostExecutionProposalResultV1:
        return PostD2ContinuationResultV1("proposal_uncertain", "unknown_result")
    try:
        with acquire_sqlite_writer_session(location) as writer:
            checked = writer._read_post_execution_proposal(command)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return PostD2ContinuationResultV1(
            "proposal_recorded_verification_failed", "section41_readback",
            proposal_result=a_result,
        )
    if type(checked) is not CheckedPostExecutionProposalFamilyV1:
        return PostD2ContinuationResultV1(
            "proposal_recorded_verification_failed", "section41_readback",
            proposal_result=a_result,
        )
    try:
        phase = _resolve_d2_checked_layout(run.handback.d1_handback).family(
            run.handback.checked_admissions, "worker_observation:000",
        ).phase
        b_command = _rank15_command(checked, phase)
        b_selector = evidence_admission_recovery_selector(b_command)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return PostD2ContinuationResultV1(
            "proposal_recorded_verification_failed", "rank15_command",
            proposal_result=a_result,
        )
    try:
        with acquire_sqlite_writer_session(location) as writer:
            b_result = writer._admit_rw0_evidence(b_command)
    except SQLiteMutationStoreError as error:
        if error.error_class != SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value:
            return PostD2ContinuationResultV1(
                "proposal_recorded_not_admitted", "c1_admission_failed",
                proposal_result=a_result,
            )
        try:
            with acquire_sqlite_writer_session(location) as writer:
                recovery = writer._resolve_rw0_c1_evidence_admission_commit_outcome(
                    b_selector
                )
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            return PostD2ContinuationResultV1(
                "admission_uncertain", "recovery_unavailable",
                proposal_result=a_result,
            )
        if recovery.disposition.value == "definitely_not_committed":
            return PostD2ContinuationResultV1(
                "proposal_recorded_not_admitted", "definitely_not_committed",
                proposal_result=a_result,
            )
        if recovery.disposition.value != "committed_exact":
            return PostD2ContinuationResultV1(
                "admission_uncertain", recovery.disposition.value,
                proposal_result=a_result,
            )
        try:
            with acquire_sqlite_writer_session(location) as writer:
                # Recovery is followed by checked historical readback. A
                # second admission call would duplicate B after lost return.
                b_result = writer._read_rw0_c1_checked_family(
                    b_selector
                ).admission_result
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            return PostD2ContinuationResultV1(
                "admitted_verification_failed", "c1_recovery_readback",
                proposal_result=a_result,
            )
    if type(b_result) is RW0C1ConflictV1:
        return PostD2ContinuationResultV1(
            "proposal_recorded_not_admitted", b_result.reason.value,
            proposal_result=a_result,
        )
    if type(b_result) is not RW0C1AdmitEvidenceResultV1:
        return PostD2ContinuationResultV1(
            "admission_uncertain", "unknown_result", proposal_result=a_result,
        )
    try:
        with acquire_sqlite_writer_session(location) as writer:
            final_a = writer._read_post_execution_proposal(command)
        with acquire_sqlite_writer_session(location) as writer:
            final_b = writer._read_rw0_c1_checked_family(b_result)
        if final_a != checked:
            raise ValueError("section41_changed")
        projected = _project(final_a, final_b)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return PostD2ContinuationResultV1(
            "admitted_verification_failed", "final_readback_or_projection",
            proposal_result=a_result, admission_result=b_result,
        )
    return PostD2ContinuationResultV1(
        "projected", "complete", a_result, b_result, projected,
    )


def run_rw0_d2_post_execution_continuation(
    work_spec: WorkSpecV1, fixture: D1ArtificialFixture,
) -> PostD2ContinuationResultV1:
    """Run D2 exactly once, then own its creator-process disposal in finally."""
    run = run_rw0_d2_offline(work_spec, fixture)
    result: PostD2ContinuationResultV1 | None = None
    primary: BaseException | None = None
    try:
        result = continue_open_rw0_d2_run(run)
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            run.close()
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception as cleanup_error:
            if primary is not None:
                primary.add_note("d2_run_cleanup_unresolved")
                raise primary from cleanup_error
            result = PostD2ContinuationResultV1(
                "cleanup_unresolved", "d2_run_cleanup_unresolved",
                proposal_result=(result.proposal_result if result else None),
                admission_result=(result.admission_result if result else None),
                cleanup_complete=False,
            )
        else:
            if result is not None:
                result = replace(result, cleanup_complete=True)
    if result is None:
        raise RuntimeError("post_d2_continuation_result_missing")
    return result
