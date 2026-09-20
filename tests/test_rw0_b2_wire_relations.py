from __future__ import annotations

import pytest

import ge_nwp_coordinator._rw0_wire_protocol_values as wire
import ge_nwp_coordinator._worker_execution_semantic_values as semantic
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1, CeilingsV1, DeliveryEnvelopeV1, EffectFenceV1,
    WorkerCommandV1, WorkerObservationV1,
)
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireCancellationRequestObservationV1, RW0WireProcessObservationV1,
    RW0WireProtocolError, RW0WireWorkerResultV1, classify_wire_process_result,
    encode_wire_command_frame, encode_wire_result_frame,
    validate_wire_cancellation_request_relation,
    validate_wire_process_observation_relation, validate_wire_result_relation,
)
from tests.c2a_contract_support import (
    _reseal_author_command, _reseal_single_digest_record,
)
from tests.test_rw0_b2_wire_values import (
    REQUEST_SCHEMA, PROCESS_SCHEMA, adapter_observation, graph, process_mapping,
    request_mapping, seal, worker_observation,
)

MAX_INTEGER = 9_223_372_036_854_775_807


def check_request(value, graph_values) -> None:
    command, attempt, author, delivery, cancel, cancel_delivery = graph_values
    validate_wire_cancellation_request_relation(
        request=value, author_command=command, attempt_fence=attempt,
        author_effect_fence=author, target_effect_fence=author,
        target_delivery=delivery, cancellation_effect_fence=cancel,
        cancellation_delivery=cancel_delivery)


def check_process(value, graph_values) -> None:
    command, attempt, author, delivery, _, _ = graph_values
    validate_wire_process_observation_relation(
        observation=value, author_command=command, attempt_fence=attempt,
        author_effect_fence=author, target_effect_fence=author,
        target_delivery=delivery)


def _integer_graph(
    value: int, *, ceiling_field: str | None = None,
    propagate_ceiling: bool = True,
) -> tuple[WorkerCommandV1, AttemptFenceV1, EffectFenceV1, DeliveryEnvelopeV1]:
    base_command, base_attempt, base_author, base_delivery, _, _ = graph()

    def change(mapping: dict[str, object], nested_field: str) -> None:
        if ceiling_field is None:
            mapping["global_stop_version"] = value
            return
        ceilings = mapping[nested_field]
        assert type(ceilings) is dict
        ceilings[ceiling_field] = value

    attempt_mapping = base_attempt.to_mapping()
    change(attempt_mapping, "aggregate_ceilings")
    attempt = AttemptFenceV1.from_mapping(
        _reseal_single_digest_record("AttemptFenceV1", attempt_mapping)
    )

    command_mapping = base_command.to_mapping()
    if ceiling_field is None or propagate_ceiling:
        change(command_mapping, "effect_ceilings")
    command_mapping.update(
        attempt_fence_digest=attempt.attempt_fence_digest,
        effect_fence_digest="0" * 64,
    )
    command_mapping = _reseal_author_command(command_mapping)
    preliminary_command = WorkerCommandV1.from_mapping(command_mapping)

    author_mapping = base_author.to_mapping()
    if ceiling_field is None or propagate_ceiling:
        change(author_mapping, "effect_ceilings")
    author_mapping.update(
        attempt_fence_digest=attempt.attempt_fence_digest,
        command_digest=preliminary_command.command_digest,
    )
    author = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", author_mapping)
    )

    command_mapping["effect_fence_digest"] = author.effect_fence_digest
    command = WorkerCommandV1.from_mapping(command_mapping)
    delivery_mapping = base_delivery.to_mapping()
    delivery_mapping.update(
        command_digest=command.command_digest,
        attempt_fence_digest=attempt.attempt_fence_digest,
        effect_fence_digest=author.effect_fence_digest,
    )
    delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", delivery_mapping)
    )
    return command, attempt, author, delivery


_INTEGER_SPY_SURFACES = (
    "CeilingsV1.from_mapping",
    "CeilingsV1.to_mapping",
    "AttemptFenceV1.from_mapping",
    "AttemptFenceV1.to_mapping",
    "EffectFenceV1.from_mapping",
    "EffectFenceV1.to_mapping",
    "WorkerCommandV1.from_mapping",
    "WorkerCommandV1.to_mapping",
    "DeliveryEnvelopeV1.from_mapping",
    "DeliveryEnvelopeV1.to_mapping",
    "WorkerObservationV1.from_mapping",
    "WorkerObservationV1.to_mapping",
    "owner._canonical_bytes",
    "owner._domain_digest",
    "owner.canonical_identity_bytes",
    "owner.computed_digest",
    "wire._rebuild_safe_c2a",
    "wire._rebuild_c2a",
    "wire._canonical",
    "wire._self_digest",
    "wire._request_digest_impl",
    "wire._process_digest_impl",
    "wire._wire_value_mapping_impl",
    "wire._frame",
)


