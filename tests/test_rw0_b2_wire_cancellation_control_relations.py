from __future__ import annotations

import pytest

import ge_nwp_coordinator._rw0_wire_protocol_values as wire
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    DeliveryEnvelopeV1,
)
from tests.c2a_contract_support import _reseal_single_digest_record
from tests.test_rw0_b2_wire_cancellation_control_values import (
    ControlGraph,
    capsule_operand,
    control_graph,
    make_adapter,
    make_process,
    make_request,
)


TARGET_CLASSES = ("author_candidate", "validate_candidate", "review_candidate")
ROUTES = ("direct_local_bootstrap", "execution_substrate")


def _request_call(graph: ControlGraph, request=None) -> None:
    wire.validate_wire_exact_current_cancellation_request_relation(
        request=make_request(graph) if request is None else request,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        target_effect_fence=graph.target,
        target_delivery=graph.target_delivery,
        cancellation_effect_fence=graph.cancel,
        cancellation_delivery=graph.cancel_delivery,
        **capsule_operand(graph),
    )


def _process_call(graph: ControlGraph, observation=None) -> None:
    wire.validate_wire_exact_current_process_observation_relation(
        observation=(
            make_process(graph, "signal_delivered")
            if observation is None
            else observation
        ),
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        target_effect_fence=graph.target,
        target_delivery=graph.target_delivery,
        **capsule_operand(graph),
    )


def _response_call(graph: ControlGraph, response=None, request=None) -> None:
    wire.validate_wire_exact_current_cancellation_response_relation(
        response=(
            make_adapter(graph, "cancellation_acknowledged")
            if response is None
            else response
        ),
        request=make_request(graph) if request is None else request,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        target_effect_fence=graph.target,
        target_delivery=graph.target_delivery,
        cancellation_effect_fence=graph.cancel,
        cancellation_delivery=graph.cancel_delivery,
        **capsule_operand(graph),
    )


def _assert_error(call, reason: str) -> wire.RW0WireProtocolError:
    with pytest.raises(wire.RW0WireProtocolError) as caught:
        call()
    error = caught.value
    assert error.reason == reason
    assert error.args == ("RW0WireProtocolError",)
    assert str(error) == repr(error) == "RW0WireProtocolError"
    assert error.__cause__ is None
    assert error.__context__ is None
    return error


def test_request_relation_accepts_complete_target_and_route_matrix(monkeypatch) -> None:
    calls: list[str] = []
    owner = wire.validate_delivery_relation

    def observed(**kwargs):
        calls.append(kwargs["effect_fence"].effect_class)
        return owner(**kwargs)

    monkeypatch.setattr(wire, "validate_delivery_relation", observed)
    for target_class in TARGET_CLASSES:
        for route in ROUTES:
            _request_call(control_graph(target_class, route))
    assert calls == [
        "author_candidate", "cancel_effect",
        "author_candidate", "cancel_effect",
        "validate_candidate", "cancel_effect",
        "validate_candidate", "cancel_effect",
        "review_candidate", "cancel_effect",
        "review_candidate", "cancel_effect",
    ]


def test_process_relation_accepts_complete_target_event_source_matrix() -> None:
    for target_class in TARGET_CLASSES:
        for route in ROUTES:
            graph = control_graph(target_class, route)
            for event_kind in ("resource_limit_exceeded", "signal_delivered"):
                for source_kind in ("supervisor", "operating_system"):
                    observation = make_process(
                        graph,
                        event_kind,
                        ref=(
                            f"process.{target_class}.{route}.{event_kind}."
                            f"{source_kind}.0001"
                        ).replace("_", "-"),
                        source_kind=source_kind,
                    )
                    _process_call(graph, observation)


def test_response_relation_accepts_acknowledgement_and_rejection_matrix(monkeypatch) -> None:
    roles: list[str] = []
    owner = wire.validate_observation_relation

    def observed(**kwargs):
        roles.append(kwargs["observation"].observation_kind)
        return owner(**kwargs)

    monkeypatch.setattr(wire, "validate_observation_relation", observed)
    for target_class in TARGET_CLASSES:
        for route in ROUTES:
            graph = control_graph(target_class, route)
            request = make_request(graph)
            for role in ("cancellation_acknowledged", "cancellation_rejected"):
                response = make_adapter(
                    graph,
                    role,
                    ref=(
                        f"response.{target_class}.{route}.{role}.0001"
                    ).replace("_", "-"),
                )
                _response_call(graph, response, request)
    assert roles == [
        role
        for _target in TARGET_CLASSES
        for _route in ROUTES
        for role in ("cancellation_acknowledged", "cancellation_rejected")
    ]


