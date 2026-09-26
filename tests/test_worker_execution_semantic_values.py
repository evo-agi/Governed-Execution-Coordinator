from __future__ import annotations

from collections.abc import Callable
from copy import copy, deepcopy
from pathlib import Path
import pickle
import sys
import traceback

import pytest

import ge_nwp_coordinator._worker_execution_semantic_values as semantic_values
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    CapsuleEntryV1,
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
    _observation_for_vector,
    _reseal_single_digest_record,
)


class _DictSubclass(dict[object, object]):
    pass


class _ListSubclass(list[object]):
    pass


class _StringSubclass(str):
    pass


class _IntegerSubclass(int):
    pass


class _HostileInput:
    def __init__(self, invocations: list[str], marker: str) -> None:
        self._invocations = invocations
        self._marker = marker

    def _called(self, method: str) -> None:
        self._invocations.append(method)
        raise RuntimeError(self._marker)

    def __eq__(self, other: object) -> bool:
        self._called("__eq__")

    def __format__(self, format_spec: str) -> str:
        self._called("__format__")

    def __hash__(self) -> int:
        self._called("__hash__")

    def __int__(self) -> int:
        self._called("__int__")

    def __iter__(self):
        self._called("__iter__")

    def __repr__(self) -> str:
        self._called("__repr__")

    def __str__(self) -> str:
        self._called("__str__")

    @property
    def effect_class(self) -> str:
        self._called("effect_class")


def test_private_owner_reconstruction_rejects_deep_raw_state_before_projection() -> None:
    reconstruct = getattr(
        semantic_values, "_reconstruct_exact_worker_execution_value"
    )
    work_spec = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    nested: object = "leaf"
    for _ in range(2_000):
        nested = (nested,)
    object.__setattr__(work_spec, "_requirements", (nested,))

    with pytest.raises(WorkerExecutionValueError) as caught:
        reconstruct(work_spec, WorkSpecV1)
    assert caught.value.reason == "relation_mismatch"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


_OWNER_RECONSTRUCTION_CASES = (
    (CeilingsV1, "CeilingsV1", 16, 32),
    (CapsuleEntryV1, "CapsuleEntryV1", 8, 16),
    (WorkSpecV1, "WorkSpecV1", 86, 172),
    (AttemptFenceV1, "AttemptFenceV1", 46, 92),
    (EffectFenceV1, "EffectFenceV1", 51, 102),
    (WorkerCommandV1, "WorkerCommandV1", 58, 116),
    (DeliveryEnvelopeV1, "DeliveryEnvelopeV1", 16, 32),
    (CandidateCapsuleManifestV1, "CandidateCapsuleManifestV1", 49, 98),
)


def _maximum_owner_value(value_type: type, model_name: str):
    if value_type is CeilingsV1:
        return value_type.from_mapping(
            _full_record("AttemptFenceV1")["aggregate_ceilings"]
        )
    if value_type is CapsuleEntryV1:
        return value_type.from_mapping(
            _full_record("CandidateCapsuleManifestV1")["entries"][0]
        )
    mapping = _full_record(model_name)
    if value_type is WorkSpecV1:
        mapping["requirements"] = [f"requirement-{index:02d}" for index in range(32)]
        mapping["exclusions"] = [f"exclusion-{index:02d}" for index in range(32)]
        mapping = _reseal_single_digest_record(model_name, mapping)
    return value_type.from_mapping(mapping)


@pytest.mark.parametrize(
    "value_type,model_name,graph_work,tariff", _OWNER_RECONSTRUCTION_CASES
)
def test_private_owner_reconstruction_exact_tariffs_and_one_under(
    value_type: type, model_name: str, graph_work: int, tariff: int,
) -> None:
    value = _maximum_owner_value(value_type, model_name)
    assert graph_work * 2 == tariff
    assert semantic_values._exact_worker_execution_reconstruction_work(
        value_type
    ) == tariff
    budget = semantic_values._WorkerExecutionReconstructionBudget(tariff)
    rebuilt, projection = (
        semantic_values._reconstruct_exact_worker_execution_value(
            value, value_type, budget
        )
    )
    assert budget.remaining == 0
    assert type(rebuilt) is value_type and rebuilt is not value
    assert projection == value.to_mapping()
    assert projection is not value.to_mapping()

    one_under = semantic_values._WorkerExecutionReconstructionBudget(tariff - 1)
    with pytest.raises(WorkerExecutionValueError) as caught:
        semantic_values._reconstruct_exact_worker_execution_value(
            value, value_type, one_under
        )
    assert caught.value.reason == "relation_mismatch"
    assert caught.value.field_path == (
        "_reconstruct_exact_worker_execution_value"
    )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


class _ProjectionTraceBudget:
    def __init__(
        self,
        events: list[tuple[str, int]],
        *,
        limit: int = 10_000,
        fail_on_call: int | None = None,
    ) -> None:
        self.remaining = limit
        self.calls = 0
        self._events = events
        self._fail_on_call = fail_on_call

    def consume(self, amount: int = 1) -> None:
        self.calls += 1
        self._events.append(("charge", self.calls))
        if self.calls == self._fail_on_call or amount > self.remaining:
            raise semantic_values._WorkerExecutionReconstructionFailure
        self.remaining -= amount