def _install_integer_spies(monkeypatch, events: list[str]) -> None:
    for cls in (
        CeilingsV1, AttemptFenceV1, EffectFenceV1, WorkerCommandV1,
        DeliveryEnvelopeV1, WorkerObservationV1,
    ):
        original_from_mapping = cls.from_mapping

        def counted_from_mapping(
            owner_cls, payload, *, _original=original_from_mapping,
            _name=cls.__name__,
        ):
            events.append(_name + ".from_mapping")
            return _original(payload)

        monkeypatch.setattr(cls, "from_mapping", classmethod(counted_from_mapping))
        original_to_mapping = cls.to_mapping

        def counted_to_mapping(
            instance, *, _original=original_to_mapping, _name=cls.__name__,
        ):
            events.append(_name + ".to_mapping")
            return _original(instance)

        monkeypatch.setattr(cls, "to_mapping", counted_to_mapping)

    def patch_call(owner, name: str, label: str) -> None:
        original = getattr(owner, name)

        def counted(*args, **kwargs):
            events.append(label)
            return original(*args, **kwargs)

        monkeypatch.setattr(owner, name, counted)

    patch_call(semantic, "_canonical_bytes", "owner._canonical_bytes")
    patch_call(semantic, "_domain_digest", "owner._domain_digest")
    patch_call(
        semantic._TopLevelValue,
        "canonical_identity_bytes",
        "owner.canonical_identity_bytes",
    )
    patch_call(semantic._TopLevelValue, "computed_digest", "owner.computed_digest")
    patch_call(wire, "_rebuild_safe_c2a", "wire._rebuild_safe_c2a")
    patch_call(wire, "_rebuild_c2a", "wire._rebuild_c2a")
    patch_call(wire, "_canonical", "wire._canonical")
    patch_call(wire, "_self_digest", "wire._self_digest")
    patch_call(wire, "_request_digest_impl", "wire._request_digest_impl")
    patch_call(wire, "_process_digest_impl", "wire._process_digest_impl")
    patch_call(wire, "_wire_value_mapping_impl", "wire._wire_value_mapping_impl")
    patch_call(wire, "_frame", "wire._frame")


def _assert_early_integer_rejection(call, value: int, events: list[str]) -> None:
    events.clear()
    with pytest.raises(RW0WireProtocolError) as caught:
        call()
    error = caught.value
    assert error.reason == "invalid_field_value"
    assert error.args == ("RW0WireProtocolError",)
    assert str(error) == repr(error) == "RW0WireProtocolError"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert str(value) not in str(error)
    assert events == []


def _isolated_integer_boundary(
    owner: type[object], field_path: str, value: int,
) -> tuple[str, object, object]:
    command, attempt, author, delivery, _, _ = graph()
    if owner is CeilingsV1:
        target = attempt.aggregate_ceilings
        boundary_name = "encode_wire_command_frame"
    elif owner is AttemptFenceV1:
        target = attempt
        boundary_name = "encode_wire_command_frame"
    elif owner is EffectFenceV1:
        target = author
        boundary_name = "encode_wire_command_frame"
    elif owner is WorkerCommandV1:
        target = command
        boundary_name = "encode_wire_command_frame"
    elif owner is WorkerObservationV1:
        started = worker_observation("worker_started", "observation.integer.started.0001")
        completed = worker_observation(
            "worker_completed", "observation.integer.completed.0001",
        )
        result = RW0WireWorkerResultV1._create((started, completed))
        target = result.observations[0]
        boundary_name = "encode_wire_result_frame"
    else:
        raise AssertionError(f"integer owner has no public Wire boundary: {owner!r}")

    if "." in field_path:
        container_field, field = field_path.split(".", 1)
        target = object.__getattribute__(target, "_" + container_field)
        assert type(target) is CeilingsV1
    else:
        field = field_path
    fields = type(target)._FIELDS
    before = tuple(
        (name, object.__getattribute__(target, "_" + name)) for name in fields
    )
    object.__setattr__(target, "_" + field, value)
    after = tuple(
        (name, object.__getattribute__(target, "_" + name)) for name in fields
    )
    assert [name for (name, old), (_, new) in zip(before, after) if old is not new] == [
        field
    ]

    if owner is WorkerObservationV1:
        def invoke() -> bytes:
            return encode_wire_result_frame(
                result=result,
                command=command,
                delivery=delivery,
                attempt_fence=attempt,
                author_effect_fence=author,
            )
    else:
        def invoke() -> bytes:
            return encode_wire_command_frame(
                command=command,
                delivery=delivery,
                attempt_fence=attempt,
                author_effect_fence=author,
            )
    return boundary_name, invoke, target


def _exercise_valid_integer_boundary(
    monkeypatch, owner: type[object], field_path: str, value: int,
) -> str:
    ceiling_field = (
        field_path
        if owner is CeilingsV1
        else field_path.rsplit(".", 1)[-1] if "." in field_path else None
    )
    if owner in (CeilingsV1, AttemptFenceV1):
        command, attempt, author, delivery = _integer_graph(
            value,
            ceiling_field=ceiling_field,
            propagate_ceiling=False,
        )
        target = attempt.aggregate_ceilings if owner is CeilingsV1 else attempt
        boundary_name = "encode_wire_command_frame"
    elif owner in (EffectFenceV1, WorkerCommandV1):
        command, attempt, author, delivery = _integer_graph(
            value, ceiling_field=ceiling_field,
        )
        target = author if owner is EffectFenceV1 else command
        boundary_name = "encode_wire_command_frame"
    elif owner is WorkerObservationV1:
        command, attempt, author, delivery, _, _ = graph()
        target = WorkerObservationV1.create(
            observation_ref="observation.integer.valid.0001",
            source_kind="direct_local_adapter",
            source_ref="adapter.integer.valid.0001",
            source_invocation_ref="adapter.invocation.integer.valid.0001",
            observation_kind="process_exited",
            outcome="exited",
            reason_code="reason.none",
            evidence_refs=["evidence.integer.valid.0001"],
            observed_at="2026-08-08T18:00:01Z",
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author,
            effect_fence=author,
            process_exit_code=value,
        )
        boundary_name = "classify_wire_process_result"
    else:
        raise AssertionError(f"integer owner has no valid public boundary: {owner!r}")

    original_extract = wire._safe_c2a_extract
    reached: list[tuple[str, str]] = []

    def observed_extract(candidate, expected):
        extracted = original_extract(candidate, expected)
        if candidate is target and expected is owner:
            extracted_value: object = extracted.mapping
            for component in field_path.split("."):
                assert type(extracted_value) is dict
                extracted_value = extracted_value[component]
            assert type(extracted_value) is int
            assert extracted_value == value
            reached.append((owner.__name__, field_path))
        return extracted

    with monkeypatch.context() as positive_patch:
        positive_patch.setattr(wire, "_safe_c2a_extract", observed_extract)
        if owner is WorkerObservationV1:
            classification = classify_wire_process_result(
                command=command,
                delivery=delivery,
                attempt_fence=attempt,
                author_effect_fence=author,
                result=None,
                result_failure=None,
                adapter_observations=(target,),
                request=None,
                process_observations=(),
                cancellation_effect_fence=None,
                cancellation_delivery=None,
            )
            expected = (
                ("unusable", "result_missing")
                if value == 0
                else ("unusable", "process_failed")
            )
            assert (classification.classification, classification.reason) == expected
        else:
            frame = encode_wire_command_frame(
                command=command,
                delivery=delivery,
                attempt_fence=attempt,
                author_effect_fence=author,
            )
            assert type(frame) is bytes
    assert reached == [(owner.__name__, field_path)]
    return boundary_name