def test_capsule_branch_is_exact(monkeypatch) -> None:
    author = control_graph("author_candidate")
    _request_call(author)
    common = {
        "request": make_request(author),
        "author_command": author.command,
        "attempt_fence": author.attempt,
        "author_effect_fence": author.author,
        "target_effect_fence": author.target,
        "target_delivery": author.target_delivery,
        "cancellation_effect_fence": author.cancel,
        "cancellation_delivery": author.cancel_delivery,
    }
    _assert_error(
        lambda: wire.validate_wire_exact_current_cancellation_request_relation(
            **common, target_capsule_manifest=None
        ),
        "invalid_field_type",
    )
    _assert_error(
        lambda: wire.validate_wire_exact_current_cancellation_request_relation(
            **common, target_capsule_manifest=author.manifest
        ),
        "relation_mismatch",
    )
    for target_class in ("validate_candidate", "review_candidate"):
        graph = control_graph(target_class)
        _request_call(graph)
        _assert_error(
            lambda graph=graph: wire.validate_wire_exact_current_cancellation_request_relation(
                request=make_request(graph),
                author_command=graph.command,
                attempt_fence=graph.attempt,
                author_effect_fence=graph.author,
                target_effect_fence=graph.target,
                target_delivery=graph.target_delivery,
                cancellation_effect_fence=graph.cancel,
                cancellation_delivery=graph.cancel_delivery,
            ),
            "relation_mismatch",
        )
    graph = control_graph("validate_candidate")
    owner_reconstruct = wire._reconstruct_exact_worker_execution_value
    reconstructed: list[object] = []

    def counted_manifest(value, expected, budget=None):
        reconstructed.append(value)
        return owner_reconstruct(value, expected, budget)

    monkeypatch.setattr(
        wire, "_reconstruct_exact_worker_execution_value", counted_manifest
    )
    _request_call(graph)
    assert reconstructed == [graph.manifest]


def test_request_source_is_bound_only_to_cancellation_delivery_route() -> None:
    for route, correct, wrong in (
        ("direct_local_bootstrap", "supervisor", "execution_substrate"),
        ("execution_substrate", "execution_substrate", "supervisor"),
    ):
        graph = control_graph("author_candidate", route)
        request = make_request(graph, source_kind=correct)
        _request_call(graph, request)
        _response_call(
            graph,
            make_adapter(graph, "cancellation_acknowledged"),
            request,
        )
        _assert_error(
            lambda graph=graph, wrong=wrong: _request_call(
                graph, make_request(graph, source_kind=wrong)
            ),
            "relation_mismatch",
        )


def test_target_cancel_swaps_cross_attempts_and_sibling_graphs_fail(monkeypatch) -> None:
    graph = control_graph("author_candidate")
    request = make_request(graph)
    _assert_error(
        lambda: wire.validate_wire_exact_current_cancellation_request_relation(
            request=request,
            author_command=graph.command,
            attempt_fence=graph.attempt,
            author_effect_fence=graph.author,
            target_effect_fence=graph.target,
            target_delivery=graph.cancel_delivery,
            cancellation_effect_fence=graph.cancel,
            cancellation_delivery=graph.target_delivery,
        ),
        "relation_mismatch",
    )
    alternate_mapping = graph.target_delivery.to_mapping()
    alternate_mapping["adapter_safe_correlation_ref"] = (
        "adapter-correlation.reconstructed-alternate.0001"
    )
    alternate_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", alternate_mapping)
    )
    owner_rebuild = wire._rebuild_c2a

    def substitute_reconstructed(candidate, expected):
        if candidate is graph.target_delivery and expected is DeliveryEnvelopeV1:
            return alternate_delivery
        return owner_rebuild(candidate, expected)

    monkeypatch.setattr(wire, "_rebuild_c2a", substitute_reconstructed)
    _assert_error(lambda: _request_call(graph, request), "relation_mismatch")
    attempt_mapping = graph.attempt.to_mapping()
    attempt_mapping["semantic_attempt_ref"] = "semantic-attempt.cross.0002"
    cross_attempt = AttemptFenceV1.from_mapping(
        _reseal_single_digest_record("AttemptFenceV1", attempt_mapping)
    )
    _assert_error(
        lambda: wire.validate_wire_exact_current_cancellation_request_relation(
            request=request,
            author_command=graph.command,
            attempt_fence=cross_attempt,
            author_effect_fence=graph.author,
            target_effect_fence=graph.target,
            target_delivery=graph.target_delivery,
            cancellation_effect_fence=graph.cancel,
            cancellation_delivery=graph.cancel_delivery,
        ),
        "relation_mismatch",
    )
    sibling = control_graph("review_candidate")
    _assert_error(
        lambda: wire.validate_wire_exact_current_cancellation_request_relation(
            request=request,
            author_command=sibling.command,
            attempt_fence=sibling.attempt,
            author_effect_fence=sibling.author,
            target_effect_fence=sibling.target,
            target_delivery=sibling.target_delivery,
            cancellation_effect_fence=sibling.cancel,
            cancellation_delivery=sibling.cancel_delivery,
            target_capsule_manifest=sibling.manifest,
        ),
        "relation_mismatch",
    )