def _trace_tuple_dereferences(
    value: WorkSpecV1,
    budget: _ProjectionTraceBudget,
) -> tuple[dict[str, object], int] | None:
    raw = semantic_values._raw_worker_execution_projection
    source_lines = Path(semantic_values.__file__).read_text().splitlines()
    start = raw.__code__.co_firstlineno
    end = start + 200
    dereference_lines = {
        number
        for number, line in enumerate(source_lines, 1)
        if start <= number <= end and "sequence[index]" in line
    }
    assert len(dereference_lines) == 1

    def trace(frame, event, _argument):
        if frame.f_code is raw.__code__ and event == "line":
            if frame.f_lineno in dereference_lines:
                budget._events.append(("index", budget.calls))
        return trace

    previous = sys.gettrace()
    sys.settrace(trace)
    try:
        return raw(value, WorkSpecV1, budget)
    finally:
        sys.settrace(previous)


def test_c2a_tuple_members_are_charged_before_each_index_operation() -> None:
    value = _maximum_owner_value(WorkSpecV1, "WorkSpecV1")
    events: list[tuple[str, int]] = []
    budget = _ProjectionTraceBudget(events)
    projection, graph_work = _trace_tuple_dereferences(value, budget)

    assert projection == value.to_mapping()
    assert graph_work == 86
    assert budget.calls == 86
    assert sum(kind == "index" for kind, _call in events) == 67
    for position, (kind, call) in enumerate(events):
        if kind == "index":
            assert position > 0
            assert events[position - 1] == ("charge", call)

    first_tuple_field = next(
        field
        for field in WorkSpecV1._FIELDS
        if semantic_values._worker_execution_tuple_field_limit(WorkSpecV1, field)
        is not None
    )
    first_member_charge = 3 + WorkSpecV1._FIELDS.index(first_tuple_field)
    one_short_events: list[tuple[str, int]] = []
    one_short = _ProjectionTraceBudget(
        one_short_events, fail_on_call=first_member_charge
    )
    with pytest.raises(semantic_values._WorkerExecutionReconstructionFailure):
        _trace_tuple_dereferences(value, one_short)
    assert [event for event in one_short_events if event[0] == "index"] == []


def test_private_owner_reconstruction_recharges_repeated_aliases() -> None:
    mapping = _full_record("WorkSpecV1")
    shared = [f"shared-requirement-{index:02d}" for index in range(32)]
    mapping["requirements"] = list(shared)
    mapping["exclusions"] = list(shared)
    value = WorkSpecV1.from_mapping(
        _reseal_single_digest_record("WorkSpecV1", mapping)
    )
    object.__setattr__(
        value,
        "_exclusions",
        object.__getattribute__(value, "_requirements"),
    )
    rebuilt, projection = semantic_values._reconstruct_exact_worker_execution_value(
        value, WorkSpecV1
    )
    assert rebuilt.to_mapping() == projection
    assert projection["requirements"] == projection["exclusions"]
    assert projection["requirements"] is not projection["exclusions"]


def test_private_owner_reconstruction_excludes_worker_observation() -> None:
    observation = WorkerObservationV1.from_mapping(
        _full_record("WorkerObservationV1")
    )
    with pytest.raises(WorkerExecutionValueError) as caught:
        semantic_values._reconstruct_exact_worker_execution_value(
            observation, WorkerObservationV1
        )
    assert caught.value.reason == "relation_mismatch"
    assert caught.value.__cause__ is None


def _assert_isolated_hostile_unused_arguments(
    constructor: Callable[..., object],
) -> None:
    expected = "WorkerExecutionValueError cannot be constructed directly"
    for form in ("positional", "keyword"):
        invocations: list[str] = []
        marker = f"private-isolated-{form}-marker-25f6a8"
        hostile = _HostileInput(invocations, marker)
        try:
            if form == "positional":
                constructor(
                    "invalid_field_type",
                    "WorkSpecV1.program_ref",
                    hostile,
                )
            else:
                constructor(
                    reason="invalid_field_type",
                    field_path="WorkSpecV1.program_ref",
                    hostile_unused_keyword=hostile,
                )
        except Exception as error:
            rendered = "".join(
                traceback.TracebackException.from_exception(
                    error, capture_locals=False
                ).format()
            )
            assert invocations == [], f"{form} invoked hostile caller behavior"
            assert type(error) is TypeError
            assert str(error) == expected
            assert error.__cause__ is None
            assert error.__context__ is None
            assert marker not in str(error)
            assert marker not in repr(error)
            assert marker not in rendered
        else:
            raise AssertionError(f"{form} direct construction unexpectedly passed")


def _before_blobs() -> dict[str, bytes]:
    return {path: BLOB_FIXTURES[path]["before"] for path in AUTHORIZED_PATHS}


def _after_blobs() -> dict[str, bytes]:
    return {path: BLOB_FIXTURES[path]["after"] for path in AUTHORIZED_PATHS}


def _golden_values() -> tuple[object, ...]:
    return (
        CeilingsV1.from_mapping(
            _full_record("AttemptFenceV1")["aggregate_ceilings"]
        ),
        CapsuleEntryV1.from_mapping(
            _full_record("CandidateCapsuleManifestV1")["entries"][0]
        ),
        WorkSpecV1.from_mapping(_full_record("WorkSpecV1")),
        AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1")),
        EffectFenceV1.from_mapping(_full_record("EffectFenceV1")),
        WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1")),
        DeliveryEnvelopeV1.from_mapping(_full_record("DeliveryEnvelopeV1")),
        WorkerObservationV1.from_mapping(_full_record("WorkerObservationV1")),
        CandidateCapsuleManifestV1.from_mapping(
            _full_record("CandidateCapsuleManifestV1")
        ),
    )