def _runtime_integer_paths(value: object) -> tuple[str, ...]:
    paths: list[str] = []
    for field in type(value)._FIELDS:
        item = object.__getattribute__(value, "_" + field)
        if type(item) is int:
            paths.append(field)
        elif type(item) is CeilingsV1:
            paths.extend(
                field + "." + nested
                for nested in CeilingsV1._FIELDS
                if type(object.__getattribute__(item, "_" + nested)) is int
            )
    return tuple(paths)


def test_oversized_c2a_integers_fail_before_owner_or_wire_canonicalization(
    monkeypatch,
) -> None:
    maximum = _integer_graph(MAX_INTEGER)
    assert type(encode_wire_command_frame(
        command=maximum[0], delivery=maximum[3],
        attempt_fence=maximum[1], author_effect_fence=maximum[2],
    )) is bytes

    events: list[str] = []
    _install_integer_spies(monkeypatch, events)
    for value in (MAX_INTEGER + 1, int("9" * 1000)):
        boundary_name, invoke, _ = _isolated_integer_boundary(
            WorkerCommandV1, "global_stop_version", value,
        )
        assert boundary_name == "encode_wire_command_frame"
        _assert_early_integer_rejection(invoke, value, events)


def test_every_reachable_c2a_integer_path_is_isolated_before_owner_or_wire_canonicalization(
    monkeypatch,
) -> None:
    huge = int("9" * 1000)
    oversized = (MAX_INTEGER + 1, huge)
    spies = _INTEGER_SPY_SURFACES
    literal_integer_path_inventory = (
        (CeilingsV1, "max_active_invocations", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_candidate_bytes", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_changed_files", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_cost_microusd", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_cpu_seconds", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_deliveries", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_deployments", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_local_commits", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_memory_bytes", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_merges", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_model_input_tokens", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_model_output_tokens", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_pull_requests", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_pushes", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (CeilingsV1, "max_wall_seconds", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "global_stop_version", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_active_invocations", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_candidate_bytes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_changed_files", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_cost_microusd", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_cpu_seconds", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_deliveries", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_deployments", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_local_commits", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_memory_bytes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_merges", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_model_input_tokens", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_model_output_tokens", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_pull_requests", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_pushes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (AttemptFenceV1, "aggregate_ceilings.max_wall_seconds", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "global_stop_version", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_active_invocations", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_candidate_bytes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_changed_files", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_cost_microusd", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_cpu_seconds", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_deliveries", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_deployments", "encode_wire_command_frame", True, 0, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_local_commits", "encode_wire_command_frame", True, 0, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_memory_bytes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_merges", "encode_wire_command_frame", True, 0, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_model_input_tokens", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_model_output_tokens", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_pull_requests", "encode_wire_command_frame", True, 0, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_pushes", "encode_wire_command_frame", True, 0, oversized, spies),
        (EffectFenceV1, "effect_ceilings.max_wall_seconds", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "global_stop_version", "encode_wire_command_frame", False, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_active_invocations", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_candidate_bytes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_changed_files", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_cost_microusd", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_cpu_seconds", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_deliveries", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_deployments", "encode_wire_command_frame", True, 0, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_local_commits", "encode_wire_command_frame", True, 0, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_memory_bytes", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_merges", "encode_wire_command_frame", True, 0, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_model_input_tokens", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_model_output_tokens", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_pull_requests", "encode_wire_command_frame", True, 0, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_pushes", "encode_wire_command_frame", True, 0, oversized, spies),
        (WorkerCommandV1, "effect_ceilings.max_wall_seconds", "encode_wire_command_frame", True, MAX_INTEGER, oversized, spies),
        (WorkerObservationV1, "process_exit_code", ("encode_wire_result_frame", "classify_wire_process_result"), False, 255, oversized, spies),
    )
    assert len(literal_integer_path_inventory) == 64
    assert all(case[5] == oversized and case[6] == spies for case in literal_integer_path_inventory)
    assert all(type(case[4]) is int for case in literal_integer_path_inventory)

    command, attempt, author, delivery, _, _ = graph()
    direct_ceilings = attempt.aggregate_ceilings
    exit_observation = adapter_observation(
        "process_exited", "observation.integer.inventory.0001", 0,
    )
    runtime_values = {
        CeilingsV1: direct_ceilings,
        AttemptFenceV1: attempt,
        EffectFenceV1: author,
        WorkerCommandV1: command,
        DeliveryEnvelopeV1: delivery,
        WorkerObservationV1: exit_observation,
    }
    literal_paths = {
        owner: frozenset(
            case[1] for case in literal_integer_path_inventory if case[0] is owner
        )
        for owner in runtime_values
    }
    assert literal_paths == {
        owner: frozenset(_runtime_integer_paths(value))
        for owner, value in runtime_values.items()
    }
    assert tuple(case[0] for case in literal_integer_path_inventory).count(CeilingsV1) == 15
    assert tuple(case[0] for case in literal_integer_path_inventory).count(AttemptFenceV1) == 16
    assert tuple(case[0] for case in literal_integer_path_inventory).count(EffectFenceV1) == 16
    assert tuple(case[0] for case in literal_integer_path_inventory).count(WorkerCommandV1) == 16
    assert tuple(case[0] for case in literal_integer_path_inventory).count(DeliveryEnvelopeV1) == 0
    assert tuple(case[0] for case in literal_integer_path_inventory).count(WorkerObservationV1) == 1

    expected_coverage_keys = frozenset(
        (owner.__name__, field_path)
        for owner, field_path, _, _, _, _, _ in literal_integer_path_inventory
    )
    assert len(expected_coverage_keys) == 64
    positive_coverage: dict[tuple[str, str], tuple[int, str]] = {}
    maximum_ceiling_coverage: dict[str, set[tuple[str, str]]] = {}
    for owner, field_path, boundaries, _, valid, _, _ in (
        literal_integer_path_inventory
    ):
        if type(boundaries) is tuple:
            assert boundaries == (
                "encode_wire_result_frame", "classify_wire_process_result",
            )
            positive_boundary = boundaries[1]
        else:
            assert type(boundaries) is str
            positive_boundary = boundaries
        key = (owner.__name__, field_path)
        assert key not in positive_coverage
        observed_boundary = _exercise_valid_integer_boundary(
            monkeypatch, owner, field_path, valid,
        )
        assert observed_boundary == positive_boundary
        positive_coverage[key] = (valid, observed_boundary)
        if valid == MAX_INTEGER and (owner is CeilingsV1 or "." in field_path):
            leaf = field_path.rsplit(".", 1)[-1]
            maximum_ceiling_coverage.setdefault(leaf, set()).add(key)
    assert frozenset(positive_coverage) == expected_coverage_keys
    expected_maximum_ceiling_keys = frozenset(
        (owner.__name__, field_path)
        for owner, field_path, _, _, valid, _, _ in literal_integer_path_inventory
        if valid == MAX_INTEGER and (owner is CeilingsV1 or "." in field_path)
    )
    assert frozenset(maximum_ceiling_coverage) == frozenset(CeilingsV1._FIELDS)
    assert frozenset(
        key for keys in maximum_ceiling_coverage.values() for key in keys
    ) == expected_maximum_ceiling_keys

    broken_command, broken_attempt, broken_author, broken_delivery = _integer_graph(
        MAX_INTEGER,
        ceiling_field="max_active_invocations",
        propagate_ceiling=False,
    )
    broken_key = (CeilingsV1.__name__, "max_active_invocations")
    assert positive_coverage[broken_key] == (
        MAX_INTEGER, "encode_wire_command_frame",
    )
    original_extract = wire._safe_c2a_extract
    broken_control_hits = 0

    def reject_selected_exact_max(candidate, expected):
        nonlocal broken_control_hits
        extracted = original_extract(candidate, expected)
        if (
            expected is CeilingsV1
            and extracted.mapping["max_active_invocations"] == MAX_INTEGER
        ):
            broken_control_hits += 1
            wire._safe_c2a_integer(MAX_INTEGER + 1)
        return extracted

    with monkeypatch.context() as broken_control:
        broken_control.setattr(
            wire, "_safe_c2a_extract", reject_selected_exact_max,
        )
        with pytest.raises(RW0WireProtocolError) as broken:
            encode_wire_command_frame(
                command=broken_command,
                delivery=broken_delivery,
                attempt_fence=broken_attempt,
                author_effect_fence=broken_author,
            )
    assert broken.value.reason == "invalid_field_value"
    assert broken_control_hits == 1

    for exit_code, expected in (
        (-255, ("unusable", "process_failed")),
        (0, ("unusable", "result_missing")),
        (255, ("unusable", "process_failed")),
    ):
        observation = adapter_observation(
            "process_exited", f"observation.integer.exit.{exit_code}.0001", exit_code,
        )
        classification = classify_wire_process_result(
            command=command, delivery=delivery, attempt_fence=attempt,
            author_effect_fence=author, result=None, result_failure=None,
            adapter_observations=(observation,), request=None,
            process_observations=(), cancellation_effect_fence=None,
            cancellation_delivery=None,
        )
        assert (classification.classification, classification.reason) == expected

    events: list[str] = []
    _install_integer_spies(monkeypatch, events)
    negative_maximum_coverage: dict[tuple[str, str], str] = {}
    negative_huge_coverage: dict[tuple[str, str], str] = {}
    for owner, field_path, boundaries, nested, valid, mutations, surfaces in (
        literal_integer_path_inventory
    ):
        assert nested is ("." in field_path)
        assert surfaces == _INTEGER_SPY_SURFACES
        assert type(valid) is int
        expected_boundary = boundaries[0] if type(boundaries) is tuple else boundaries
        key = (owner.__name__, field_path)
        for mutation in mutations:
            boundary_name, invoke, _ = _isolated_integer_boundary(
                owner, field_path, mutation,
            )
            assert boundary_name == expected_boundary
            _assert_early_integer_rejection(invoke, mutation, events)
            ledger = (
                negative_maximum_coverage
                if mutation == MAX_INTEGER + 1
                else negative_huge_coverage
            )
            assert key not in ledger
            ledger[key] = boundary_name
    assert frozenset(negative_maximum_coverage) == expected_coverage_keys
    assert frozenset(negative_huge_coverage) == expected_coverage_keys

    selected_path = "global_stop_version"
    selected_oversized = MAX_INTEGER + 1
    selected_boundary, selected_call, selected_target = _isolated_integer_boundary(
        AttemptFenceV1, selected_path, selected_oversized,
    )
    unrelated_boundary, unrelated_call, unrelated_target = _isolated_integer_boundary(
        EffectFenceV1, "global_stop_version", MAX_INTEGER + 1,
    )
    sentinel_path = "aggregate_ceilings.max_active_invocations"
    (
        sentinel_command,
        sentinel_target,
        sentinel_author,
        sentinel_delivery,
    ) = _integer_graph(
        MAX_INTEGER + 1,
        ceiling_field="max_active_invocations",
        propagate_ceiling=False,
    )

    def sentinel_call() -> bytes:
        return encode_wire_command_frame(
            command=sentinel_command,
            delivery=sentinel_delivery,
            attempt_fence=sentinel_target,
            author_effect_fence=sentinel_author,
        )

    def attempt_integer_at_path(value: AttemptFenceV1, field_path: str) -> int:
        current: object = value
        for component in field_path.split("."):
            current = object.__getattribute__(current, "_" + component)
        assert type(current) is int
        return current

    assert selected_boundary == unrelated_boundary == "encode_wire_command_frame"
    assert type(selected_target) is AttemptFenceV1
    assert type(sentinel_target) is AttemptFenceV1
    assert type(unrelated_target) is EffectFenceV1
    assert sentinel_target is not selected_target
    assert attempt_integer_at_path(sentinel_target, selected_path) <= MAX_INTEGER
    assert tuple(
        path
        for path in _runtime_integer_paths(sentinel_target)
        if attempt_integer_at_path(sentinel_target, path) > MAX_INTEGER
    ) == (sentinel_path,)
    original_extract = wire._safe_c2a_extract
    original_integer = wire._safe_c2a_integer
    attempt_inventory_paths = tuple(
        field_path
        for owner, field_path, _, _, _, _, _ in literal_integer_path_inventory
        if owner is AttemptFenceV1
    )
    selected_guard_order = tuple(
        path for path in attempt_inventory_paths if path != selected_path
    ) + (selected_path,)
    assert selected_guard_order == _runtime_integer_paths(selected_target)
    observed_attempt_guard_paths: list[str] = []
    delegated_attempt_guard_paths: list[str] = []
    selected_bypass_count = 0
    sentinel_real_body_entries = 0
    sentinel_real_body_rejections = 0

    def observed_real_attempt_integer(candidate):
        nonlocal sentinel_real_body_entries, sentinel_real_body_rejections
        sentinel_real_body_entries += 1
        try:
            return original_integer(candidate)
        except wire._WireFailure:
            sentinel_real_body_rejections += 1
            raise

    sentinel_integer_operation = observed_real_attempt_integer
    unrelated_effect_integer_operation = original_integer

    def selective_extract(value, expected):
        nonlocal selected_bypass_count
        if value is selected_target and expected is AttemptFenceV1:
            def selected_integer(candidate):
                nonlocal selected_bypass_count
                index = len(observed_attempt_guard_paths)
                assert index < len(selected_guard_order)
                field_path = selected_guard_order[index]
                observed_attempt_guard_paths.append(field_path)
                if (
                    field_path == selected_path
                    and type(candidate) is int
                    and candidate == selected_oversized
                ):
                    selected_bypass_count += 1
                    return candidate
                delegated_attempt_guard_paths.append(field_path)
                return original_integer(candidate)

            wire._safe_c2a_integer = selected_integer
            try:
                return original_extract(value, expected)
            finally:
                wire._safe_c2a_integer = original_integer
        if value is sentinel_target and expected is AttemptFenceV1:
            wire._safe_c2a_integer = sentinel_integer_operation
            try:
                return original_extract(value, expected)
            finally:
                wire._safe_c2a_integer = original_integer
        if value is unrelated_target and expected is EffectFenceV1:
            wire._safe_c2a_integer = unrelated_effect_integer_operation
            try:
                return original_extract(value, expected)
            finally:
                wire._safe_c2a_integer = original_integer
        return original_extract(value, expected)

    def sealed_invalid_field_value(
        error: RW0WireProtocolError | None, value: int,
    ) -> bool:
        return (
            type(error) is RW0WireProtocolError
            and error.reason == "invalid_field_value"
            and error.args == ("RW0WireProtocolError",)
            and str(error) == repr(error) == "RW0WireProtocolError"
            and error.__cause__ is None
            and error.__context__ is None
            and str(value) not in str(error)
        )

    def assert_non_selected_attempt_sentinel() -> None:
        nonlocal sentinel_real_body_entries, sentinel_real_body_rejections
        sentinel_real_body_entries = 0
        sentinel_real_body_rejections = 0
        bypasses_before = selected_bypass_count
        observed_before = tuple(observed_attempt_guard_paths)
        delegated_before = tuple(delegated_attempt_guard_paths)
        events.clear()
        error: RW0WireProtocolError | None = None
        try:
            sentinel_call()
        except RW0WireProtocolError as caught:
            error = caught
        if not (
            sealed_invalid_field_value(error, MAX_INTEGER + 1)
            and sentinel_real_body_entries == 1
            and sentinel_real_body_rejections == 1
            and selected_bypass_count == bypasses_before
            and tuple(observed_attempt_guard_paths) == observed_before
            and tuple(delegated_attempt_guard_paths) == delegated_before
            and events == []
        ):
            raise AssertionError(
                "non_selected_attempt_integer_guard_not_enforced"
            ) from None

    def assert_unrelated_effect_guard() -> None:
        bypasses_before = selected_bypass_count
        observed_before = tuple(observed_attempt_guard_paths)
        delegated_before = tuple(delegated_attempt_guard_paths)
        events.clear()
        error: RW0WireProtocolError | None = None
        try:
            unrelated_call()
        except RW0WireProtocolError as caught:
            error = caught
        if not (
            sealed_invalid_field_value(error, MAX_INTEGER + 1)
            and selected_bypass_count == bypasses_before
            and tuple(observed_attempt_guard_paths) == observed_before
            and tuple(delegated_attempt_guard_paths) == delegated_before
            and events == []
        ):
            raise AssertionError(
                "unrelated_effect_integer_guard_not_enforced"
            ) from None

    monkeypatch.setattr(wire, "_safe_c2a_extract", selective_extract)
    events.clear()
    with pytest.raises(RW0WireProtocolError) as selected:
        selected_call()
    assert selected.value.reason == "invalid_field_value"
    assert tuple(observed_attempt_guard_paths) == selected_guard_order
    assert tuple(delegated_attempt_guard_paths) == selected_guard_order[:-1]
    assert selected_bypass_count == 1
    assert len(delegated_attempt_guard_paths) == 15
    assert events.count("AttemptFenceV1.from_mapping") == 1

    assert_non_selected_attempt_sentinel()

    class_wide_attempt_bypass_calls = 0

    def bypass_all_attempt_integers(candidate):
        nonlocal class_wide_attempt_bypass_calls
        class_wide_attempt_bypass_calls += 1
        return candidate

    sentinel_integer_operation = bypass_all_attempt_integers
    with pytest.raises(
        AssertionError,
        match="^non_selected_attempt_integer_guard_not_enforced$",
    ) as attempt_mutant:
        assert_non_selected_attempt_sentinel()
    assert str(attempt_mutant.value) == (
        "non_selected_attempt_integer_guard_not_enforced"
    )
    assert class_wide_attempt_bypass_calls == 16
    assert sentinel_real_body_entries == sentinel_real_body_rejections == 0
    assert events.count("AttemptFenceV1.from_mapping") == 1
    assert any(event in events for event in (
        "owner._canonical_bytes", "owner._domain_digest",
        "wire._canonical", "wire._frame",
    ))

    sentinel_integer_operation = observed_real_attempt_integer
    assert_non_selected_attempt_sentinel()
    assert_unrelated_effect_guard()

    unrelated_effect_bypass_calls = 0

    def bypass_all_unrelated_effect_integers(candidate):
        nonlocal unrelated_effect_bypass_calls
        unrelated_effect_bypass_calls += 1
        return candidate

    unrelated_effect_integer_operation = bypass_all_unrelated_effect_integers
    assert_non_selected_attempt_sentinel()
    with pytest.raises(
        AssertionError,
        match="^unrelated_effect_integer_guard_not_enforced$",
    ) as effect_mutant:
        assert_unrelated_effect_guard()
    assert str(effect_mutant.value) == (
        "unrelated_effect_integer_guard_not_enforced"
    )
    assert unrelated_effect_bypass_calls == 16
    assert events.count("EffectFenceV1.from_mapping") == 1
    assert any(event in events for event in (
        "owner._canonical_bytes", "owner._domain_digest",
        "wire._canonical", "wire._frame",
    ))

    unrelated_effect_integer_operation = original_integer
    assert_unrelated_effect_guard()


def test_request_supervisor_and_execution_substrate_route_sources() -> None:
    local = graph()
    check_request(RW0WireCancellationRequestObservationV1.from_mapping(request_mapping()), local)
    command, attempt, author, delivery, cancel, _ = local
    es_delivery = DeliveryEnvelopeV1.create(
        delivery_attempt_ref="delivery-attempt.cancellation.es.0001",
        adapter_kind="execution_substrate",
        adapter_safe_correlation_ref="adapter-correlation.cancellation.es.0001",
        author_command=command, attempt_fence=attempt,
        author_effect_fence=author, effect_fence=cancel,
        cancellation_target=author)
    es_graph = (command, attempt, author, delivery, cancel, es_delivery)
    mapping = request_mapping("execution_substrate")
    mapping["cancellation_delivery_attempt_ref"] = es_delivery.delivery_attempt_ref
    mapping["cancellation_delivery_envelope_digest"] = es_delivery.delivery_envelope_digest
    value = RW0WireCancellationRequestObservationV1.from_mapping(
        seal(mapping, REQUEST_SCHEMA + ".identity", "request_observation_digest"))
    check_request(value, es_graph)
    wrong_source = RW0WireCancellationRequestObservationV1.from_mapping(
        request_mapping("execution_substrate"))
    with pytest.raises(RW0WireProtocolError) as caught:
        check_request(wrong_source, local)
    assert caught.value.reason == "relation_mismatch"
    changed = request_mapping();changed["source_kind"] = "direct_local_adapter"
    with pytest.raises(RW0WireProtocolError) as caught:
        RW0WireCancellationRequestObservationV1.from_mapping(
            seal(changed, REQUEST_SCHEMA + ".identity", "request_observation_digest"))
    assert caught.value.reason == "invalid_field_value"


@pytest.mark.parametrize("field", (
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "candidate_ref", "command_ref", "command_digest", "attempt_fence_ref",
    "attempt_fence_digest", "cancellation_effect_intent_ref",
    "cancellation_effect_fence_ref", "cancellation_effect_fence_digest",
    "cancellation_delivery_attempt_ref", "cancellation_delivery_envelope_digest",
    "target_effect_intent_ref", "target_effect_fence_ref",
    "target_effect_fence_digest", "target_delivery_attempt_ref",
    "target_delivery_envelope_digest",
))
def test_every_request_coordinate_is_bound(field: str) -> None:
    mapping = request_mapping()
    mapping[field] = ("a" * 64 if field.endswith("_digest") else "other.safe.0001")
    value = RW0WireCancellationRequestObservationV1.from_mapping(
        seal(mapping, REQUEST_SCHEMA + ".identity", "request_observation_digest"))
    with pytest.raises(RW0WireProtocolError) as caught:
        check_request(value, graph())
    assert caught.value.reason == "relation_mismatch"


@pytest.mark.parametrize("kind,source", (
    ("signal_delivered", "supervisor"), ("signal_delivered", "operating_system"),
    ("resource_limit_exceeded", "supervisor"),
    ("resource_limit_exceeded", "operating_system"),
))
def test_process_claim_kinds_and_sources(kind: str, source: str) -> None:
    value = RW0WireProcessObservationV1.from_mapping(process_mapping(kind, source))
    check_process(value, graph())


@pytest.mark.parametrize("field", (
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "candidate_ref", "command_ref", "command_digest", "attempt_fence_ref",
    "attempt_fence_digest", "effect_intent_ref", "effect_fence_ref",
    "effect_fence_digest", "delivery_attempt_ref", "delivery_envelope_digest",
))
def test_every_process_coordinate_is_bound(field: str) -> None:
    mapping = process_mapping()
    mapping[field] = ("a" * 64 if field.endswith("_digest") else "other.safe.0001")
    value = RW0WireProcessObservationV1.from_mapping(
        seal(mapping, PROCESS_SCHEMA + ".identity", "process_observation_digest"))
    with pytest.raises(RW0WireProtocolError) as caught:
        check_process(value, graph())
    assert caught.value.reason == "relation_mismatch"


def test_worker_result_source_invocation_candidate_and_unique_refs() -> None:
    command, attempt, author, delivery, _, _ = graph()
    started = worker_observation("worker_started", "observation.started.0001")
    captured = worker_observation("candidate_captured", "observation.captured.0001")
    completed = worker_observation("worker_completed", "observation.completed.0001")
    def relation(result):
        validate_wire_result_relation(result=result, command=command,
            delivery=delivery, attempt_fence=attempt, author_effect_fence=author)
    relation(RW0WireWorkerResultV1._create((started, captured, completed)))
    for field, value in (
        ("source_ref", "other.worker.0001"),
        ("source_invocation_ref", "other.invocation.0001"),
        ("candidate_ref", "other.candidate.0001"),
        ("observation_ref", started.observation_ref),
    ):
        mapping = captured.to_mapping()
        mapping[field] = value
        changed = WorkerObservationV1.from_mapping(
            _reseal_single_digest_record("WorkerObservationV1", mapping))
        with pytest.raises(RW0WireProtocolError) as caught:
            relation(RW0WireWorkerResultV1._create((started, changed, completed)))
        assert caught.value.reason == "relation_mismatch"


def test_request_and_response_do_not_require_source_claim_equality() -> None:
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    request = RW0WireCancellationRequestObservationV1.from_mapping(request_mapping())
    check_request(request, (command, attempt, author, delivery, cancel, cancel_delivery))
    assert request.source_kind == "supervisor"
    assert request.source_ref != "adapter.safe.0001"
    assert request.source_invocation_ref != "adapter.invocation.safe.0001"


def test_command_observation_target_and_cancellation_c2a_relations_are_causal(
    monkeypatch,
) -> None:
    command, attempt, author, delivery, cancel, cancel_delivery = graph()

    changed_delivery_mapping = delivery.to_mapping()
    changed_delivery_mapping["program_ref"] = "program.c2a-only-mismatch"
    changed_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", changed_delivery_mapping))
    with pytest.raises(RW0WireProtocolError) as caught:
        encode_wire_command_frame(
            command=command, delivery=changed_delivery,
            attempt_fence=attempt, author_effect_fence=author)
    assert caught.value.reason == "relation_mismatch"

    started = worker_observation("worker_started", "observation.causal.started.0001")
    completed = worker_observation("worker_completed", "observation.causal.completed.0001")
    changed_observation_mapping = completed.to_mapping()
    changed_observation_mapping["program_ref"] = "program.c2a-only-mismatch"
    changed_observation = WorkerObservationV1.from_mapping(
        _reseal_single_digest_record("WorkerObservationV1", changed_observation_mapping))
    changed_result = RW0WireWorkerResultV1._create((started, changed_observation))
    with pytest.raises(RW0WireProtocolError) as caught:
        validate_wire_result_relation(
            result=changed_result, command=command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=author)
    assert caught.value.reason == "relation_mismatch"

    changed_target_mapping = delivery.to_mapping()
    changed_target_mapping["program_ref"] = "program.target-c2a-only-mismatch"
    changed_target = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", changed_target_mapping))
    target_request_mapping = request_mapping()
    target_request_mapping["target_delivery_envelope_digest"] = (
        changed_target.delivery_envelope_digest
    )
    target_request = RW0WireCancellationRequestObservationV1.from_mapping(
        seal(target_request_mapping, REQUEST_SCHEMA + ".identity",
             "request_observation_digest"))
    with pytest.raises(RW0WireProtocolError) as caught:
        check_request(
            target_request,
            (command, attempt, author, changed_target, cancel, cancel_delivery),
        )
    assert caught.value.reason == "relation_mismatch"

    changed_cancel_mapping = cancel_delivery.to_mapping()
    changed_cancel_mapping["program_ref"] = "program.cancel-c2a-only-mismatch"
    changed_cancel_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", changed_cancel_mapping))
    cancel_request_mapping = request_mapping()
    cancel_request_mapping["cancellation_delivery_envelope_digest"] = (
        changed_cancel_delivery.delivery_envelope_digest
    )
    cancel_request = RW0WireCancellationRequestObservationV1.from_mapping(
        seal(cancel_request_mapping, REQUEST_SCHEMA + ".identity",
             "request_observation_digest"))
    with pytest.raises(RW0WireProtocolError) as caught:
        check_request(
            cancel_request,
            (command, attempt, author, delivery, cancel, changed_cancel_delivery),
        )
    assert caught.value.reason == "relation_mismatch"

    monkeypatch.setattr(wire, "validate_delivery_relation", lambda **kwargs: None)
    encode_wire_command_frame(
        command=command, delivery=changed_delivery,
        attempt_fence=attempt, author_effect_fence=author)
    check_request(
        target_request,
        (command, attempt, author, changed_target, cancel, cancel_delivery),
    )
    check_request(
        cancel_request,
        (command, attempt, author, delivery, cancel, changed_cancel_delivery),
    )

    monkeypatch.setattr(wire, "validate_observation_relation", lambda **kwargs: None)
    validate_wire_result_relation(
        result=changed_result, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)
    encode_wire_result_frame(
        result=changed_result, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)


def test_bypass_constructed_and_tampered_wire_values_fail_closed_at_relations() -> None:
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    bypass_request = object.__new__(RW0WireCancellationRequestObservationV1)
    with pytest.raises(RW0WireProtocolError) as caught:
        check_request(
            bypass_request,
            (command, attempt, author, delivery, cancel, cancel_delivery),
        )
    assert caught.value.reason == "invalid_field_value"
    assert caught.value.__cause__ is caught.value.__context__ is None

    bypass_process = object.__new__(RW0WireProcessObservationV1)
    with pytest.raises(RW0WireProtocolError) as caught:
        check_process(bypass_process, graph())
    assert caught.value.reason == "invalid_field_value"
    assert caught.value.__cause__ is caught.value.__context__ is None

    bypass_result = object.__new__(RW0WireWorkerResultV1)
    with pytest.raises(RW0WireProtocolError) as caught:
        validate_wire_result_relation(
            result=bypass_result, command=command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=author)
    assert caught.value.reason == "invalid_field_value"
    assert caught.value.__cause__ is caught.value.__context__ is None
    with pytest.raises(RW0WireProtocolError) as caught:
        encode_wire_result_frame(
            result=bypass_result, command=command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=author)
    assert caught.value.reason == "invalid_field_value"
    assert caught.value.__cause__ is caught.value.__context__ is None

    request = RW0WireCancellationRequestObservationV1.from_mapping(request_mapping())
    object.__setattr__(request, "_request_observation_digest", "0" * 64)
    with pytest.raises(RW0WireProtocolError) as caught:
        check_request(
            request,
            (command, attempt, author, delivery, cancel, cancel_delivery),
        )
    assert caught.value.reason == "invalid_field_value"

    process = RW0WireProcessObservationV1.from_mapping(process_mapping())
    object.__setattr__(process, "_process_observation_digest", "0" * 64)
    with pytest.raises(RW0WireProtocolError) as caught:
        check_process(process, graph())
    assert caught.value.reason == "invalid_field_value"


def test_c2a_bypass_is_sealed_across_every_wire_relation_encoder_and_classifier() -> None:
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    request = RW0WireCancellationRequestObservationV1.from_mapping(
        request_mapping())
    process = RW0WireProcessObservationV1.from_mapping(process_mapping())
    result = RW0WireWorkerResultV1._create((
        worker_observation(
            "worker_started", "observation.boundary.started.0001"),
        worker_observation(
            "worker_completed", "observation.boundary.completed.0001"),
    ))
    bypass = object.__new__(WorkerCommandV1)
    calls = (
        lambda: encode_wire_command_frame(
            command=bypass, delivery=delivery, attempt_fence=attempt,
            author_effect_fence=author),
        lambda: encode_wire_result_frame(
            result=result, command=bypass, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=author),
        lambda: validate_wire_result_relation(
            result=result, command=bypass, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=author),
        lambda: validate_wire_cancellation_request_relation(
            request=request, author_command=bypass, attempt_fence=attempt,
            author_effect_fence=author, target_effect_fence=author,
            target_delivery=delivery, cancellation_effect_fence=cancel,
            cancellation_delivery=cancel_delivery),
        lambda: validate_wire_process_observation_relation(
            observation=process, author_command=bypass,
            attempt_fence=attempt, author_effect_fence=author,
            target_effect_fence=author, target_delivery=delivery),
    )
    for call in calls:
        with pytest.raises(RW0WireProtocolError) as caught:
            call()
        assert caught.value.reason == "invalid_field_value"
        assert caught.value.args == ("RW0WireProtocolError",)
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None

    classified = classify_wire_process_result(
        command=bypass, delivery=delivery, attempt_fence=attempt,
        author_effect_fence=author, result=result, result_failure=None,
        adapter_observations=(), request=None, process_observations=(),
        cancellation_effect_fence=None, cancellation_delivery=None,
    )
    assert (classified.classification, classified.reason) == (
        "invalid", "invalid_input")
