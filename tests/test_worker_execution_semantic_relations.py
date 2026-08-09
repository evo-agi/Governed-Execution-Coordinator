from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

import ge_nwp_coordinator._worker_execution_semantic_values as semantic_values
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    CeilingsV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
    WorkerExecutionValueError,
    WorkerObservationV1,
    WorkSpecV1,
    create_author_command_and_effect_fence,
    create_effect_fence,
    validate_authoring_relation,
    validate_capsule_manifest_relation,
    validate_delivery_relation,
    validate_effect_relation,
    validate_observation_relation,
    validate_redelivery_relation,
)
from tests.c2a_contract_support import (
    AUTHORIZED_PATHS,
    BLOB_FIXTURES,
    _delivery_for_vector,
    _effect_fence_for_vector,
    _full_record,
    _observation_for_kind,
    _observation_for_vector,
    _reseal_observation,
    _reseal_single_digest_record,
    _valid_redelivery_candidate,
)


def _before_blobs() -> dict[str, bytes]:
    return {path: BLOB_FIXTURES[path]["before"] for path in AUTHORIZED_PATHS}


def _after_blobs() -> dict[str, bytes]:
    return {path: BLOB_FIXTURES[path]["after"] for path in AUTHORIZED_PATHS}


def _common_graph() -> tuple[
    WorkSpecV1,
    AttemptFenceV1,
    WorkerCommandV1,
    EffectFenceV1,
    CandidateCapsuleManifestV1,
]:
    return (
        WorkSpecV1.from_mapping(_full_record("WorkSpecV1")),
        AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1")),
        WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1")),
        EffectFenceV1.from_mapping(_effect_fence_for_vector("author")),
        CandidateCapsuleManifestV1.from_mapping(
            _full_record("CandidateCapsuleManifestV1")
        ),
    )


_TEST_OBSERVATION_SPECS = (
    ("delivery_acknowledged", "direct_local_adapter", "acknowledged", "none"),
    ("delivery_rejected", "direct_local_adapter", "rejected", "none"),
    ("worker_started", "worker", "started", "none"),
    ("worker_completed", "worker", "completed", "none"),
    ("candidate_captured", "worker", "captured", "candidate"),
    ("capsule_sealed", "capsule_builder", "sealed", "capsule"),
    ("capsule_seal_failed", "capsule_builder", "failed", "candidate"),
    ("validation_completed", "validator", "passed", "capsule"),
    (
        "independent_review_completed",
        "independent_reviewer",
        "passed",
        "capsule",
    ),
    (
        "cancellation_acknowledged",
        "direct_local_adapter",
        "acknowledged",
        "none",
    ),
    ("cancellation_rejected", "direct_local_adapter", "rejected", "none"),
    ("process_exited", "direct_local_adapter", "exited", "exit"),
    ("deadline_elapsed", "direct_local_adapter", "elapsed", "none"),
    ("delivery_outcome_unknown", "direct_local_adapter", "unknown", "none"),
    (
        "workspace_teardown_succeeded",
        "workspace_custodian",
        "succeeded",
        "capsule",
    ),
    (
        "workspace_teardown_failed",
        "workspace_custodian",
        "failed",
        "capsule",
    ),
    (
        "capsule_retrieval_succeeded",
        "capsule_store",
        "succeeded",
        "capsule",
    ),
    ("capsule_retrieval_failed", "capsule_store", "failed", "capsule"),
)

_TEST_OBSERVATION_GRAPH_FAMILIES = (
    (
        "author",
        "author_candidate",
        None,
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "worker_started",
            "worker_completed",
            "candidate_captured",
            "capsule_sealed",
            "capsule_seal_failed",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
            "workspace_teardown_succeeded",
            "workspace_teardown_failed",
        ),
        (),
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "worker_started",
            "worker_completed",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
        ),
    ),
    (
        "validation",
        "validate_candidate",
        None,
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "validation_completed",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
            "capsule_retrieval_succeeded",
            "capsule_retrieval_failed",
        ),
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
        ),
        (),
    ),
    (
        "review",
        "review_candidate",
        None,
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "independent_review_completed",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
            "capsule_retrieval_succeeded",
            "capsule_retrieval_failed",
        ),
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
        ),
        (),
    ),
    (
        "cancel_author",
        "cancel_effect",
        "author_candidate",
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
            "workspace_teardown_succeeded",
            "workspace_teardown_failed",
        ),
        (),
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
        ),
    ),
    (
        "cancel_validation",
        "cancel_effect",
        "validate_candidate",
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
            "workspace_teardown_succeeded",
            "workspace_teardown_failed",
        ),
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
        ),
        (),
    ),
    (
        "cancel_review",
        "cancel_effect",
        "review_candidate",
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
            "workspace_teardown_succeeded",
            "workspace_teardown_failed",
        ),
        (
            "delivery_acknowledged",
            "delivery_rejected",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "process_exited",
            "deadline_elapsed",
            "delivery_outcome_unknown",
        ),
        (),
    ),
)


_TEST_MANDATORY_CANCELLATION_GRAPH_ROWS = (
    ("cancel_validation", "delivery_acknowledged"),
    ("cancel_validation", "delivery_rejected"),
    ("cancel_validation", "cancellation_rejected"),
    ("cancel_validation", "process_exited"),
    ("cancel_validation", "deadline_elapsed"),
    ("cancel_validation", "delivery_outcome_unknown"),
    ("cancel_review", "delivery_acknowledged"),
    ("cancel_review", "delivery_rejected"),
    ("cancel_review", "cancellation_acknowledged"),
    ("cancel_review", "cancellation_rejected"),
    ("cancel_review", "process_exited"),
    ("cancel_review", "deadline_elapsed"),
    ("cancel_review", "delivery_outcome_unknown"),
)