def test_all_mapping_decoders_and_fresh_mapping_encoders() -> None:
    records = (
        (WorkSpecV1, "WorkSpecV1"),
        (AttemptFenceV1, "AttemptFenceV1"),
        (EffectFenceV1, "EffectFenceV1"),
        (WorkerCommandV1, "WorkerCommandV1"),
        (DeliveryEnvelopeV1, "DeliveryEnvelopeV1"),
        (WorkerObservationV1, "WorkerObservationV1"),
        (CandidateCapsuleManifestV1, "CandidateCapsuleManifestV1"),
    )
    for value_type, model_name in records:
        source = _full_record(model_name)
        value = value_type.from_mapping(source)
        first = value.to_mapping()
        second = value.to_mapping()
        assert first == source
        assert second == source
        assert first is not second

    ceiling_source = _full_record("AttemptFenceV1")["aggregate_ceilings"]
    ceilings = CeilingsV1.from_mapping(ceiling_source)
    assert ceilings.to_mapping() == ceiling_source
    entry_source = _full_record("CandidateCapsuleManifestV1")["entries"][0]
    entry = CapsuleEntryV1.from_mapping(entry_source)
    assert entry.to_mapping() == entry_source


def test_embedded_create_apis_compute_blob_and_ceiling_values() -> None:
    ceiling_mapping = _full_record("AttemptFenceV1")["aggregate_ceilings"]
    assert CeilingsV1.create(**ceiling_mapping).to_mapping() == ceiling_mapping

    path = AUTHORIZED_PATHS[0]
    entry = CapsuleEntryV1.create(
        path=path,
        mode="100644",
        before_blob=BLOB_FIXTURES[path]["before"],
        after_blob=BLOB_FIXTURES[path]["after"],
    )
    assert entry.to_mapping() == _full_record("CandidateCapsuleManifestV1")[
        "entries"
    ][0]


def test_work_spec_and_attempt_create_apis_reproduce_golden_records() -> None:
    work = _full_record("WorkSpecV1")
    created_work = WorkSpecV1.create(
        work_spec_ref=work["work_spec_ref"],
        program_ref=work["program_ref"],
        program_version_ref=work["program_version_ref"],
        accepted_intent_revision_ref=work["accepted_intent_revision_ref"],
        work_item_ref=work["work_item_ref"],
        work_item_revision_ref=work["work_item_revision_ref"],
        repository_ref=work["repository_ref"],
        base_git_oid=work["base_git_oid"],
        authorized_paths=work["authorized_paths"],
        objective=work["objective"],
        requirements=work["requirements"],
        exclusions=work["exclusions"],
        validation_requirement_ref=work["validation_requirement_ref"],
        review_requirement_ref=work["review_requirement_ref"],
    )
    assert created_work.to_mapping() == work

    attempt = _full_record("AttemptFenceV1")
    created_attempt = AttemptFenceV1.create(
        attempt_fence_ref=attempt["attempt_fence_ref"],
        parent_standing_grant_ref=attempt["parent_standing_grant_ref"],
        parent_standing_grant_digest=attempt["parent_standing_grant_digest"],
        attempt_authorization_ref=attempt["attempt_authorization_ref"],
        attempt_authorization_digest=attempt["attempt_authorization_digest"],
        program_ref=attempt["program_ref"],
        program_version_ref=attempt["program_version_ref"],
        accepted_intent_revision_ref=attempt["accepted_intent_revision_ref"],
        work_item_ref=attempt["work_item_ref"],
        work_item_revision_ref=attempt["work_item_revision_ref"],
        semantic_attempt_ref=attempt["semantic_attempt_ref"],
        repository_ref=attempt["repository_ref"],
        base_git_oid=attempt["base_git_oid"],
        path_ceiling=attempt["path_ceiling"],
        allowed_effect_classes=attempt["allowed_effect_classes"],
        aggregate_ceilings=CeilingsV1.from_mapping(
            attempt["aggregate_ceilings"]
        ),
        expires_at=attempt["expires_at"],
        global_stop_ref=attempt["global_stop_ref"],
        global_stop_version=attempt["global_stop_version"],
    )
    assert created_attempt.to_mapping() == attempt


def test_author_pair_and_manifest_relation_aware_create_apis() -> None:
    work = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    command_mapping = _full_record("WorkerCommandV1")
    command, fence = create_author_command_and_effect_fence(
        work_spec=work,
        attempt_fence=attempt,
        command_ref=command_mapping["command_ref"],
        effect_intent_ref=command_mapping["effect_intent_ref"],
        effect_fence_ref=command_mapping["effect_fence_ref"],
        candidate_ref=command_mapping["candidate_ref"],
        effect_authorization_ref=command_mapping["effect_authorization_ref"],
        effect_authorization_digest=command_mapping[
            "effect_authorization_digest"
        ],
        expires_at="2030-01-01T00:00:00Z",
        validation_requirement_digest=command_mapping[
            "validation_requirement_digest"
        ],
        review_requirement_digest=command_mapping["review_requirement_digest"],
        capsule_profile_ref=command_mapping["capsule_profile_ref"],
        redaction_profile_ref=command_mapping["redaction_profile_ref"],
        effect_ceilings=CeilingsV1.from_mapping(
            command_mapping["effect_ceilings"]
        ),
    )
    assert command.to_mapping() == command_mapping
    assert fence.to_mapping() == _full_record("EffectFenceV1")
    validate_authoring_relation(
        work_spec=work,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=fence,
    )

    manifest = CandidateCapsuleManifestV1.create(
        before_blobs=_before_blobs(),
        after_blobs=_after_blobs(),
        modes={path: "100644" for path in AUTHORIZED_PATHS},
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=fence,
        capsule_manifest_ref="capsule-manifest.0001",
    )
    assert manifest.to_mapping() == _full_record("CandidateCapsuleManifestV1")


