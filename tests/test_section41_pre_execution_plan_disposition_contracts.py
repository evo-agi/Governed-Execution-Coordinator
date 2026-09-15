from __future__ import annotations

import pytest

import ge_nwp_coordinator._cognitive_proposal_row_values as rows
import ge_nwp_coordinator._cognitive_proposal_semantic_values as semantic
import ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts as contracts
from ge_nwp_coordinator._cognitive_proposal_value_support import (
    _CognitiveProposalContractViolation,
)
from ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts import (
    CognitiveMutationGraphEntryV1,
    CognitiveMutationGraphV1,
    PreExecutionPlanDispositionConflictReasonV1,
    PreExecutionPlanDispositionConflictV1,
    PreExecutionPlanDispositionRecoveryClassificationV1,
    PreExecutionPlanDispositionRecoveryProbeV1,
    PreExecutionPlanDispositionRecoveryResultV1,
    PreExecutionPlanDispositionResultProjectionV1,
    PreExecutionPlanDispositionResultV1,
    PreExecutionSelectionHeadPreimageV1,
    RecordPreExecutionPlanDispositionCommandV1,
    _K8_FIELDS,
    _RECOVERY_PROBE_IDENTITY_SHAPES,
    _PreExecutionPlanDispositionWritePlan,
    _build_pre_execution_plan_disposition_recovery_probe_from_basis,
)
from test_remote_worker_pre_execution_planning_contract import (
    _build_repaired_physical_family,
)


def _exact_command_and_recovery_probe(
    readiness_present: bool = False,
) -> tuple[
    RecordPreExecutionPlanDispositionCommandV1,
    PreExecutionPlanDispositionRecoveryProbeV1,
]:
    oracle = _build_repaired_physical_family(readiness_present)
    command = RecordPreExecutionPlanDispositionCommandV1(**oracle["command"])
    context_member = next(
        member
        for member in oracle["physical_rows"]
        if member["role"] == "planning_context"
    )
    evidence_members = tuple(
        member
        for member in oracle["physical_rows"]
        if member["role"].startswith("evidence.")
    )
    probe = _build_pre_execution_plan_disposition_recovery_probe_from_basis(
        command,
        semantic.PreExecutionPlanningContextV1(**context_member["values"]),
        tuple(
            semantic.ModelProposalEvidenceBindingV1(**member["values"])
            for member in evidence_members
        ),
    )
    return command, probe


def _shared_tuple_dag(depth: int) -> tuple[object, ...]:
    node: tuple[object, ...] = ("bounded-leaf",)
    for _index in range(depth):
        node = (node, node)
    return node


@pytest.mark.parametrize("readiness_present", (False, True))
def test_contract_values_match_both_repaired_section41_golden_families(
    readiness_present: bool,
) -> None:
    oracle = _build_repaired_physical_family(readiness_present)
    command = RecordPreExecutionPlanDispositionCommandV1(**oracle["command"])
    physical = tuple(
        rows.CanonicalCognitivePhysicalRow(
            table=member["table"],
            role=member["role"],
            rank=member["rank"],
            ordinal=member["ordinal"],
            values=rows._row_value_from_mapping(member["table"], member["values"]),
        )
        for member in oracle["physical_rows"]
    )
    graph = CognitiveMutationGraphV1(
        mutation_ref=oracle["graph"]["mutation_ref"],
        command_digest=oracle["graph"]["command_digest"],
        entries=tuple(
            CognitiveMutationGraphEntryV1(**entry)
            for entry in oracle["graph"]["entries"]
        ),
        mutation_graph_digest=oracle["graph"]["mutation_graph_digest"],
    )
    projection = PreExecutionPlanDispositionResultProjectionV1(
        **oracle["result_projection"]
    )
    result = PreExecutionPlanDispositionResultV1(
        projection=projection,
        receipt_digest=oracle["fresh_result"]["receipt_digest"],
    )
    selection_key = tuple(
        (name, object.__getattribute__(command, name)) for name in _K8_FIELDS
    )
    preimage = PreExecutionSelectionHeadPreimageV1(
        selection_key=selection_key,
        expected_current_selection_revision=command.expected_current_selection_revision,
        expected_current_selection_head_digest=(
            command.expected_current_selection_head_digest
        ),
        supersedes_disposition_ref=command.supersedes_disposition_ref,
    )
    context_member = next(
        member for member in oracle["physical_rows"] if member["role"] == "planning_context"
    )
    evidence_members = tuple(
        member
        for member in oracle["physical_rows"]
        if member["role"].startswith("evidence.")
    )
    probe = _build_pre_execution_plan_disposition_recovery_probe_from_basis(
        command,
        semantic.PreExecutionPlanningContextV1(**context_member["values"]),
        tuple(
            semantic.ModelProposalEvidenceBindingV1(**member["values"])
            for member in evidence_members
        ),
    )
    plan = _PreExecutionPlanDispositionWritePlan(
        command=command,
        rows=physical,
        graph=graph,
        planned_result=result,
        recovery_probe=probe,
    )
    assert plan.command.to_mapping() == oracle["command"]
    assert plan.graph.to_mapping() == oracle["graph"]
    assert plan.planned_result.to_mapping() == oracle["fresh_result"]
    assert plan.command is not command
    assert plan.graph is not graph
    assert plan.planned_result is not result
    assert plan.recovery_probe is not probe
    assert all(retained is not supplied for retained, supplied in zip(plan.rows, physical))
    assert all(
        retained.values is not supplied.values
        for retained, supplied in zip(plan.rows, physical)
    )
    assert len(plan.rows) == (23 if readiness_present else 22)
    assert len(plan.recovery_probe.identity_locators) == 30
    assert len(plan.recovery_probe.evidence_member_locators) == (
        15 if readiness_present else 14
    )
    assert tuple(
        (table, tuple(name for name, _value in locator))
        for table, locator in plan.recovery_probe.identity_locators
    ) == _RECOVERY_PROBE_IDENTITY_SHAPES