def test_timestamp_order_is_not_semantics() -> None:
    graph = control_graph("review_candidate")
    request = make_request(graph, observed_at="2026-08-08T18:59:59Z")
    response = make_adapter(
        graph,
        "cancellation_rejected",
        observed_at="2026-08-08T18:00:00Z",
    )
    process = make_process(
        graph,
        "signal_delivered",
        observed_at="2026-08-08T17:00:00Z",
    )
    _request_call(graph, request)
    _response_call(graph, response, request)
    _process_call(graph, process)


def test_relation_failures_are_content_free_and_process_control_propagates(monkeypatch) -> None:
    graph = control_graph("validate_candidate")
    supplied = "private-payload-must-not-escape"
    error = _assert_error(
        lambda: wire.validate_wire_exact_current_process_observation_relation(
            observation=supplied,
            author_command=graph.command,
            attempt_fence=graph.attempt,
            author_effect_fence=graph.author,
            target_effect_fence=graph.target,
            target_delivery=graph.target_delivery,
            target_capsule_manifest=graph.manifest,
        ),
        "invalid_field_type",
    )
    assert supplied not in str(error) and supplied not in repr(error)

    def foreign(*args, **kwargs):
        raise RuntimeError(supplied)

    monkeypatch.setattr(wire, "_reconstruct_exact_worker_execution_value", foreign)
    _assert_error(lambda: _request_call(graph), "invalid_field_value")

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(wire, "_reconstruct_exact_worker_execution_value", interrupt)
    with pytest.raises(KeyboardInterrupt):
        _request_call(graph)


def test_relation_work_maxima_and_one_under_controls_are_exact(monkeypatch) -> None:
    graph = control_graph("author_candidate")
    rebuilt_occurrences: list[object] = []
    owner_rebuild = wire._rebuild_c2a

    def counted_rebuild(value, expected):
        rebuilt_occurrences.append(value)
        return owner_rebuild(value, expected)

    with monkeypatch.context() as reconstruction_patch:
        reconstruction_patch.setattr(wire, "_rebuild_c2a", counted_rebuild)
        _request_call(graph)
    assert rebuilt_occurrences == [
        graph.command,
        graph.attempt,
        graph.author,
        graph.target,
        graph.target_delivery,
        graph.cancel,
        graph.cancel_delivery,
    ]
    for target_class in TARGET_CLASSES:
        graph = control_graph(target_class)
        request = make_request(graph)
        response = make_adapter(graph, "cancellation_acknowledged")
        process = make_process(graph, "resource_limit_exceeded")
        operations = (
            lambda graph=graph, request=request: _request_call(graph, request),
            lambda graph=graph, process=process: _process_call(graph, process),
            lambda graph=graph, response=response, request=request: _response_call(
                graph, response, request
            ),
        )
        for operation in operations:
            monkeypatch.setattr(
                wire, "_CANCELLATION_CONTROL_WORK_TEST_EXTRA_UNITS", 0
            )
            operation()
            monkeypatch.setattr(
                wire, "_CANCELLATION_CONTROL_WORK_TEST_EXTRA_UNITS", -1
            )
            _assert_error(operation, "work_limit_exceeded")