def test_relation_aware_delivery_and_observation_create_apis() -> None:
    command = WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    fence = EffectFenceV1.from_mapping(_effect_fence_for_vector("author"))
    manifest = CandidateCapsuleManifestV1.from_mapping(
        _full_record("CandidateCapsuleManifestV1")
    )
    delivery_source = _delivery_for_vector("author")
    delivery = DeliveryEnvelopeV1.create(
        delivery_attempt_ref=delivery_source["delivery_attempt_ref"],
        adapter_kind=delivery_source["adapter_kind"],
        adapter_safe_correlation_ref=delivery_source[
            "adapter_safe_correlation_ref"
        ],
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=fence,
        effect_fence=fence,
    )
    assert delivery.to_mapping() == delivery_source

    observation_source = _observation_for_vector("author")
    observation = WorkerObservationV1.create(
        observation_ref=observation_source["observation_ref"],
        source_kind=observation_source["source_kind"],
        source_ref=observation_source["source_ref"],
        source_invocation_ref=observation_source["source_invocation_ref"],
        observation_kind=observation_source["observation_kind"],
        outcome=observation_source["outcome"],
        reason_code=observation_source["reason_code"],
        evidence_refs=observation_source["evidence_refs"],
        observed_at=observation_source["observed_at"],
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=fence,
        effect_fence=fence,
        capsule_manifest=manifest,
        before_blobs=_before_blobs(),
        after_blobs=_after_blobs(),
    )
    assert observation.to_mapping() == observation_source


def test_unknown_fields_precede_missing_fields_and_errors_are_bounded() -> None:
    mapping = _full_record("WorkSpecV1")
    mapping.pop("program_ref")
    mapping["unexpected_private_key"] = "private payload"
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(mapping)
    assert caught.value.reason == "unknown_field"
    assert caught.value.field_path == "WorkSpecV1.fields"
    assert str(caught.value) == "unknown_field:WorkSpecV1.fields"
    assert "unexpected_private_key" not in str(caught.value)
    assert "private payload" not in repr(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "payload",
    (
        None,
        [],
        (),
        _DictSubclass(_full_record("WorkSpecV1")),
    ),
)
def test_outer_mapping_requires_exact_builtin_dict(payload: object) -> None:
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(payload)
    assert caught.value.reason == "invalid_field_type"


def test_exact_builtin_scalar_array_and_integer_types_are_required() -> None:
    string_subclass = _full_record("WorkSpecV1")
    string_subclass["program_ref"] = _StringSubclass("program.es-docs")
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(string_subclass)
    assert caught.value.reason == "invalid_field_type"

    list_subclass = _full_record("WorkSpecV1")
    list_subclass["authorized_paths"] = _ListSubclass(AUTHORIZED_PATHS)
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(list_subclass)
    assert caught.value.reason == "invalid_field_type"

    tuple_array = _full_record("WorkSpecV1")
    tuple_array["authorized_paths"] = AUTHORIZED_PATHS
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(tuple_array)
    assert caught.value.reason == "invalid_field_type"

    bool_integer = _full_record("AttemptFenceV1")
    bool_integer["global_stop_version"] = True
    with pytest.raises(WorkerExecutionValueError) as caught:
        AttemptFenceV1.from_mapping(bool_integer)
    assert caught.value.reason == "invalid_field_type"

    integer_subclass = _full_record("AttemptFenceV1")
    integer_subclass["global_stop_version"] = _IntegerSubclass(7)
    with pytest.raises(WorkerExecutionValueError) as caught:
        AttemptFenceV1.from_mapping(integer_subclass)
    assert caught.value.reason == "invalid_field_type"


def test_conditionally_absent_fields_are_not_nullable() -> None:
    observation = _observation_for_vector("cancellation")
    observation["candidate_ref"] = None
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(observation)
    assert caught.value.reason == "invalid_field_type"
    assert caught.value.field_path == "WorkerObservationV1.candidate_ref"

    effect = _effect_fence_for_vector("author")
    effect.pop("portable_capsule_digest")
    with pytest.raises(WorkerExecutionValueError) as caught:
        EffectFenceV1.from_mapping(effect)
    assert caught.value.reason == "missing_field"


def test_value_storage_is_immutable_alias_safe_and_content_free() -> None:
    work_mapping = _full_record("WorkSpecV1")
    work = WorkSpecV1.from_mapping(work_mapping)
    work_mapping["requirements"][0] = "changed"
    assert work.requirements[0] != "changed"
    assert type(work.requirements) is tuple

    manifest_mapping = _full_record("CandidateCapsuleManifestV1")
    manifest = CandidateCapsuleManifestV1.from_mapping(manifest_mapping)
    manifest_mapping["entries"][0]["mode"] = "100755"
    assert manifest.entries[0].mode == "100644"
    assert type(manifest.entries) is tuple

    for value in _golden_values():
        assert not hasattr(value, "__dict__")
        assert repr(value) == f"<{type(value).__name__}>"
        assert str(value) == repr(value)
        assert copy(value) is value
        assert deepcopy(value) is value
        with pytest.raises(AttributeError):
            value.schema_id = "changed"
        with pytest.raises(TypeError):
            hash(value)
        with pytest.raises(TypeError, match="pickling disabled"):
            pickle.dumps(value)