def _assert_graph_expected_truth_source(source: str) -> None:
    declaration_names = (
        "_TEST_OBSERVATION_SPECS",
        "_TEST_OBSERVATION_GRAPH_FAMILIES",
        "_TEST_MANDATORY_CANCELLATION_GRAPH_ROWS",
    )
    module = ast.parse(source)
    assignments: dict[str, list[ast.Assign]] = {
        name: [] for name in declaration_names
    }
    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id in assignments:
                assignments[target.id].append(statement)

    defining_assignments: set[int] = set()
    for name in declaration_names:
        assert len(assignments[name]) == 1, (
            f"{name} must have exactly one top-level assignment"
        )
        assignment = assignments[name][0]
        assert len(assignment.targets) == 1
        defining_assignments.add(id(assignment))
        pending = [assignment.value]
        while pending:
            value = pending.pop()
            if isinstance(value, ast.Constant):
                continue
            if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
                pending.extend(value.elts)
                continue
            if isinstance(value, ast.Dict):
                assert all(key is not None for key in value.keys), (
                    f"{name} must not contain dictionary unpacking"
                )
                pending.extend(value.keys)
                pending.extend(value.values)
                continue
            raise AssertionError(
                f"{name} must be recursively literal, not {type(value).__name__}"
            )

    def root_name(value: ast.AST) -> str | None:
        while isinstance(value, (ast.Attribute, ast.Subscript)):
            value = value.value
        return value.id if isinstance(value, ast.Name) else None

    def target_names(value: ast.AST) -> set[str]:
        if isinstance(value, ast.Name):
            return {value.id}
        if isinstance(value, (ast.Tuple, ast.List)):
            return set().union(*(target_names(item) for item in value.elts))
        root = root_name(value)
        return {root} if root is not None else set()

    mutation_methods = {
        "add",
        "append",
        "clear",
        "extend",
        "insert",
        "pop",
        "remove",
        "reverse",
        "sort",
        "update",
    }
    for node in ast.walk(module):
        if id(node) in defining_assignments:
            continue
        mutation_targets: tuple[ast.AST, ...] = ()
        if isinstance(node, ast.Assign):
            mutation_targets = tuple(node.targets)
            if (
                isinstance(node.value, ast.Name)
                and node.value.id in declaration_names
            ):
                raise AssertionError(
                    f"{node.value.id} must not be assigned through an alias"
                )
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            mutation_targets = (node.target,)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            mutation_targets = (node.target,)
        elif isinstance(node, ast.Delete):
            mutation_targets = tuple(node.targets)
        if any(
            target_names(target).intersection(declaration_names)
            for target in mutation_targets
        ):
            raise AssertionError(
                "graph expected-truth declarations must not be rebound or mutated"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in mutation_methods
            and root_name(node.func.value) in declaration_names
        ):
            raise AssertionError(
                "graph expected-truth declarations must not be mutated after definition"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("delattr", "setattr")
            and node.args
            and root_name(node.args[0]) in declaration_names
        ):
            raise AssertionError(
                "graph expected-truth declarations must not be mutated dynamically"
            )


def _fresh_test_observation_graph(
    family: str, index: int
) -> tuple[
    AttemptFenceV1,
    WorkerCommandV1,
    EffectFenceV1,
    CandidateCapsuleManifestV1,
    EffectFenceV1,
    DeliveryEnvelopeV1,
    EffectFenceV1 | None,
]:
    _, attempt, command, author_fence, manifest = _common_graph()
    label = family.replace("_", "-")
    cancellation_target: EffectFenceV1 | None = None

    if family in ("validation", "review", "cancel_validation", "cancel_review"):
        target_class = (
            "review_candidate"
            if family in ("review", "cancel_review")
            else "validate_candidate"
        )
        target = create_effect_fence(
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence_ref=f"effect-fence.graph-matrix.{label}.{index:03d}.target",
            effect_intent_ref=f"effect-intent.graph-matrix.{label}.{index:03d}.target",
            effect_class=target_class,
            effect_authorization_ref=(
                f"effect-authorization.graph-matrix.{label}.{index:03d}.target"
            ),
            effect_authorization_digest="b" * 64,
            effect_ceilings=command.effect_ceilings,
            expires_at=author_fence.expires_at,
            capsule_manifest=manifest,
        )
        effect_fence = target
    else:
        effect_fence = author_fence

    if family in ("cancel_author", "cancel_validation", "cancel_review"):
        cancellation_target = (
            author_fence if family == "cancel_author" else effect_fence
        )
        cancellation_arguments: dict[str, object] = {
            "attempt_fence": attempt,
            "author_command": command,
            "author_effect_fence": author_fence,
            "effect_fence_ref": (
                f"effect-fence.graph-matrix.{label}.{index:03d}.cancel"
            ),
            "effect_intent_ref": (
                f"effect-intent.graph-matrix.{label}.{index:03d}.cancel"
            ),
            "effect_class": "cancel_effect",
            "effect_authorization_ref": (
                f"effect-authorization.graph-matrix.{label}.{index:03d}.cancel"
            ),
            "effect_authorization_digest": "c" * 64,
            "effect_ceilings": command.effect_ceilings,
            "expires_at": author_fence.expires_at,
            "cancellation_target": cancellation_target,
        }
        if family in ("cancel_validation", "cancel_review"):
            cancellation_arguments["capsule_manifest"] = manifest
        effect_fence = create_effect_fence(**cancellation_arguments)

    delivery_arguments: dict[str, object] = {
        "delivery_attempt_ref": (
            f"delivery-attempt.graph-matrix.{label}.{index:03d}"
        ),
        "adapter_kind": "direct_local_bootstrap",
        "adapter_safe_correlation_ref": (
            f"adapter-correlation.graph-matrix.{label}.{index:03d}"
        ),
        "author_command": command,
        "attempt_fence": attempt,
        "author_effect_fence": author_fence,
        "effect_fence": effect_fence,
    }
    if family in ("validation", "review", "cancel_validation", "cancel_review"):
        delivery_arguments["capsule_manifest"] = manifest
    if cancellation_target is not None:
        delivery_arguments["cancellation_target"] = cancellation_target
    delivery = DeliveryEnvelopeV1.create(**delivery_arguments)
    return (
        attempt,
        command,
        author_fence,
        manifest,
        effect_fence,
        delivery,
        cancellation_target,
    )


def _sibling_test_manifest(
    manifest: CandidateCapsuleManifestV1, index: int
) -> CandidateCapsuleManifestV1:
    sibling_mapping = manifest.to_mapping()
    sibling_mapping["capsule_manifest_ref"] = (
        f"capsule-manifest.graph-matrix-sibling.{index:03d}"
    )
    return CandidateCapsuleManifestV1.from_mapping(
        _reseal_single_digest_record(
            "CandidateCapsuleManifestV1", sibling_mapping
        )
    )


def test_author_pair_factory_post_binds_without_exposing_a_draft() -> None:
    work, attempt, _, _, _ = _common_graph()
    expected = _full_record("WorkerCommandV1")
    command, fence = create_author_command_and_effect_fence(
        work_spec=work,
        attempt_fence=attempt,
        command_ref=expected["command_ref"],
        effect_intent_ref=expected["effect_intent_ref"],
        effect_fence_ref=expected["effect_fence_ref"],
        candidate_ref=expected["candidate_ref"],
        effect_authorization_ref=expected["effect_authorization_ref"],
        effect_authorization_digest=expected["effect_authorization_digest"],
        expires_at="2030-01-01T00:00:00Z",
        validation_requirement_digest=expected[
            "validation_requirement_digest"
        ],
        review_requirement_digest=expected["review_requirement_digest"],
        capsule_profile_ref=expected["capsule_profile_ref"],
        redaction_profile_ref=expected["redaction_profile_ref"],
        effect_ceilings=CeilingsV1.from_mapping(expected["effect_ceilings"]),
    )
    assert command.command_digest == (
        "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927"
    )
    assert fence.command_digest == command.command_digest
    assert command.effect_fence_digest == fence.effect_fence_digest
    validate_authoring_relation(
        work_spec=work,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=fence,
    )

    sibling_mapping = fence.to_mapping()
    sibling_mapping["effect_fence_ref"] = "effect-fence.sibling.0001"
    sibling = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", sibling_mapping)
    )
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_authoring_relation(
            work_spec=work,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=sibling,
        )