def test_post_mutated_exact_command_reconstruction_uses_finite_reason() -> None:
    command, _probe = _exact_command_and_recovery_probe()
    object.__setattr__(command, "mutation_ref", "mutation-ref-post-mutated")

    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        contracts._reconstruct_exact_contract_value(
            command,
            RecordPreExecutionPlanDispositionCommandV1,
        )
    assert type(caught.value) is _CognitiveProposalContractViolation
    assert caught.value.reason == "cognitive_mutation_identity_invalid"
    assert caught.value.args == ("cognitive_mutation_identity_invalid",)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_post_mutated_exact_recovery_probe_reconstruction_uses_finite_reason() -> None:
    _command, probe = _exact_command_and_recovery_probe()
    replacement = "f" * 64 if probe.recovery_probe_digest != "f" * 64 else "e" * 64
    object.__setattr__(probe, "recovery_probe_digest", replacement)

    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        contracts._require_exact_recovery_probe(probe)
    assert type(caught.value) is _CognitiveProposalContractViolation
    assert caught.value.reason == "recovery_unresolved"
    assert caught.value.args == ("recovery_unresolved",)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_inconsistent_evidence_set_reconstruction_uses_finite_reason() -> None:
    command, probe = _exact_command_and_recovery_probe()
    fields = command.to_mapping()
    fields["evidence_set_digest"] = (
        "f" * 64 if fields["evidence_set_digest"] != "f" * 64 else "e" * 64
    )
    fields["mutation_command_digest"] = contracts._domain_separated_digest(
        contracts._COMMAND_DOMAIN,
        contracts._without_field(fields, "mutation_command_digest"),
    )
    inconsistent_command = RecordPreExecutionPlanDispositionCommandV1(**fields)
    object.__setattr__(probe, "command", inconsistent_command)

    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        contracts._require_exact_recovery_probe(probe)
    assert type(caught.value) is _CognitiveProposalContractViolation
    assert caught.value.reason == "recovery_unresolved"
    assert caught.value.args == ("recovery_unresolved",)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "exception_type",
    (KeyboardInterrupt, SystemExit, GeneratorExit),
    ids=("keyboard-interrupt", "system-exit", "generator-exit"),
)
@pytest.mark.parametrize(
    "handler_boundary",
    ("contract-constructor", "evidence-set-validation"),
)
def test_genuine_process_control_identity_is_preserved_at_both_contract_handlers(
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
    handler_boundary: str,
) -> None:
    command, probe = _exact_command_and_recovery_probe()
    sentinel = exception_type()

    def raise_process_control(*args: object, **kwargs: object) -> None:
        raise sentinel

    if handler_boundary == "contract-constructor":
        monkeypatch.setattr(
            contracts,
            "_domain_separated_digest",
            raise_process_control,
        )

        def invoke() -> object:
            return contracts._reconstruct_exact_contract_value(
                command,
                RecordPreExecutionPlanDispositionCommandV1,
            )

    else:
        fields = {
            name: object.__getattribute__(probe, name)
            for name in probe._FIELD_ORDER
        }
        monkeypatch.setattr(
            semantic,
            "ModelProposalEvidenceSetV1",
            raise_process_control,
        )

        def invoke() -> object:
            return PreExecutionPlanDispositionRecoveryProbeV1(**fields)

    with pytest.raises(exception_type) as caught:
        invoke()
    assert caught.value is sentinel
    assert type(caught.value) is exception_type