def test_all_value_classes_disable_direct_construction_and_subclassing() -> None:
    value_types = (
        CeilingsV1,
        CapsuleEntryV1,
        WorkSpecV1,
        AttemptFenceV1,
        EffectFenceV1,
        WorkerCommandV1,
        DeliveryEnvelopeV1,
        WorkerObservationV1,
        CandidateCapsuleManifestV1,
    )
    for value_type in value_types:
        with pytest.raises(TypeError, match="construction disabled"):
            value_type()
        with pytest.raises(TypeError, match="subclassing disabled"):
            type(f"Child{value_type.__name__}", (value_type,), {})


def test_worker_execution_value_error_is_catch_only() -> None:
    expected = "WorkerExecutionValueError cannot be constructed directly"
    direct_calls = (
        ((), {}),
        (("invalid_field_type",), {}),
        (("invalid_field_type", "WorkSpecV1.program_ref"), {}),
        (
            (
                "invalid_field_type",
                "WorkSpecV1.program_ref",
                "unexpected-extra",
            ),
            {},
        ),
        (
            (),
            {
                "reason": "invalid_field_type",
                "field_path": "WorkSpecV1.program_ref",
            },
        ),
        (
            (),
            {
                "reason": "invalid_field_type",
                "field_path": "WorkSpecV1.program_ref",
                "unexpected": "extra-keyword",
            },
        ),
    )
    for args, kwargs in direct_calls:
        with pytest.raises(TypeError) as caught:
            WorkerExecutionValueError(*args, **kwargs)
        assert str(caught.value) == expected
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None


def test_worker_execution_value_error_direct_construction_does_not_invoke_caller_behavior() -> None:
    invocations: list[str] = []
    hostile = _HostileInput(invocations, "private-direct-construction-marker")
    expected = "WorkerExecutionValueError cannot be constructed directly"

    for args, kwargs in (
        ((hostile, "WorkSpecV1.program_ref"), {}),
        (("invalid_field_type", hostile), {}),
        ((hostile, hostile), {}),
        ((hostile, hostile, hostile), {}),
        ((), {"reason": hostile, "field_path": hostile}),
        (
            (),
            {
                "reason": hostile,
                "field_path": hostile,
                "unexpected": hostile,
            },
        ),
    ):
        with pytest.raises(TypeError) as caught:
            WorkerExecutionValueError(*args, **kwargs)
        assert str(caught.value) == expected

    assert invocations == []


def test_worker_execution_value_error_isolates_hostile_unused_arguments() -> None:
    _assert_isolated_hostile_unused_arguments(WorkerExecutionValueError)


def test_worker_execution_value_error_tests_reject_late_unused_argument_inspection() -> None:
    expected = "WorkerExecutionValueError cannot be constructed directly"

    def late_positional_inspection(*args: object, **kwargs: object) -> None:
        if (
            len(args) >= 3
            and type(args[0]) is str
            and type(args[1]) is str
            and args[0] == "invalid_field_type"
            and args[1] == "WorkSpecV1.program_ref"
        ):
            format(args[2])
        raise TypeError(expected)

    def late_keyword_inspection(*args: object, **kwargs: object) -> None:
        reason = kwargs.get("reason")
        field_path = kwargs.get("field_path")
        extra_values = tuple(
            value
            for name, value in kwargs.items()
            if name not in ("reason", "field_path")
        )
        if (
            not args
            and type(reason) is str
            and type(field_path) is str
            and reason == "invalid_field_type"
            and field_path == "WorkSpecV1.program_ref"
            and extra_values
        ):
            format(extra_values[0])
        raise TypeError(expected)

    for form, mutant in (
        ("positional", late_positional_inspection),
        ("keyword", late_keyword_inspection),
    ):
        with pytest.raises(
            AssertionError, match=f"{form} invoked hostile caller behavior"
        ):
            _assert_isolated_hostile_unused_arguments(mutant)


def test_worker_execution_value_error_direct_failure_is_content_free() -> None:
    marker = "private-direct-error-marker-94b357"
    with pytest.raises(TypeError) as caught:
        WorkerExecutionValueError(marker, f"field.{marker}")

    rendered = "".join(
        traceback.TracebackException.from_exception(
            caught.value, capture_locals=False
        ).format()
    )
    assert str(caught.value) == (
        "WorkerExecutionValueError cannot be constructed directly"
    )
    assert marker not in str(caught.value)
    assert marker not in repr(caught.value)
    assert marker not in rendered
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_production_created_worker_execution_value_error_preserves_bounded_contract() -> None:
    errors: list[WorkerExecutionValueError] = []

    invalid_type = _full_record("WorkSpecV1")
    invalid_type["program_ref"] = 7
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(invalid_type)
    errors.append(caught.value)
    assert (caught.value.reason, caught.value.field_path, str(caught.value)) == (
        "invalid_field_type",
        "WorkSpecV1.program_ref",
        "invalid_field_type:WorkSpecV1.program_ref",
    )

    work = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    command = WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1"))
    author_fence = EffectFenceV1.from_mapping(_effect_fence_for_vector("author"))
    sibling_mapping = author_fence.to_mapping()
    sibling_mapping["effect_fence_ref"] = "effect-fence.catch-only-sibling.0001"
    sibling = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", sibling_mapping)
    )
    with pytest.raises(WorkerExecutionValueError) as caught:
        validate_authoring_relation(
            work_spec=work,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=sibling,
        )
    errors.append(caught.value)
    assert (caught.value.reason, caught.value.field_path, str(caught.value)) == (
        "relation_mismatch",
        "validate_authoring_relation.effect_fence_ref",
        "relation_mismatch:validate_authoring_relation.effect_fence_ref",
    )

    assert all(isinstance(error, ValueError) for error in errors)
    assert all(error.__cause__ is None for error in errors)
    assert all(error.__context__ is None for error in errors)


