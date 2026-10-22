"""Exact transient command bindings for the selected D2 checking effects."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from ge_nwp_coordinator._development_bound_effect_establishment_contracts import (
    DevelopmentBoundEffectAuthorizationSafeBindingV1,
    DevelopmentBoundEffectEstablishmentCommandV1,
    DevelopmentBoundEffectEstablishmentResultV1,
    _BOUND_BINDING_SCHEMA, _COMMAND_SCHEMA, _RECEIPT_RESULT_SCHEMA, _RESULT_SCHEMA,
    _development_bound_effect_establishment_write_plan,
    _development_bound_effect_authorization_safe_binding,
    _reduce_development_bound_effect_establishment_command,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from test_rw0_d1_offline_integration import work_spec


def _bound_command(handback: object, work: object, effect_class: str) -> object:
    author = handback.author_command
    suffix = effect_class.replace("_", "-")
    binding = _development_bound_effect_authorization_safe_binding(
        parent_standing_grant_ref=author.attempt_fence.parent_standing_grant_ref,
        parent_standing_grant_digest=author.attempt_fence.parent_standing_grant_digest,
        effect_authorization_ref="effect-authorization.d2." + suffix,
        effect_authorization_digest="8" * 64,
        attempt_fence_ref=author.attempt_fence_ref,
        attempt_fence_digest=author.attempt_fence.attempt_fence_digest,
        semantic_attempt_ref=author.semantic_attempt_ref,
        effect_intent_ref="effect-intent.d2." + suffix,
        effect_class=effect_class,
        path_ceiling=author.attempt_fence.path_ceiling,
        effect_ceilings=author.effect_authorization_safe_binding.effect_ceilings,
        expires_at=author.effect_authorization_safe_binding.expires_at,
        global_stop_ref=author.coding_global_stop_ref,
        global_stop_version=author.coding_global_stop_version,
    )
    return _reduce_development_bound_effect_establishment_command(
        mutation_ref="mutation.d2." + suffix,
        effect_class=effect_class,
        effect_intent_ref="effect-intent.d2." + suffix,
        effect_fence_ref="effect-fence.d2." + suffix,
        authority_evaluation_ref="authority-evaluation.d2." + suffix,
        delivery_attempt_ref="delivery-attempt.d2." + suffix,
        adapter_safe_correlation_ref="adapter-correlation.d2." + suffix,
        author_command=author,
        selected_disposition=handback.section41_result,
        phase_basis=handback.phase_basis,
        work_spec=work,
        capture=handback.capture,
        capsule_manifest=handback.capsule_manifest,
        requirement_evidence=(author.validation_requirement_evidence
                              if effect_class == "validate_candidate"
                              else author.review_requirement_evidence),
        effect_authorization_safe_binding=binding,
    )


@pytest.mark.parametrize("effect_class", ("validate_candidate", "review_candidate"))
def test_native_command_retains_real_bytes_and_uses_distinct_result_identity(effect_class: str) -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        command = _bound_command(run.handback, work, effect_class)
        assert type(command) is DevelopmentBoundEffectEstablishmentCommandV1
        assert type(command.effect_authorization_safe_binding) is DevelopmentBoundEffectAuthorizationSafeBindingV1
        assert command.effect_authorization_safe_binding.schema_id == _BOUND_BINDING_SCHEMA
        assert command.schema_id == _COMMAND_SCHEMA
        assert command.computed_digest() == command.command_digest
        assert command.effect_fence.effect_class == effect_class
        assert command.delivery_envelope.effect_fence_ref == command.effect_fence_ref
        assert tuple(path for path, _ in command.before_blob_entries) == tuple(
            entry.path for entry in run.handback.capsule_manifest.entries
        )
        assert tuple(field.name for field in fields(command))[-8:] == (
            "effect_authorization_safe_binding", "capsule_manifest",
            "requirement_evidence", "before_blob_entries", "after_blob_entries",
            "effect_fence", "delivery_envelope", "command_digest",
        )
        assert _RESULT_SCHEMA != _RECEIPT_RESULT_SCHEMA
        plan = _development_bound_effect_establishment_write_plan(
            command, "2026-10-18T00:00:00Z"
        )
        assert len(plan.graph_entries) == 6
        assert plan.effect_intent.effect_class == effect_class
        assert plan.authority_evaluation.authority_digest == (
            command.effect_authorization_safe_binding.effect_authorization_digest
        )
        assert plan.mutation_receipt.result_projection_digest != plan.planned_result.computed_digest()
        result = DevelopmentBoundEffectEstablishmentResultV1(
            "committed", command.mutation_ref, command.command_digest,
            command.program_ref, command.basis_decision_ref,
            command.program_version_ref, command.semantic_attempt_ref,
            command.candidate_ref, command.effect_class, command.effect_intent_ref,
            command.effect_fence_ref, command.delivery_attempt_ref,
            "2026-10-18T00:00:00Z",
        )
        assert len(result.computed_digest()) == 64
        assert "D1OfflineRun" not in repr(command)
        after = list(command.after_blob_entries)
        after[2] = (after[2][0], after[2][1] + b"forged")
        with pytest.raises(ValueError, match="^invalid_development_bound_effect_command$"):
            replace(command, after_blob_entries=tuple(after))