def test_conflict_and_recovery_algebras_are_closed() -> None:
    conflict = PreExecutionPlanDispositionConflictV1(
        reason=PreExecutionPlanDispositionConflictReasonV1.PLANNING_RELATION_CONFLICT,
        mutation_ref="mutation-ref",
        command_digest="1" * 64,
        program_ref="program-ref",
    )
    assert conflict.to_mapping()["reason"] == "planning_relation_conflict"
    unresolved = PreExecutionPlanDispositionRecoveryResultV1(
        classification=PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED,
        observed_depth=257,
        committed_result=None,
    )
    assert unresolved.observed_depth == 257
    with pytest.raises(_CognitiveProposalContractViolation):
        PreExecutionPlanDispositionRecoveryResultV1(
            classification=(
                PreExecutionPlanDispositionRecoveryClassificationV1.DEFINITELY_NOT_COMMITTED
            ),
            observed_depth=1,
            committed_result=None,
        )


def test_recovery_probe_rejects_hostile_selection_key_before_equality() -> None:
    oracle = _build_repaired_physical_family(False)
    command = RecordPreExecutionPlanDispositionCommandV1(**oracle["command"])

    class EqualityBomb:
        def __eq__(self, other: object) -> bool:
            raise AssertionError("hostile equality executed")

    selection_key = tuple(EqualityBomb() for _ in _K8_FIELDS)
    preimage_key = tuple(
        (name, object.__getattribute__(command, name)) for name in _K8_FIELDS
    )
    preimage = PreExecutionSelectionHeadPreimageV1(
        selection_key=preimage_key,
        expected_current_selection_revision=None,
        expected_current_selection_head_digest=None,
        supersedes_disposition_ref=None,
    )
    physical = _build_repaired_physical_family(False)["physical_rows"]
    context_member = next(
        member for member in physical if member["role"] == "planning_context"
    )
    evidence_members = tuple(
        member for member in physical if member["role"].startswith("evidence.")
    )
    exact_probe = _build_pre_execution_plan_disposition_recovery_probe_from_basis(
        command,
        semantic.PreExecutionPlanningContextV1(**context_member["values"]),
        tuple(
            semantic.ModelProposalEvidenceBindingV1(**member["values"])
            for member in evidence_members
        ),
    )
    with pytest.raises(_CognitiveProposalContractViolation):
        PreExecutionPlanDispositionRecoveryProbeV1(
            command=command,
            planning_context=exact_probe.planning_context,
            evidence_bindings=exact_probe.evidence_bindings,
            selection_key=selection_key,  # type: ignore[arg-type]
            expected_preimage=preimage,
            identity_locators=exact_probe.identity_locators,
            evidence_member_locators=exact_probe.evidence_member_locators,
            recovery_probe_digest=exact_probe.recovery_probe_digest,
        )


def test_contract_normalization_does_not_probe_hostile_attributes() -> None:
    class AttributeBomb:
        def __getattr__(self, name: str) -> object:
            raise AssertionError("hostile attribute lookup executed")

    with pytest.raises(_CognitiveProposalContractViolation):
        CognitiveMutationGraphEntryV1(
            role=AttributeBomb(),
            rank=0,
            ordinal=0,
            table=rows._TABLE_ORDER[0],
            locator=(("source_invocation_ref", "source-ref"),),
            member_digest="0" * 64,
        )


@pytest.mark.parametrize(
    "value_type",
    (RecordPreExecutionPlanDispositionCommandV1, PreExecutionPlanDispositionRecoveryProbeV1),
)
def test_concrete_contract_class_name_and_module_spoofs_are_rejected(
    value_type: type[object],
) -> None:
    with pytest.raises(TypeError):
        type(
            value_type.__name__,
            (value_type,),
            {"__module__": value_type.__module__},
        )