@pytest.mark.parametrize(
    "observation_kind,field,value",
    (
        ("not-a-kind", "candidate_ref", 7),
        ("not-a-kind", "capsule_manifest_ref", 7),
        ("not-a-kind", "portable_capsule_digest", 7),
        ("not-a-kind", "process_exit_code", "not-an-integer"),
        ("cancellation_acknowledged", "candidate_ref", 7),
        ("cancellation_acknowledged", "capsule_manifest_ref", 7),
        ("cancellation_acknowledged", "portable_capsule_digest", 7),
        (
            "cancellation_acknowledged",
            "process_exit_code",
            "not-an-integer",
        ),
    ),
)
def test_worker_observation_present_optional_fields_complete_type_phase_before_semantics(
    observation_kind: str, field: str, value: object
) -> None:
    observation = _observation_for_vector("cancellation")
    observation["observation_kind"] = observation_kind
    observation[field] = value

    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(observation)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        f"WorkerObservationV1.{field}",
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("candidate_ref", _StringSubclass("candidate.subclass.0001")),
        (
            "capsule_manifest_ref",
            _StringSubclass("capsule-manifest.subclass.0001"),
        ),
        ("portable_capsule_digest", _StringSubclass("a" * 64)),
        ("process_exit_code", _IntegerSubclass(0)),
        ("process_exit_code", True),
    ),
)
def test_worker_observation_optional_fields_reject_scalar_subclasses_and_bool(
    field: str, value: object
) -> None:
    observation = _observation_for_vector("cancellation")
    observation[field] = value

    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(observation)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        f"WorkerObservationV1.{field}",
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("candidate_ref", "candidate.inapplicable.0001"),
        ("capsule_manifest_ref", "capsule-manifest.inapplicable.0001"),
        ("portable_capsule_digest", "a" * 64),
        ("process_exit_code", 0),
    ),
)
def test_worker_observation_correctly_typed_inapplicable_optional_fields_are_semantic_errors(
    field: str, value: object
) -> None:
    observation = _observation_for_vector("cancellation")
    observation[field] = value

    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(observation)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_value",
        "WorkerObservationV1.conditional_fields",
    )


@pytest.mark.parametrize(
    "field,value,observation_kind,source_kind,outcome",
    (
        ("candidate_ref", "", "candidate_captured", "worker", "captured"),
        (
            "capsule_manifest_ref",
            "",
            "capsule_sealed",
            "capsule_builder",
            "sealed",
        ),
        (
            "portable_capsule_digest",
            "A" * 64,
            "capsule_sealed",
            "capsule_builder",
            "sealed",
        ),
        (
            "process_exit_code",
            256,
            "process_exited",
            "direct_local_adapter",
            "exited",
        ),
    ),
)
def test_worker_observation_correctly_typed_optional_values_reach_field_semantics(
    field: str,
    value: object,
    observation_kind: str,
    source_kind: str,
    outcome: str,
) -> None:
    if observation_kind == "capsule_sealed":
        observation = _observation_for_vector("author")
    else:
        observation = _observation_for_vector("cancellation")
        observation["candidate_ref"] = "candidate.local-check.0001"
        if observation_kind == "process_exited":
            observation.pop("candidate_ref")
    observation["observation_kind"] = observation_kind
    observation["source_kind"] = source_kind
    observation["outcome"] = outcome
    observation[field] = value

    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(observation)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_value",
        f"WorkerObservationV1.{field}",
    )


def test_safe_encoding_failures_suppress_private_exception_context() -> None:
    mapping = _full_record("WorkSpecV1")
    mapping["objective"] = "private\ud800text"
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(mapping)
    assert caught.value.reason == "invalid_field_value"
    assert caught.value.field_path == "WorkSpecV1.canonical_identity"
    assert "private" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_all_from_mapping_paths_complete_type_phase_before_local_semantics() -> None:
    ceilings = deepcopy(_full_record("AttemptFenceV1")["aggregate_ceilings"])
    ceilings["max_active_invocations"] = -1
    ceilings["max_candidate_bytes"] = "wrong-type"
    with pytest.raises(WorkerExecutionValueError) as caught:
        CeilingsV1.from_mapping(ceilings)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "CeilingsV1.max_candidate_bytes",
    )

    entry = deepcopy(_full_record("CandidateCapsuleManifestV1")["entries"][0])
    entry["path"] = ""
    entry["operation"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        CapsuleEntryV1.from_mapping(entry)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "CapsuleEntryV1.operation",
    )

    work = _full_record("WorkSpecV1")
    work["schema_id"] = ""
    work["work_spec_ref"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(work)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "WorkSpecV1.work_spec_ref",
    )

    attempt = _full_record("AttemptFenceV1")
    attempt["schema_id"] = ""
    attempt["attempt_fence_ref"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        AttemptFenceV1.from_mapping(attempt)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "AttemptFenceV1.attempt_fence_ref",
    )

    effect = _full_record("EffectFenceV1")
    effect["schema_id"] = ""
    effect["effect_fence_ref"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        EffectFenceV1.from_mapping(effect)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "EffectFenceV1.effect_fence_ref",
    )

    command = _full_record("WorkerCommandV1")
    command["effect_ceilings"]["max_active_invocations"] = -1
    command["command_ref"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerCommandV1.from_mapping(command)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "WorkerCommandV1.command_ref",
    )

    delivery = _full_record("DeliveryEnvelopeV1")
    delivery["schema_id"] = ""
    delivery["delivery_attempt_ref"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        DeliveryEnvelopeV1.from_mapping(delivery)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "DeliveryEnvelopeV1.delivery_attempt_ref",
    )

    observation = _full_record("WorkerObservationV1")
    observation["observation_kind"] = "not-a-kind"
    observation["source_ref"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(observation)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "WorkerObservationV1.source_ref",
    )

    manifest = _full_record("CandidateCapsuleManifestV1")
    manifest["schema_id"] = ""
    manifest["canonicalization_profile"] = 9
    with pytest.raises(WorkerExecutionValueError) as caught:
        CandidateCapsuleManifestV1.from_mapping(manifest)
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_type",
        "CandidateCapsuleManifestV1.canonicalization_profile",
    )