@pytest.mark.parametrize(
    "vector,effect_digest,delivery_digest,observation_digest",
    (
        (
            "author",
            "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3",
            "3f72f9a3717b54275fa5c580bba60ba30381c662ce2460bcc61dfc818a18fe9a",
            "96a4cb680ae911223392d937a5b108d0b5074196535355e69d730f7a1c542dad",
        ),
        (
            "validation",
            "d0867a8d6d6f89fcd8d7efe1a150f6eb904f0dd8a918065de0224db0cb9a9531",
            "888725d2de1b7095c3cb1453c5ec4e2046c7507e732556fcd3becc8635052e74",
            "44ad4d6f505e0cfff96cf4147e4864bc942a153f85022653115e910910a737c3",
        ),
        (
            "review",
            "e615b172eeddca9b69fd6d956b535e7ca60eb36f51e73038586a9ce67316a2bc",
            "7f351c06be0b3852d542059f7b5e9f66a23219e04fb7071c11cc4e472bc839a1",
            "be91f32ee69fc46e48526471c05b2b60f7b691b5beb7d0980e585da97b67cb13",
        ),
        (
            "cancellation",
            "ccaf53c44a06410e602c9f39ddc1677e734c0ba6f92c783752b28d1f7e5ff463",
            "524ad35f298997e9d9645b0ca46fa793994a0d236ad5f0485b7a82809e04e3a2",
            "9cd66023e89e15d94149bd17aae26b9b988433e6f57eb2db6feed77a29cde78d",
        ),
        (
            "cancellation_validation",
            "ae4de68f737afa1e5f22b72384a188abad36d3f9a4ae5e28e835e7644dc0b66b",
            "e8fb1839de45b48123014b27ec37068004543880fda95f269800435498579575",
            "9febe2f17b145ceb8d3002515cf574ac58e1633ee6ec70434ce5ca4f851fc345",
        ),
    ),
)
def test_five_frozen_relation_controls_use_actual_records(
    vector: str,
    effect_digest: str,
    delivery_digest: str,
    observation_digest: str,
) -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    effect_fence = EffectFenceV1.from_mapping(_effect_fence_for_vector(vector))
    delivery = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector(vector))
    observation = WorkerObservationV1.from_mapping(_observation_for_vector(vector))
    cancellation_target: object
    if vector == "cancellation_validation":
        cancellation_target = EffectFenceV1.from_mapping(
            _effect_fence_for_vector("validation")
        )
    elif vector == "cancellation":
        cancellation_target = author_fence
    else:
        cancellation_target = None
    effect_manifest: object = (
        manifest
        if vector in ("validation", "review", "cancellation_validation")
        else None
    )

    effect_keywords: dict[str, object] = {}
    if effect_manifest is not None:
        effect_keywords["capsule_manifest"] = effect_manifest
    if cancellation_target is not None:
        effect_keywords["cancellation_target"] = cancellation_target
    validate_effect_relation(
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author_fence,
        effect_fence=effect_fence,
        **effect_keywords,
    )
    validate_delivery_relation(
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=effect_fence,
        **effect_keywords,
    )

    observation_keywords: dict[str, object] = {}
    if observation.observation_kind in (
        "capsule_sealed",
        "validation_completed",
        "independent_review_completed",
    ):
        observation_keywords.update(
            capsule_manifest=manifest,
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
        )
    elif vector == "cancellation_validation":
        observation_keywords["capsule_manifest"] = manifest
    if cancellation_target is not None:
        observation_keywords["cancellation_target"] = cancellation_target
    validate_observation_relation(
        observation=observation,
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=effect_fence,
        **observation_keywords,
    )

    assert effect_fence.effect_fence_digest == effect_digest
    assert delivery.delivery_envelope_digest == delivery_digest
    assert observation.observation_digest == observation_digest


@pytest.mark.parametrize("vector", ("validation", "review"))
def test_non_author_effect_factory_requires_and_binds_exact_manifest(vector: str) -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    expected = _effect_fence_for_vector(vector)
    created = create_effect_fence(
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author_fence,
        effect_fence_ref=expected["effect_fence_ref"],
        effect_intent_ref=expected["effect_intent_ref"],
        effect_class=expected["effect_class"],
        effect_authorization_ref=expected["effect_authorization_ref"],
        effect_authorization_digest=expected["effect_authorization_digest"],
        effect_ceilings=CeilingsV1.from_mapping(expected["effect_ceilings"]),
        expires_at=expected["expires_at"],
        capsule_manifest=manifest,
    )
    assert created.to_mapping() == expected

    with pytest.raises(WorkerExecutionValueError):
        create_effect_fence(
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence_ref="effect-fence.forbidden-author.0001",
            effect_intent_ref="effect-intent.forbidden-author.0001",
            effect_class="author_candidate",
            effect_authorization_ref="effect-authorization.forbidden-author.0001",
            effect_authorization_digest="a" * 64,
            effect_ceilings=command.effect_ceilings,
            expires_at=author_fence.expires_at,
        )


def test_cancellation_factory_binds_immutable_author_and_validation_targets() -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    expected_author_cancel = _effect_fence_for_vector("cancellation")
    author_cancel = create_effect_fence(
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author_fence,
        effect_fence_ref=expected_author_cancel["effect_fence_ref"],
        effect_intent_ref=expected_author_cancel["effect_intent_ref"],
        effect_class="cancel_effect",
        effect_authorization_ref=expected_author_cancel[
            "effect_authorization_ref"
        ],
        effect_authorization_digest=expected_author_cancel[
            "effect_authorization_digest"
        ],
        effect_ceilings=CeilingsV1.from_mapping(
            expected_author_cancel["effect_ceilings"]
        ),
        expires_at=expected_author_cancel["expires_at"],
        cancellation_target=author_fence,
    )
    assert author_cancel.to_mapping() == expected_author_cancel
    assert author_cancel.portable_capsule_digest is None

    validation = EffectFenceV1.from_mapping(
        _effect_fence_for_vector("validation")
    )
    expected_validation_cancel = _effect_fence_for_vector(
        "cancellation_validation"
    )
    validation_cancel = create_effect_fence(
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author_fence,
        effect_fence_ref=expected_validation_cancel["effect_fence_ref"],
        effect_intent_ref=expected_validation_cancel["effect_intent_ref"],
        effect_class="cancel_effect",
        effect_authorization_ref=expected_validation_cancel[
            "effect_authorization_ref"
        ],
        effect_authorization_digest=expected_validation_cancel[
            "effect_authorization_digest"
        ],
        effect_ceilings=CeilingsV1.from_mapping(
            expected_validation_cancel["effect_ceilings"]
        ),
        expires_at=expected_validation_cancel["expires_at"],
        capsule_manifest=manifest,
        cancellation_target=validation,
    )
    assert validation_cancel.to_mapping() == expected_validation_cancel
    assert (
        validation_cancel.portable_capsule_digest
        == validation.portable_capsule_digest
        == manifest.portable_capsule_digest
    )