def _hostile_contract_spoof(
    trusted_type: type[object],
    process_control: BaseException | None = None,
) -> tuple[object, dict[str, int]]:
    callbacks = {"hash": 0, "equality": 0, "conversion": 0}

    class CollisionMeta(type):
        def __hash__(cls) -> int:
            callbacks["hash"] += 1
            if process_control is not None:
                raise process_control
            return type.__hash__(trusted_type)

        def __eq__(cls, other: object) -> bool:
            callbacks["equality"] += 1
            if process_control is not None:
                raise process_control
            return other is trusted_type

    def to_mapping(self: object) -> dict[str, object]:
        callbacks["conversion"] += 1
        if process_control is not None:
            raise process_control
        raise AssertionError("hostile conversion executed")

    spoof_type = CollisionMeta(
        trusted_type.__name__,
        (),
        {"__module__": trusted_type.__module__, "to_mapping": to_mapping},
    )
    callbacks.update(hash=0, equality=0, conversion=0)
    return spoof_type(), callbacks


@pytest.mark.parametrize(
    "trusted_type",
    (
        RecordPreExecutionPlanDispositionCommandV1,
        PreExecutionPlanDispositionRecoveryProbeV1,
    ),
)
def test_contract_registry_rejects_equal_hash_spoofs_by_identity_without_callbacks(
    trusted_type: type[object],
) -> None:
    spoof, callbacks = _hostile_contract_spoof(trusted_type)
    with pytest.raises(_CognitiveProposalContractViolation):
        contracts._clone_exact_contract_member(spoof, set(), 0)
    with pytest.raises(_CognitiveProposalContractViolation):
        contracts._reconstruct_exact_contract_value(spoof, trusted_type)
    assert callbacks == {"hash": 0, "equality": 0, "conversion": 0}


def test_recovery_probe_reconstruction_rejects_nested_semantic_metaclass_spoof_without_callbacks() -> None:
    oracle = _build_repaired_physical_family(False)
    command = RecordPreExecutionPlanDispositionCommandV1(**oracle["command"])
    context_member = next(
        member
        for member in oracle["physical_rows"]
        if member["role"] == "planning_context"
    )
    evidence_members = tuple(
        member
        for member in oracle["physical_rows"]
        if member["role"].startswith("evidence.")
    )
    probe = _build_pre_execution_plan_disposition_recovery_probe_from_basis(
        command,
        semantic.PreExecutionPlanningContextV1(**context_member["values"]),
        tuple(
            semantic.ModelProposalEvidenceBindingV1(**member["values"])
            for member in evidence_members
        ),
    )
    sentinel = GeneratorExit("hostile-process-control-sentinel")
    spoof, callbacks = _hostile_contract_spoof(
        semantic.PreExecutionPlanningContextV1,
        sentinel,
    )
    object.__setattr__(probe, "planning_context", spoof)

    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        contracts._require_exact_recovery_probe(probe)
    assert caught.value.reason == "recovery_unresolved"
    assert callbacks == {"hash": 0, "equality": 0, "conversion": 0}
    assert sentinel not in caught.value.args


def test_contract_reconstruction_shared_dag_exhausts_one_cross_layer_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _command, probe = _exact_command_and_recovery_probe(True)
    shared = _shared_tuple_dag(10)
    object.__setattr__(
        probe,
        "identity_locators",
        tuple((shared, shared) for _index in range(30)),
    )
    monkeypatch.setattr(
        contracts,
        "_MAX_EXACT_CONTRACT_RECONSTRUCTION_WORK",
        5_000,
        raising=False,
    )
    constructed: list[object] = []
    original_init = semantic._SemanticReconstructionBudget.__init__

    def record_budget(self: object, *args: object, **kwargs: object) -> None:
        constructed.append(self)
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(
        semantic._SemanticReconstructionBudget,
        "__init__",
        record_budget,
    )
    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        contracts._require_exact_recovery_probe(probe)
    assert caught.value.reason == "recovery_unresolved"
    assert len(constructed) == 1
    assert constructed[0].consumed == 5_000
    assert constructed[0].remaining == 0


def test_maximum_valid_recovery_probe_remains_accepted_under_cross_layer_budget() -> None:
    _command, probe = _exact_command_and_recovery_probe(True)
    reconstructed = contracts._require_exact_recovery_probe(probe)
    assert reconstructed.to_mapping() == probe.to_mapping()
    assert reconstructed is not probe