def test_public_factories_and_validators_prevalidate_before_caller_code_runs() -> None:
    invocations: list[str] = []
    hostile = _HostileInput(invocations, "private-hostile-input")
    work_source = _full_record("WorkSpecV1")
    attempt_source = _full_record("AttemptFenceV1")
    command_source = _full_record("WorkerCommandV1")
    observation_source = _observation_for_vector("author")
    work = WorkSpecV1.from_mapping(work_source)
    attempt = AttemptFenceV1.from_mapping(attempt_source)
    command = WorkerCommandV1.from_mapping(command_source)
    author_fence = EffectFenceV1.from_mapping(_effect_fence_for_vector("author"))
    delivery = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector("author"))
    observation = WorkerObservationV1.from_mapping(observation_source)
    manifest = CandidateCapsuleManifestV1.from_mapping(
        _full_record("CandidateCapsuleManifestV1")
    )
    ceilings = CeilingsV1.from_mapping(command_source["effect_ceilings"])

    hostile_ceilings = deepcopy(attempt_source["aggregate_ceilings"])
    hostile_ceilings["max_candidate_bytes"] = hostile
    with pytest.raises(WorkerExecutionValueError):
        CeilingsV1.create(**hostile_ceilings)

    with pytest.raises(WorkerExecutionValueError):
        CapsuleEntryV1.create(
            path=hostile,
            mode="100644",
            before_blob=b"before",
            after_blob=b"after",
        )

    with pytest.raises(WorkerExecutionValueError):
        WorkSpecV1.create(
            work_spec_ref=hostile,
            program_ref=work_source["program_ref"],
            program_version_ref=work_source["program_version_ref"],
            accepted_intent_revision_ref=work_source[
                "accepted_intent_revision_ref"
            ],
            work_item_ref=work_source["work_item_ref"],
            work_item_revision_ref=work_source["work_item_revision_ref"],
            repository_ref=work_source["repository_ref"],
            base_git_oid=work_source["base_git_oid"],
            authorized_paths=work_source["authorized_paths"],
            objective=work_source["objective"],
            requirements=work_source["requirements"],
            exclusions=work_source["exclusions"],
            validation_requirement_ref=work_source[
                "validation_requirement_ref"
            ],
            review_requirement_ref=work_source["review_requirement_ref"],
        )

    with pytest.raises(WorkerExecutionValueError):
        AttemptFenceV1.create(
            attempt_fence_ref=attempt_source["attempt_fence_ref"],
            parent_standing_grant_ref=attempt_source[
                "parent_standing_grant_ref"
            ],
            parent_standing_grant_digest=attempt_source[
                "parent_standing_grant_digest"
            ],
            attempt_authorization_ref=attempt_source[
                "attempt_authorization_ref"
            ],
            attempt_authorization_digest=attempt_source[
                "attempt_authorization_digest"
            ],
            program_ref=attempt_source["program_ref"],
            program_version_ref=attempt_source["program_version_ref"],
            accepted_intent_revision_ref=attempt_source[
                "accepted_intent_revision_ref"
            ],
            work_item_ref=attempt_source["work_item_ref"],
            work_item_revision_ref=attempt_source["work_item_revision_ref"],
            semantic_attempt_ref=attempt_source["semantic_attempt_ref"],
            repository_ref=attempt_source["repository_ref"],
            base_git_oid=attempt_source["base_git_oid"],
            path_ceiling=attempt_source["path_ceiling"],
            allowed_effect_classes=attempt_source["allowed_effect_classes"],
            aggregate_ceilings=hostile,
            expires_at=attempt_source["expires_at"],
            global_stop_ref=attempt_source["global_stop_ref"],
            global_stop_version=attempt_source["global_stop_version"],
        )

    with pytest.raises(WorkerExecutionValueError):
        DeliveryEnvelopeV1.create(
            delivery_attempt_ref="delivery-attempt.hostile.0001",
            adapter_kind="direct_local_bootstrap",
            adapter_safe_correlation_ref="adapter-correlation.hostile.0001",
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=hostile,
        )

    with pytest.raises(WorkerExecutionValueError):
        CandidateCapsuleManifestV1.create(
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
            modes={path: "100644" for path in AUTHORIZED_PATHS},
            author_command=hostile,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            capsule_manifest_ref="capsule-manifest.hostile.0001",
        )

    with pytest.raises(WorkerExecutionValueError):
        WorkerObservationV1.create(
            observation_ref=observation_source["observation_ref"],
            source_kind=observation_source["source_kind"],
            source_ref=observation_source["source_ref"],
            source_invocation_ref=observation_source["source_invocation_ref"],
            observation_kind=observation_source["observation_kind"],
            outcome=observation_source["outcome"],
            reason_code=observation_source["reason_code"],
            evidence_refs=observation_source["evidence_refs"],
            observed_at=observation_source["observed_at"],
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=hostile,
            capsule_manifest=manifest,
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
        )

    with pytest.raises(WorkerExecutionValueError):
        create_author_command_and_effect_fence(
            work_spec=hostile,
            attempt_fence=attempt,
            command_ref=command_source["command_ref"],
            effect_intent_ref=command_source["effect_intent_ref"],
            effect_fence_ref=command_source["effect_fence_ref"],
            candidate_ref=command_source["candidate_ref"],
            effect_authorization_ref=command_source["effect_authorization_ref"],
            effect_authorization_digest=command_source[
                "effect_authorization_digest"
            ],
            expires_at=author_fence.expires_at,
            validation_requirement_digest=command_source[
                "validation_requirement_digest"
            ],
            review_requirement_digest=command_source[
                "review_requirement_digest"
            ],
            capsule_profile_ref=command_source["capsule_profile_ref"],
            redaction_profile_ref=command_source["redaction_profile_ref"],
            effect_ceilings=ceilings,
        )

    with pytest.raises(WorkerExecutionValueError):
        create_effect_fence(
            attempt_fence=hostile,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence_ref="effect-fence.hostile.0001",
            effect_intent_ref="effect-intent.hostile.0001",
            effect_class="validate_candidate",
            effect_authorization_ref="effect-authorization.hostile.0001",
            effect_authorization_digest="a" * 64,
            effect_ceilings=ceilings,
            expires_at=author_fence.expires_at,
            capsule_manifest=manifest,
        )

    with pytest.raises(WorkerExecutionValueError):
        validate_authoring_relation(
            work_spec=work,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=hostile,
        )
    with pytest.raises(WorkerExecutionValueError):
        validate_effect_relation(
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author_fence,
            effect_fence=hostile,
        )
    with pytest.raises(WorkerExecutionValueError):
        validate_delivery_relation(
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=hostile,
        )
    with pytest.raises(WorkerExecutionValueError):
        validate_redelivery_relation(
            original_delivery=delivery,
            candidate_delivery=hostile,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=author_fence,
        )
    with pytest.raises(WorkerExecutionValueError):
        validate_capsule_manifest_relation(
            capsule_manifest=hostile,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
        )
    with pytest.raises(WorkerExecutionValueError):
        validate_observation_relation(
            observation=observation,
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author_fence,
            effect_fence=hostile,
            capsule_manifest=manifest,
            before_blobs=_before_blobs(),
            after_blobs=_after_blobs(),
        )

    assert invocations == []