@pytest.mark.parametrize(
    "collision_field",
    ("effect_intent_ref", "effect_fence_ref", "effect_fence_digest"),
)
def test_cancellation_rejects_current_target_identity_collisions(
    collision_field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    mapping = _effect_fence_for_vector("cancellation")
    mapping[collision_field] = getattr(author_fence, collision_field)
    original_domain_digest = semantic_values._domain_digest

    def assert_effect_and_factory_reject(current: EffectFenceV1) -> None:
        expected_path = (
            "validate_effect_relation.cancellation_target."
            f"{collision_field}_collision"
        )
        with pytest.raises(WorkerExecutionValueError) as caught:
            validate_effect_relation(
                attempt_fence=attempt,
                author_command=command,
                author_effect_fence=author_fence,
                effect_fence=current,
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

        with pytest.raises(WorkerExecutionValueError) as caught:
            create_effect_fence(
                attempt_fence=attempt,
                author_command=command,
                author_effect_fence=author_fence,
                effect_fence_ref=mapping["effect_fence_ref"],
                effect_intent_ref=mapping["effect_intent_ref"],
                effect_class="cancel_effect",
                effect_authorization_ref=mapping["effect_authorization_ref"],
                effect_authorization_digest=mapping[
                    "effect_authorization_digest"
                ],
                effect_ceilings=CeilingsV1.from_mapping(
                    mapping["effect_ceilings"]
                ),
                expires_at=mapping["expires_at"],
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

    if collision_field == "effect_fence_digest":
        identity = dict(mapping)
        identity.pop("effect_fence_digest")
        canonical_identity = semantic_values._canonical_bytes(
            identity, "test.cancellation_collision"
        )

        def substituted_digest(domain: str, canonical_bytes: bytes) -> str:
            if (
                domain == EffectFenceV1._DOMAIN
                and canonical_bytes == canonical_identity
            ):
                return author_fence.effect_fence_digest
            return original_domain_digest(domain, canonical_bytes)

        with monkeypatch.context() as digest_patch:
            digest_patch.setattr(
                semantic_values, "_domain_digest", substituted_digest
            )
            current = EffectFenceV1.from_mapping(mapping)
            assert_effect_and_factory_reject(current)
        assert semantic_values._domain_digest is original_domain_digest
    else:
        current = EffectFenceV1.from_mapping(
            _reseal_single_digest_record("EffectFenceV1", mapping)
        )
        assert_effect_and_factory_reject(current)


@pytest.mark.parametrize(
    "collision_field",
    ("effect_intent_ref", "effect_fence_ref", "effect_fence_digest"),
)
def test_cancellation_identity_collisions_reject_through_delivery_and_observation(
    collision_field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    mapping = _effect_fence_for_vector("cancellation")
    mapping[collision_field] = getattr(author_fence, collision_field)
    original_domain_digest = semantic_values._domain_digest

    def assert_propagation_rejects(current: EffectFenceV1) -> None:
        expected_path = (
            "validate_effect_relation.cancellation_target."
            f"{collision_field}_collision"
        )
        delivery_mapping = _delivery_for_vector("cancellation")
        delivery_mapping["effect_intent_ref"] = current.effect_intent_ref
        delivery_mapping["effect_fence_ref"] = current.effect_fence_ref
        delivery_mapping["effect_fence_digest"] = current.effect_fence_digest
        delivery = DeliveryEnvelopeV1.from_mapping(
            _reseal_single_digest_record(
                "DeliveryEnvelopeV1", delivery_mapping
            )
        )
        redelivery = DeliveryEnvelopeV1.from_mapping(
            _valid_redelivery_candidate(delivery.to_mapping())
        )
        observation_mapping = _observation_for_vector("cancellation")
        observation_mapping["effect_intent_ref"] = current.effect_intent_ref
        observation_mapping["effect_fence_ref"] = current.effect_fence_ref
        observation_mapping["effect_fence_digest"] = current.effect_fence_digest
        observation = WorkerObservationV1.from_mapping(
            _reseal_observation(observation_mapping)
        )

        with pytest.raises(WorkerExecutionValueError) as caught:
            DeliveryEnvelopeV1.create(
                delivery_attempt_ref=delivery.delivery_attempt_ref,
                adapter_kind=delivery.adapter_kind,
                adapter_safe_correlation_ref=delivery.adapter_safe_correlation_ref,
                author_command=command,
                attempt_fence=attempt,
                author_effect_fence=author_fence,
                effect_fence=current,
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

        with pytest.raises(WorkerExecutionValueError) as caught:
            validate_delivery_relation(
                delivery=delivery,
                author_command=command,
                attempt_fence=attempt,
                author_effect_fence=author_fence,
                effect_fence=current,
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

        with pytest.raises(WorkerExecutionValueError) as caught:
            validate_redelivery_relation(
                original_delivery=delivery,
                candidate_delivery=redelivery,
                author_command=command,
                attempt_fence=attempt,
                author_effect_fence=author_fence,
                effect_fence=current,
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

        with pytest.raises(WorkerExecutionValueError) as caught:
            WorkerObservationV1.create(
                observation_ref=observation.observation_ref,
                source_kind=observation.source_kind,
                source_ref=observation.source_ref,
                source_invocation_ref=observation.source_invocation_ref,
                observation_kind=observation.observation_kind,
                outcome=observation.outcome,
                reason_code=observation.reason_code,
                evidence_refs=list(observation.evidence_refs),
                observed_at=observation.observed_at,
                delivery=delivery,
                author_command=command,
                attempt_fence=attempt,
                author_effect_fence=author_fence,
                effect_fence=current,
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

        with pytest.raises(WorkerExecutionValueError) as caught:
            validate_observation_relation(
                observation=observation,
                delivery=delivery,
                author_command=command,
                attempt_fence=attempt,
                author_effect_fence=author_fence,
                effect_fence=current,
                cancellation_target=author_fence,
            )
        assert caught.value.field_path == expected_path

    if collision_field == "effect_fence_digest":
        identity = dict(mapping)
        identity.pop("effect_fence_digest")
        canonical_identity = semantic_values._canonical_bytes(
            identity, "test.cancellation_collision"
        )

        def substituted_digest(domain: str, canonical_bytes: bytes) -> str:
            if (
                domain == EffectFenceV1._DOMAIN
                and canonical_bytes == canonical_identity
            ):
                return author_fence.effect_fence_digest
            return original_domain_digest(domain, canonical_bytes)

        with monkeypatch.context() as digest_patch:
            digest_patch.setattr(
                semantic_values, "_domain_digest", substituted_digest
            )
            current = EffectFenceV1.from_mapping(mapping)
            assert_propagation_rejects(current)
        assert semantic_values._domain_digest is original_domain_digest
    else:
        current = EffectFenceV1.from_mapping(
            _reseal_single_digest_record("EffectFenceV1", mapping)
        )
        assert_propagation_rejects(current)


def test_effect_class_and_ceiling_relations_fail_closed() -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    validation_mapping = _effect_fence_for_vector("validation")
    validation_mapping["effect_ceilings"]["max_cpu_seconds"] = (
        attempt.aggregate_ceilings.max_cpu_seconds + 1
    )
    widened = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", validation_mapping)
    )
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_effect_relation(
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence=widened,
            capsule_manifest=manifest,
        )

    narrowed_attempt_mapping = attempt.to_mapping()
    narrowed_attempt_mapping["allowed_effect_classes"].remove(
        "validate_candidate"
    )
    narrowed_attempt = AttemptFenceV1.from_mapping(
        _reseal_single_digest_record("AttemptFenceV1", narrowed_attempt_mapping)
    )
    validation = EffectFenceV1.from_mapping(
        _effect_fence_for_vector("validation")
    )
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_effect_relation(
            attempt_fence=narrowed_attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence=validation,
            capsule_manifest=manifest,
        )


def test_delivery_binding_and_exact_redelivery_delta() -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    original = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector("author"))
    later = DeliveryEnvelopeV1.from_mapping(
        _valid_redelivery_candidate(original.to_mapping())
    )
    validate_redelivery_relation(
        original_delivery=original,
        candidate_delivery=later,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=author_fence,
    )
    assert original.delivery_attempt_ref != later.delivery_attempt_ref
    assert (
        original.adapter_safe_correlation_ref
        != later.adapter_safe_correlation_ref
    )

    same_attempt = later.to_mapping()
    same_attempt["delivery_attempt_ref"] = original.delivery_attempt_ref
    same_attempt = _reseal_single_digest_record(
        "DeliveryEnvelopeV1", same_attempt
    )
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_redelivery_relation(
            original_delivery=original,
            candidate_delivery=DeliveryEnvelopeV1.from_mapping(same_attempt),
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
        )


@pytest.mark.parametrize(
    "field",
    (
        "schema_id",
        "program_ref",
        "program_version_ref",
        "command_ref",
        "command_digest",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "adapter_kind",
    ),
)
def test_every_other_redelivery_identity_delta_rejects(field: str) -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    original = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector("author"))
    changed = _valid_redelivery_candidate(original.to_mapping())
    if field == "adapter_kind":
        changed[field] = "execution_substrate"
    elif field == "schema_id":
        changed[field] = "governed-execution.nwp-delivery-envelope.v2"
    elif field.endswith("_digest"):
        changed[field] = "0" * 64
    else:
        changed[field] = f"{changed[field]}.different"
    changed = _reseal_single_digest_record("DeliveryEnvelopeV1", changed)
    if field == "schema_id":
        with pytest.raises(WorkerExecutionValueError):
            DeliveryEnvelopeV1.from_mapping(changed)
        return
    candidate = DeliveryEnvelopeV1.from_mapping(changed)
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_redelivery_relation(
            original_delivery=original,
            candidate_delivery=candidate,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
        )


def test_manifest_relation_accepts_binary_blobs_and_rejects_blob_or_key_drift() -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    before = {
        AUTHORIZED_PATHS[0]: b"\x00\xff",
        AUTHORIZED_PATHS[1]: b"",
        AUTHORIZED_PATHS[2]: b"binary\x80without-lf",
    }
    after = {
        AUTHORIZED_PATHS[0]: b"\xfe\x00after",
        AUTHORIZED_PATHS[1]: b"no-final-lf",
        AUTHORIZED_PATHS[2]: b"\x01\x02\x03",
    }
    manifest = CandidateCapsuleManifestV1.create(
        before_blobs=before,
        after_blobs=after,
        modes={path: "100644" for path in AUTHORIZED_PATHS},
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        capsule_manifest_ref="capsule-manifest.binary.0001",
    )
    validate_capsule_manifest_relation(
        capsule_manifest=manifest,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        before_blobs=before,
        after_blobs=after,
    )
    changed = dict(after)
    changed[AUTHORIZED_PATHS[0]] += b"x"
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_capsule_manifest_relation(
            capsule_manifest=manifest,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            before_blobs=before,
            after_blobs=changed,
        )
    missing = dict(before)
    missing.pop(AUTHORIZED_PATHS[0])
    with pytest.raises(WorkerExecutionValueError, match="missing_field"):
        validate_capsule_manifest_relation(
            capsule_manifest=manifest,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            before_blobs=missing,
            after_blobs=after,
        )
    extra = dict(after)
    extra["fourth.md"] = b""
    with pytest.raises(WorkerExecutionValueError, match="unknown_field"):
        validate_capsule_manifest_relation(
            capsule_manifest=manifest,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            before_blobs=before,
            after_blobs=extra,
        )


@pytest.mark.parametrize(
    "kind",
    (
        "delivery_acknowledged",
        "delivery_rejected",
        "worker_started",
        "worker_completed",
        "candidate_captured",
        "capsule_sealed",
        "capsule_seal_failed",
        "validation_completed",
        "independent_review_completed",
        "cancellation_acknowledged",
        "cancellation_rejected",
        "process_exited",
        "deadline_elapsed",
        "delivery_outcome_unknown",
        "workspace_teardown_succeeded",
        "workspace_teardown_failed",
        "capsule_retrieval_succeeded",
        "capsule_retrieval_failed",
    ),
)
def test_all_observation_kinds_and_conditional_forms(kind: str) -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    observation_mapping, effect_mapping, delivery_mapping = _observation_for_kind(
        kind
    )
    observation = WorkerObservationV1.from_mapping(observation_mapping)
    effect_fence = EffectFenceV1.from_mapping(effect_mapping)
    delivery = DeliveryEnvelopeV1.from_mapping(delivery_mapping)
    keywords: dict[str, object] = {}
    if kind in (
        "capsule_sealed",
        "validation_completed",
        "independent_review_completed",
        "workspace_teardown_succeeded",
        "workspace_teardown_failed",
        "capsule_retrieval_succeeded",
        "capsule_retrieval_failed",
    ):
        keywords.update(
            capsule_manifest=manifest,
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
        )
    if effect_fence.effect_class == "cancel_effect":
        keywords["cancellation_target"] = author_fence
    validate_observation_relation(
        observation=observation,
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=effect_fence,
        **keywords,
    )


def test_worker_observation_factory_separates_graph_manifest_from_identity_fields() -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    effect_fence = EffectFenceV1.from_mapping(
        _effect_fence_for_vector("validation")
    )
    delivery = DeliveryEnvelopeV1.from_mapping(
        _delivery_for_vector("validation")
    )
    observation = WorkerObservationV1.create(
        observation_ref="observation.graph-evidence.0001",
        source_kind="direct_local_adapter",
        source_ref="direct-local-adapter.graph-evidence.0001",
        source_invocation_ref="source-invocation.graph-evidence.0001",
        observation_kind="delivery_acknowledged",
        outcome="acknowledged",
        reason_code="reason.none",
        evidence_refs=["evidence.graph-evidence.0001"],
        observed_at="2026-08-08T18:10:00Z",
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=effect_fence,
        capsule_manifest=manifest,
    )
    serialized = observation.to_mapping()
    assert not {
        "candidate_ref",
        "capsule_manifest_ref",
        "portable_capsule_digest",
        "process_exit_code",
    } & set(serialized)
    validate_observation_relation(
        observation=observation,
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=effect_fence,
        capsule_manifest=manifest,
    )

    with pytest.raises(WorkerExecutionValueError):
        WorkerObservationV1.create(
            observation_ref="observation.graph-evidence.omitted.0001",
            source_kind="direct_local_adapter",
            source_ref="direct-local-adapter.graph-evidence.0001",
            source_invocation_ref="source-invocation.graph-evidence.0001",
            observation_kind="delivery_acknowledged",
            outcome="acknowledged",
            reason_code="reason.none",
            evidence_refs=["evidence.graph-evidence.0001"],
            observed_at="2026-08-08T18:10:00Z",
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=effect_fence,
        )

    sibling_mapping = manifest.to_mapping()
    sibling_mapping["capsule_manifest_ref"] = "capsule-manifest.sibling.0001"
    sibling_manifest = CandidateCapsuleManifestV1.from_mapping(
        _reseal_single_digest_record(
            "CandidateCapsuleManifestV1", sibling_mapping
        )
    )
    with pytest.raises(WorkerExecutionValueError):
        WorkerObservationV1.create(
            observation_ref="observation.graph-evidence.mismatch.0001",
            source_kind="direct_local_adapter",
            source_ref="direct-local-adapter.graph-evidence.0001",
            source_invocation_ref="source-invocation.graph-evidence.0001",
            observation_kind="delivery_acknowledged",
            outcome="acknowledged",
            reason_code="reason.none",
            evidence_refs=["evidence.graph-evidence.0001"],
            observed_at="2026-08-08T18:10:00Z",
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=effect_fence,
            capsule_manifest=sibling_manifest,
        )


def test_worker_observation_graph_expected_truth_is_literal_test_owned_and_immutable() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    _assert_graph_expected_truth_source(source)


def test_worker_observation_graph_expected_truth_rejects_production_or_support_derivation() -> None:
    def candidate(graph_assignment: str, suffix: str = "") -> str:
        return (
            '_TEST_OBSERVATION_SPECS = (("kind", "source", "outcome", "none"),)\n'
            f"_TEST_OBSERVATION_GRAPH_FAMILIES = {graph_assignment}\n"
            '_TEST_MANDATORY_CANCELLATION_GRAPH_ROWS = (("family", "kind"),)\n'
            f"{suffix}"
        )

    literal_graph = '(("family", "effect", None, ("kind",), (), ()),)'
    _assert_graph_expected_truth_source(candidate(literal_graph))

    counterfactuals = (
        candidate(
            'semantic_values._effect_classes_for_observation("kind")'
        ),
        candidate(
            'tuple(row for row in semantic_values._effect_classes_for_observation("kind"))'
        ),
        candidate("c2a_contract_support.EXPECTED_ROWS"),
        (
            'PRODUCTION_ROWS = semantic_values._effect_classes_for_observation("kind")\n'
            + candidate("PRODUCTION_ROWS")
        ),
        candidate(
            literal_graph,
            "_TEST_OBSERVATION_GRAPH_FAMILIES += "
            'semantic_values._effect_classes_for_observation("kind")\n',
        ),
        candidate(
            '[("family", "effect", None, ("kind",), (), ())]',
            "_TEST_OBSERVATION_GRAPH_FAMILIES.append("
            'semantic_values._effect_classes_for_observation("kind"))\n',
        ),
        (
            "from tests.test_other_semantic_graph import EXPECTED_ROWS\n"
            + candidate("EXPECTED_ROWS")
        ),
    )
    for counterfactual in counterfactuals:
        with pytest.raises(AssertionError):
            _assert_graph_expected_truth_source(counterfactual)

    family_descriptors = (
        ("author", "author_candidate", None),
        ("validation", "validate_candidate", None),
        ("review", "review_candidate", None),
        ("cancel_author", "cancel_effect", "author_candidate"),
        ("cancel_validation", "cancel_effect", "validate_candidate"),
        ("cancel_review", "cancel_effect", "review_candidate"),
    )
    production_derived_rows = []
    for family, effect_class, target_class in family_descriptors:
        valid_kinds = tuple(
            kind
            for kind, _, _, _ in _TEST_OBSERVATION_SPECS
            if effect_class
            in semantic_values._effect_classes_for_observation(kind)
        )
        graph_manifest_required = effect_class in (
            "validate_candidate",
            "review_candidate",
        ) or (
            effect_class == "cancel_effect"
            and target_class in ("validate_candidate", "review_candidate")
        )
        graph_only_kinds = tuple(
            kind
            for kind in valid_kinds
            if graph_manifest_required
            and semantic_values._observation_spec(kind)[2] != "capsule"
        )
        unnecessary_kinds = tuple(
            kind
            for kind in valid_kinds
            if not graph_manifest_required
            and semantic_values._observation_spec(kind)[2] in ("none", "exit")
        )
        production_derived_rows.append(
            (
                family,
                effect_class,
                target_class,
                valid_kinds,
                graph_only_kinds,
                unnecessary_kinds,
            )
        )
    assert tuple(production_derived_rows) == _TEST_OBSERVATION_GRAPH_FAMILIES

    source = Path(__file__).read_text(encoding="utf-8")
    module = ast.parse(source)
    graph_assignment = next(
        statement
        for statement in module.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "_TEST_OBSERVATION_GRAPH_FAMILIES"
            for target in statement.targets
        )
    )
    source_lines = source.splitlines(keepends=True)
    production_replacement = '''_TEST_OBSERVATION_GRAPH_FAMILIES = tuple(
    (
        family,
        effect_class,
        target_class,
        tuple(
            kind
            for kind, _, _, _ in _TEST_OBSERVATION_SPECS
            if effect_class in semantic_values._effect_classes_for_observation(kind)
        ),
        tuple(
            kind
            for kind, _, _, _ in _TEST_OBSERVATION_SPECS
            if effect_class in semantic_values._effect_classes_for_observation(kind)
            and (
                effect_class in ("validate_candidate", "review_candidate")
                or effect_class == "cancel_effect"
                and target_class in ("validate_candidate", "review_candidate")
            )
            and semantic_values._observation_spec(kind)[2] != "capsule"
        ),
        tuple(
            kind
            for kind, _, _, _ in _TEST_OBSERVATION_SPECS
            if effect_class in semantic_values._effect_classes_for_observation(kind)
            and not (
                effect_class in ("validate_candidate", "review_candidate")
                or effect_class == "cancel_effect"
                and target_class in ("validate_candidate", "review_candidate")
            )
            and semantic_values._observation_spec(kind)[2] in ("none", "exit")
        ),
    )
    for family, effect_class, target_class in (
        ("author", "author_candidate", None),
        ("validation", "validate_candidate", None),
        ("review", "review_candidate", None),
        ("cancel_author", "cancel_effect", "author_candidate"),
        ("cancel_validation", "cancel_effect", "validate_candidate"),
        ("cancel_review", "cancel_effect", "review_candidate"),
    )
)
'''
    production_derived_source = "".join(
        (
            *source_lines[: graph_assignment.lineno - 1],
            production_replacement,
            *source_lines[graph_assignment.end_lineno :],
        )
    )
    with pytest.raises(AssertionError, match="recursively literal"):
        _assert_graph_expected_truth_source(production_derived_source)


def test_worker_observation_factory_covers_complete_contract_derived_graph_matrix() -> None:
    family_shape = tuple(
        (family, len(kinds), len(graph_only_kinds))
        for (
            family,
            _,
            _,
            kinds,
            graph_only_kinds,
            _,
        ) in _TEST_OBSERVATION_GRAPH_FAMILIES
    )
    assert family_shape == (
        ("author", 12, 0),
        ("validation", 8, 5),
        ("review", 8, 5),
        ("cancel_author", 9, 0),
        ("cancel_validation", 9, 7),
        ("cancel_review", 9, 7),
    )

    serial = 0
    for (
        family,
        effect_class,
        target_class,
        kinds,
        graph_only_kinds,
        _,
    ) in _TEST_OBSERVATION_GRAPH_FAMILIES:
        for kind in kinds:
            serial += 1
            _, source_kind, outcome, conditional = next(
                row for row in _TEST_OBSERVATION_SPECS if row[0] == kind
            )
            (
                attempt,
                command,
                author_fence,
                manifest,
                effect_fence,
                delivery,
                cancellation_target,
            ) = _fresh_test_observation_graph(family, serial)
            arguments: dict[str, object] = {
                "observation_ref": f"observation.graph-matrix.{serial:03d}",
                "source_kind": source_kind,
                "source_ref": f"source.graph-matrix.{serial:03d}",
                "source_invocation_ref": (
                    f"source-invocation.graph-matrix.{serial:03d}"
                ),
                "observation_kind": kind,
                "outcome": outcome,
                "reason_code": "reason.none",
                "evidence_refs": [f"evidence.graph-matrix.{serial:03d}"],
                "observed_at": "2026-08-08T18:10:00Z",
                "delivery": delivery,
                "author_command": command,
                "attempt_fence": attempt,
                "author_effect_fence": author_fence,
                "effect_fence": effect_fence,
            }
            if cancellation_target is not None:
                arguments["cancellation_target"] = cancellation_target
            if conditional == "exit":
                arguments["process_exit_code"] = 0
            if conditional == "capsule":
                arguments.update(
                    capsule_manifest=manifest,
                    before_blobs=_before_blobs(),
                    after_blobs=_after_blobs(),
                )
            elif kind in graph_only_kinds:
                arguments["capsule_manifest"] = manifest

            observation = WorkerObservationV1.create(**arguments)
            serialized = observation.to_mapping()
            assert type(observation) is WorkerObservationV1
            assert not hasattr(observation, "__dict__")
            assert observation.observation_kind == kind
            optional_fields = {
                "candidate_ref",
                "capsule_manifest_ref",
                "portable_capsule_digest",
                "process_exit_code",
            }
            if conditional == "candidate":
                expected_optional = {"candidate_ref"}
            elif conditional == "capsule":
                expected_optional = {
                    "candidate_ref",
                    "capsule_manifest_ref",
                    "portable_capsule_digest",
                }
            elif conditional == "exit":
                expected_optional = {"process_exit_code"}
            else:
                expected_optional = set()
            assert set(serialized) & optional_fields == expected_optional
            assert effect_fence.effect_class == effect_class
            assert (
                None
                if cancellation_target is None
                else cancellation_target.effect_class
            ) == target_class
            if cancellation_target is not None:
                assert (
                    effect_fence.cancellation_target_effect_intent_ref
                    == cancellation_target.effect_intent_ref
                )
                assert (
                    effect_fence.cancellation_target_effect_fence_ref
                    == cancellation_target.effect_fence_ref
                )
                assert (
                    effect_fence.cancellation_target_effect_fence_digest
                    == cancellation_target.effect_fence_digest
                )

            relation_arguments: dict[str, object] = {
                "observation": observation,
                "delivery": delivery,
                "author_command": command,
                "attempt_fence": attempt,
                "author_effect_fence": author_fence,
                "effect_fence": effect_fence,
            }
            if cancellation_target is not None:
                relation_arguments["cancellation_target"] = cancellation_target
            if conditional == "capsule":
                relation_arguments.update(
                    capsule_manifest=manifest,
                    before_blobs=_before_blobs(),
                    after_blobs=_after_blobs(),
                )
            elif kind in graph_only_kinds:
                relation_arguments["capsule_manifest"] = manifest
            validate_observation_relation(**relation_arguments)

    assert serial == 55


def test_worker_observation_factory_enforces_all_graph_only_manifest_requirements() -> None:
    serial = 100
    covered = 0
    for (
        family,
        _,
        _,
        _,
        graph_only_kinds,
        _,
    ) in _TEST_OBSERVATION_GRAPH_FAMILIES:
        for kind in graph_only_kinds:
            serial += 1
            covered += 1
            _, source_kind, outcome, conditional = next(
                row for row in _TEST_OBSERVATION_SPECS if row[0] == kind
            )
            assert conditional in ("none", "exit")
            (
                attempt,
                command,
                author_fence,
                manifest,
                effect_fence,
                delivery,
                cancellation_target,
            ) = _fresh_test_observation_graph(family, serial)
            arguments: dict[str, object] = {
                "observation_ref": (
                    f"observation.graph-only.{family.replace('_', '-')}.{serial:03d}"
                ),
                "source_kind": source_kind,
                "source_ref": f"source.graph-only.{serial:03d}",
                "source_invocation_ref": f"source-invocation.graph-only.{serial:03d}",
                "observation_kind": kind,
                "outcome": outcome,
                "reason_code": "reason.none",
                "evidence_refs": [f"evidence.graph-only.{serial:03d}"],
                "observed_at": "2026-08-08T18:11:00Z",
                "delivery": delivery,
                "author_command": command,
                "attempt_fence": attempt,
                "author_effect_fence": author_fence,
                "effect_fence": effect_fence,
            }
            if cancellation_target is not None:
                arguments["cancellation_target"] = cancellation_target
            if conditional == "exit":
                arguments["process_exit_code"] = 0

            exact = WorkerObservationV1.create(
                **arguments, capsule_manifest=manifest
            )
            expected_optional = (
                {"process_exit_code"} if conditional == "exit" else set()
            )
            assert (
                set(exact.to_mapping())
                & {
                    "candidate_ref",
                    "capsule_manifest_ref",
                    "portable_capsule_digest",
                    "process_exit_code",
                }
                == expected_optional
            )

            with pytest.raises(WorkerExecutionValueError) as omitted:
                WorkerObservationV1.create(**arguments)
            assert (omitted.value.reason, omitted.value.field_path) == (
                "invalid_field_type",
                "WorkerObservationV1.capsule_manifest",
            )

            sibling_manifest = _sibling_test_manifest(manifest, serial)
            with pytest.raises(WorkerExecutionValueError) as mismatched:
                WorkerObservationV1.create(
                    **arguments, capsule_manifest=sibling_manifest
                )
            assert mismatched.value.reason == "relation_mismatch"

    assert covered == 24


def test_worker_observation_graph_matrix_includes_all_cancellation_to_review_rows() -> None:
    cancel_review_row = next(
        row for row in _TEST_OBSERVATION_GRAPH_FAMILIES if row[0] == "cancel_review"
    )
    kinds = cancel_review_row[3]
    graph_only_kinds = cancel_review_row[4]
    assert kinds == (
        "delivery_acknowledged",
        "delivery_rejected",
        "cancellation_acknowledged",
        "cancellation_rejected",
        "process_exited",
        "deadline_elapsed",
        "delivery_outcome_unknown",
        "workspace_teardown_succeeded",
        "workspace_teardown_failed",
    )
    assert graph_only_kinds == (
        "delivery_acknowledged",
        "delivery_rejected",
        "cancellation_acknowledged",
        "cancellation_rejected",
        "process_exited",
        "deadline_elapsed",
        "delivery_outcome_unknown",
    )

    mandatory_rows = tuple(
        (family, kind)
        for family, _, _, _, graph_kinds, _ in _TEST_OBSERVATION_GRAPH_FAMILIES
        if family in ("cancel_validation", "cancel_review")
        for kind in graph_kinds
        if not (
            family == "cancel_validation"
            and kind == "cancellation_acknowledged"
        )
    )
    assert mandatory_rows == _TEST_MANDATORY_CANCELLATION_GRAPH_ROWS

    for index, kind in enumerate(kinds, start=201):
        _, source_kind, outcome, conditional = next(
            row for row in _TEST_OBSERVATION_SPECS if row[0] == kind
        )
        (
            attempt,
            command,
            author_fence,
            manifest,
            effect_fence,
            delivery,
            cancellation_target,
        ) = _fresh_test_observation_graph("cancel_review", index)
        assert cancellation_target is not None
        arguments: dict[str, object] = {
            "observation_ref": f"observation.cancel-review.{index:03d}",
            "source_kind": source_kind,
            "source_ref": f"source.cancel-review.{index:03d}",
            "source_invocation_ref": f"source-invocation.cancel-review.{index:03d}",
            "observation_kind": kind,
            "outcome": outcome,
            "reason_code": "reason.none",
            "evidence_refs": [f"evidence.cancel-review.{index:03d}"],
            "observed_at": "2026-08-08T18:12:00Z",
            "delivery": delivery,
            "author_command": command,
            "attempt_fence": attempt,
            "author_effect_fence": author_fence,
            "effect_fence": effect_fence,
            "capsule_manifest": manifest,
            "cancellation_target": cancellation_target,
        }
        if conditional == "exit":
            arguments["process_exit_code"] = 0
        if conditional == "capsule":
            arguments["before_blobs"] = _before_blobs()
            arguments["after_blobs"] = _after_blobs()
        WorkerObservationV1.create(**arguments)


def test_worker_observation_graph_matrix_rejects_unnecessary_manifest_evidence() -> None:
    covered = 0
    serial = 300
    for (
        family,
        _,
        _,
        _,
        _,
        unnecessary_manifest_kinds,
    ) in _TEST_OBSERVATION_GRAPH_FAMILIES:
        for kind in unnecessary_manifest_kinds:
            serial += 1
            covered += 1
            _, source_kind, outcome, conditional = next(
                row for row in _TEST_OBSERVATION_SPECS if row[0] == kind
            )
            assert conditional in ("none", "exit")
            (
                attempt,
                command,
                author_fence,
                manifest,
                effect_fence,
                delivery,
                cancellation_target,
            ) = _fresh_test_observation_graph(family, serial)
            arguments: dict[str, object] = {
                "observation_ref": f"observation.unnecessary.{serial:03d}",
                "source_kind": source_kind,
                "source_ref": f"source.unnecessary.{serial:03d}",
                "source_invocation_ref": f"source-invocation.unnecessary.{serial:03d}",
                "observation_kind": kind,
                "outcome": outcome,
                "reason_code": "reason.none",
                "evidence_refs": [f"evidence.unnecessary.{serial:03d}"],
                "observed_at": "2026-08-08T18:13:00Z",
                "delivery": delivery,
                "author_command": command,
                "attempt_fence": attempt,
                "author_effect_fence": author_fence,
                "effect_fence": effect_fence,
            }
            if cancellation_target is not None:
                arguments["cancellation_target"] = cancellation_target
            if conditional == "exit":
                arguments["process_exit_code"] = 0

            WorkerObservationV1.create(**arguments)
            with pytest.raises(WorkerExecutionValueError) as unnecessary:
                WorkerObservationV1.create(
                    **arguments, capsule_manifest=manifest
                )
            assert (unnecessary.value.reason, unnecessary.value.field_path) == (
                "invalid_field_value",
                "WorkerObservationV1.conditional_fields",
            )

    assert covered == 14


def test_direct_local_and_es_route_source_pairs_are_exact() -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    observation_mapping, _, delivery_mapping = _observation_for_kind(
        "delivery_acknowledged"
    )
    direct_observation = WorkerObservationV1.from_mapping(observation_mapping)
    direct_delivery = DeliveryEnvelopeV1.from_mapping(delivery_mapping)
    validate_observation_relation(
        observation=direct_observation,
        delivery=direct_delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=author_fence,
    )

    es_delivery_mapping = direct_delivery.to_mapping()
    es_delivery_mapping["adapter_kind"] = "execution_substrate"
    es_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record(
            "DeliveryEnvelopeV1", es_delivery_mapping
        )
    )
    es_observation_mapping = direct_observation.to_mapping()
    es_observation_mapping["source_kind"] = "es_adapter"
    es_observation = WorkerObservationV1.from_mapping(
        _reseal_observation(es_observation_mapping)
    )
    validate_observation_relation(
        observation=es_observation,
        delivery=es_delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        effect_fence=author_fence,
    )
    with pytest.raises(WorkerExecutionValueError, match="route_source"):
        validate_observation_relation(
            observation=es_observation,
            delivery=direct_delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
        )


def test_omission_is_distinct_from_explicit_none() -> None:
    _, attempt, command, author_fence, _ = _common_graph()
    validate_effect_relation(
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author_fence,
        effect_fence=author_fence,
    )
    with pytest.raises(WorkerExecutionValueError, match="capsule_manifest"):
        validate_effect_relation(
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
            capsule_manifest=None,
        )
    with pytest.raises(WorkerExecutionValueError, match="cancellation_target"):
        validate_effect_relation(
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
            cancellation_target=None,
        )


def test_locally_valid_decoded_observation_can_be_graph_incoherent() -> None:
    _, attempt, command, author_fence, manifest = _common_graph()
    delivery = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector("author"))
    observation_mapping = _observation_for_vector("author")
    observation_mapping["capsule_manifest_ref"] = "capsule-manifest.sibling.0001"
    observation = WorkerObservationV1.from_mapping(
        _reseal_observation(observation_mapping)
    )
    assert observation.observation_digest == observation.computed_digest()
    with pytest.raises(WorkerExecutionValueError, match="relation_mismatch"):
        validate_observation_relation(
            observation=observation,
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
            capsule_manifest=manifest,
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
        )