def test_invalid_input_errors_and_tracebacks_are_content_free() -> None:
    marker = "private-hostile-marker-7f7427"
    invocations: list[str] = []
    hostile = _HostileInput(invocations, marker)
    work = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    command = WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1"))
    author_fence = EffectFenceV1.from_mapping(_effect_fence_for_vector("author"))

    errors: list[WorkerExecutionValueError] = []
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(hostile)
    errors.append(caught.value)
    with pytest.raises(WorkerExecutionValueError) as caught:
        create_author_command_and_effect_fence(
            work_spec=hostile,
            attempt_fence=attempt,
            command_ref="worker-command.private.0001",
            effect_intent_ref="effect-intent.private.0001",
            effect_fence_ref="effect-fence.private.0001",
            candidate_ref="candidate.private.0001",
            effect_authorization_ref="effect-authorization.private.0001",
            effect_authorization_digest="a" * 64,
            expires_at="2030-01-01T00:00:00Z",
            validation_requirement_digest="b" * 64,
            review_requirement_digest="c" * 64,
            capsule_profile_ref="capsule-profile.private.0001",
            redaction_profile_ref="redaction-profile.private.0001",
            effect_ceilings=command.effect_ceilings,
        )
    errors.append(caught.value)
    with pytest.raises(WorkerExecutionValueError) as caught:
        validate_authoring_relation(
            work_spec=work,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=hostile,
        )
    errors.append(caught.value)

    for error in errors:
        rendered = "".join(
            traceback.TracebackException.from_exception(
                error, capture_locals=False
            ).format()
        )
        assert marker not in str(error)
        assert marker not in repr(error)
        assert marker not in rendered
        assert error.__cause__ is None
        assert error.__context__ is None
    assert invocations == []


def test_record_local_validity_does_not_claim_graph_coherence() -> None:
    work = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    command = WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1"))
    sibling_mapping = _effect_fence_for_vector("author")
    sibling_mapping["effect_fence_ref"] = "effect-fence.sibling.0001"
    sibling = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", sibling_mapping)
    )
    assert sibling.effect_fence_digest == sibling.computed_digest()
    with pytest.raises(WorkerExecutionValueError) as caught:
        validate_authoring_relation(
            work_spec=work,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=sibling,
        )
    assert caught.value.reason == "relation_mismatch"
