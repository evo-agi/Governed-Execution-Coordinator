from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest

import ge_nwp_coordinator._rw0_wire_protocol_values as wire
from ge_nwp_coordinator._worker_execution_semantic_values import (
    DeliveryEnvelopeV1, EffectFenceV1, WorkerObservationV1,
)
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireCancellationRequestObservationV1, RW0WireProcessObservationV1,
    RW0WireProcessResultClassificationV1, RW0WireProtocolError,
    RW0WireWorkerResultV1, classify_wire_process_result,
)
from tests.c2a_contract_support import _reseal_single_digest_record
from tests.test_rw0_b2_wire_values import (
    PROCESS_SCHEMA, REQUEST_SCHEMA, adapter_observation, graph, process_mapping,
    request_mapping, seal, worker_observation,
)

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- RW0_B2_WIRE_CURRENT_STATUS_BEGIN -->"
END = "<!-- RW0_B2_WIRE_CURRENT_STATUS_END -->"
PATHS = (
    ".docs/rw0-remote-worker-contact-phase-entry.md",
    ".docs/authority-boundaries.md",
    ".docs/autonomous-software-development-operating-model.md",
    ".docs/durable-state-model.md",
    ".docs/worker-execution-boundary.md",
)
PROFILE_DIGEST = "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"


def classify(*, result=True, failure=None, adapters=(), request=False, processes=(), cancellation=False):
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    worker_result = RW0WireWorkerResultV1._create((
        worker_observation("worker_started", "observation.started.0001"),
        worker_observation("worker_completed", "observation.completed.0001"),
    )) if result else None
    request_value = RW0WireCancellationRequestObservationV1.from_mapping(
        request_mapping()) if request else None
    return classify_wire_process_result(
        command=command, delivery=delivery, attempt_fence=attempt,
        author_effect_fence=author, result=worker_result,
        result_failure=failure, adapter_observations=adapters,
        request=request_value, process_observations=processes,
        cancellation_effect_fence=cancel if cancellation else None,
        cancellation_delivery=cancel_delivery if cancellation else None,
    )


def pair(value):
    return value.classification, value.reason


def explicit_classify(
    *, result=None, failure=None, adapters=(), request=None, processes=(),
    cancellation_effect_fence=None, cancellation_delivery=None,
):
    command, attempt, author, delivery, _, _ = graph()
    return classify_wire_process_result(
        command=command, delivery=delivery, attempt_fence=attempt,
        author_effect_fence=author, result=result, result_failure=failure,
        adapter_observations=adapters, request=request,
        process_observations=processes,
        cancellation_effect_fence=cancellation_effect_fence,
        cancellation_delivery=cancellation_delivery,
    )


def cancellation_graph(token: str):
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    fence_mapping = cancel.to_mapping()
    fence_mapping.update(
        effect_intent_ref=f"effect-intent.cancel-{token}.0001",
        effect_fence_ref=f"effect-fence.cancel-{token}.0001",
        effect_authorization_ref=f"effect-authorization.cancel-{token}.0001",
    )
    cancel = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", fence_mapping))
    delivery_mapping = cancel_delivery.to_mapping()
    delivery_mapping.update(
        delivery_attempt_ref=f"delivery-attempt.cancel-{token}.0001",
        effect_intent_ref=cancel.effect_intent_ref,
        effect_fence_ref=cancel.effect_fence_ref,
        effect_fence_digest=cancel.effect_fence_digest,
        adapter_safe_correlation_ref=f"adapter-correlation.cancel-{token}.0001",
    )
    cancel_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", delivery_mapping))
    return cancel, cancel_delivery


def cancellation_request(cancel, cancel_delivery):
    mapping = request_mapping()
    mapping.update(
        cancellation_effect_intent_ref=cancel.effect_intent_ref,
        cancellation_effect_fence_ref=cancel.effect_fence_ref,
        cancellation_effect_fence_digest=cancel.effect_fence_digest,
        cancellation_delivery_attempt_ref=cancel_delivery.delivery_attempt_ref,
        cancellation_delivery_envelope_digest=cancel_delivery.delivery_envelope_digest,
    )
    return RW0WireCancellationRequestObservationV1.from_mapping(
        seal(mapping, REQUEST_SCHEMA + ".identity", "request_observation_digest"))


def cancellation_response(kind: str, reference: str, cancel, cancel_delivery):
    command, attempt, author, _, _, _ = graph()
    return WorkerObservationV1.create(
        observation_ref=reference, source_kind="direct_local_adapter",
        source_ref="adapter.safe.0001",
        source_invocation_ref="adapter.invocation.safe.0001",
        observation_kind=kind,
        outcome="acknowledged" if kind == "cancellation_acknowledged" else "rejected",
        reason_code="reason.none", evidence_refs=["evidence.safe.0002"],
        observed_at="2026-08-08T18:00:01Z", delivery=cancel_delivery,
        author_command=command, attempt_fence=attempt,
        author_effect_fence=author, effect_fence=cancel,
        cancellation_target=author,
    )


def test_usable_missing_failed_and_invalid_result_tiers() -> None:
    zero = adapter_observation("process_exited", "observation.exited.0001", 0)
    nonzero = adapter_observation("process_exited", "observation.exited.0001", 1)
    assert pair(classify(adapters=(zero,))) == ("usable", "usable")
    assert pair(classify(result=False, adapters=(zero,))) == ("unusable", "result_missing")
    assert pair(classify(adapters=(nonzero,))) == ("unusable", "process_result_contradiction")
    assert pair(classify(result=False, adapters=(nonzero,))) == ("unusable", "process_failed")
    assert pair(classify()) == ("unusable", "process_evidence_incomplete")
    try:
        RW0WireProcessObservationV1.from_mapping({})
    except RW0WireProtocolError as failure:
        assert pair(classify(result=False, failure=failure, adapters=(zero,))) == (
            "unusable", "result_invalid")


def test_resource_deadline_signal_and_request_precedence() -> None:
    resource = RW0WireProcessObservationV1.from_mapping(process_mapping("resource_limit_exceeded"))
    signal = RW0WireProcessObservationV1.from_mapping(process_mapping("signal_delivered"))
    deadline = adapter_observation("deadline_elapsed", "observation.deadline.0001")
    zero = adapter_observation("process_exited", "observation.exited.0001", 0)
    ack = adapter_observation("cancellation_acknowledged", "observation.ack.0001")
    reject = adapter_observation("cancellation_rejected", "observation.reject.0001")
    assert pair(classify(processes=(resource,), adapters=(deadline, zero), request=True,
                         cancellation=True)) == ("unusable", "resource_limit_exceeded")
    assert pair(classify(adapters=(deadline, zero), request=True,
                         cancellation=True)) == ("unusable", "deadline_elapsed")
    assert pair(classify(processes=(signal,), adapters=(zero,), request=True,
                         cancellation=True)) == ("unusable", "signal_delivered")
    assert pair(classify(adapters=(ack, zero), request=True,
                         cancellation=True)) == ("unusable", "cancellation_acknowledged")
    assert pair(classify(adapters=(reject, zero), request=True,
                         cancellation=True)) == ("unusable", "cancellation_rejected")
    assert pair(classify(adapters=(zero,), request=True,
                         cancellation=True)) == ("unusable", "cancellation_request_pending")
    assert pair(classify(adapters=(ack,), cancellation=True)) == (
        "invalid", "cancellation_graph_mismatch")
    assert pair(classify(adapters=(ack, reject), request=True,
                         cancellation=True)) == ("invalid", "conflicting_fact")


def test_duplicate_and_cardinality_are_invalid_first() -> None:
    zero = adapter_observation("process_exited", "observation.exited.0001", 0)
    resource = RW0WireProcessObservationV1.from_mapping(process_mapping("resource_limit_exceeded"))
    assert pair(classify(adapters=(zero, zero), processes=(resource,))) == ("invalid", "duplicate_fact")
    assert pair(classify(adapters=(zero,) * 5, request=True,
                         processes=(resource, resource), cancellation=True)) == (
        "invalid", "invalid_input")


def test_duplicate_identities_and_distinct_singleton_conflicts_are_separate() -> None:
    zero = adapter_observation("process_exited", "observation.exit.zero.0001", 0)
    another_zero = adapter_observation(
        "process_exited", "observation.exit.zero.0002", 0)
    nonzero = adapter_observation("process_exited", "observation.exit.one.0001", 1)
    assert pair(classify(adapters=(zero, zero))) == ("invalid", "duplicate_fact")
    assert pair(classify(adapters=(zero, another_zero))) == (
        "invalid", "conflicting_fact")
    assert pair(classify(adapters=(zero, nonzero))) == (
        "invalid", "conflicting_fact")

    same_digest = adapter_observation(
        "process_exited", "observation.exit.digest.0001", 0)
    object.__setattr__(same_digest, "_observation_digest", zero.observation_digest)
    assert pair(classify(adapters=(zero, same_digest))) == (
        "invalid", "invalid_input")
    same_ref = adapter_observation(
        "process_exited", "observation.exit.reference.0001", 0)
    object.__setattr__(same_ref, "_observation_ref", zero.observation_ref)
    assert pair(classify(adapters=(zero, same_ref))) == (
        "invalid", "invalid_input")

    deadline_a = adapter_observation(
        "deadline_elapsed", "observation.deadline.0001")
    deadline_b = adapter_observation(
        "deadline_elapsed", "observation.deadline.0002")
    assert pair(classify(adapters=(deadline_a, deadline_a))) == (
        "invalid", "duplicate_fact")
    assert pair(classify(adapters=(deadline_a, deadline_b))) == (
        "invalid", "conflicting_fact")

    process_a = RW0WireProcessObservationV1.from_mapping(
        process_mapping("resource_limit_exceeded"))
    process_b_mapping = process_mapping("resource_limit_exceeded")
    process_b_mapping.update(
        process_observation_ref="process.observation.safe.0002",
        evidence_ref="evidence.process.safe.0002",
    )
    process_b = RW0WireProcessObservationV1.from_mapping(
        seal(process_b_mapping, PROCESS_SCHEMA + ".identity",
             "process_observation_digest"))
    assert pair(classify(processes=(process_a, process_a))) == (
        "invalid", "duplicate_fact")
    assert pair(classify(processes=(process_a, process_b))) == (
        "invalid", "conflicting_fact")


def test_cancellation_graph_mismatch_is_orientation_independent() -> None:
    graph_a = cancellation_graph("a")
    graph_b = cancellation_graph("b")
    graph_c = cancellation_graph("c")
    request_a = cancellation_request(*graph_a)
    response_b = cancellation_response(
        "cancellation_acknowledged", "observation.ack.graph-b.0001", *graph_b)
    for supplied in (graph_a, graph_b, graph_c):
        assert pair(explicit_classify(
            adapters=(response_b,), request=request_a,
            cancellation_effect_fence=supplied[0],
            cancellation_delivery=supplied[1],
        )) == ("invalid", "cancellation_graph_mismatch")

    invalid_delivery_mapping = graph_c[1].to_mapping()
    invalid_delivery_mapping["program_ref"] = "program.graph-mismatch.0001"
    invalid_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record(
            "DeliveryEnvelopeV1", invalid_delivery_mapping))
    assert pair(explicit_classify(
        cancellation_effect_fence=graph_c[0],
        cancellation_delivery=invalid_delivery,
    )) == ("invalid", "cancellation_graph_mismatch")


def test_classifier_revalidates_bypass_instances_before_slot_access() -> None:
    for arguments in (
        {"request": object.__new__(RW0WireCancellationRequestObservationV1)},
        {"processes": (object.__new__(RW0WireProcessObservationV1),)},
        {"result": object.__new__(RW0WireWorkerResultV1)},
    ):
        assert pair(explicit_classify(**arguments)) == ("invalid", "invalid_input")


def test_classifier_reconstructs_every_fact_before_duplicate_semantics() -> None:
    valid = adapter_observation(
        "process_exited", "observation.reconstruct.valid.0001", 0)

    partial_adapter = object.__new__(WorkerObservationV1)
    object.__setattr__(
        partial_adapter, "_observation_ref", valid.observation_ref)
    object.__setattr__(
        partial_adapter, "_observation_digest", valid.observation_digest)
    object.__setattr__(partial_adapter, "_observation_kind", "process_exited")

    partial_request = object.__new__(RW0WireCancellationRequestObservationV1)
    object.__setattr__(
        partial_request, "_request_observation_ref", valid.observation_ref)
    object.__setattr__(
        partial_request, "_request_observation_digest", valid.observation_digest)

    partial_process = object.__new__(RW0WireProcessObservationV1)
    object.__setattr__(
        partial_process, "_process_observation_ref", valid.observation_ref)
    object.__setattr__(
        partial_process, "_process_observation_digest", valid.observation_digest)
    object.__setattr__(
        partial_process, "_event_kind", "resource_limit_exceeded")

    cases = (
        ({"adapters": (partial_adapter,)},
         {"adapters": (valid, partial_adapter)},
         {"adapters": (partial_adapter, partial_adapter)}),
        ({"request": partial_request},
         {"adapters": (valid,), "request": partial_request},
         None),
        ({"processes": (partial_process,)},
         {"adapters": (valid,), "processes": (partial_process,)},
         {"processes": (partial_process, partial_process)}),
    )
    for alone, colliding, repeated in cases:
        assert pair(explicit_classify(**alone)) == ("invalid", "invalid_input")
        assert pair(explicit_classify(**colliding)) == (
            "invalid", "invalid_input")
        if repeated is not None:
            assert pair(explicit_classify(**repeated)) == (
                "invalid", "invalid_input")

    tampered = adapter_observation(
        "process_exited", "observation.reconstruct.tampered.0001", 0)
    object.__setattr__(
        tampered, "_observation_digest", valid.observation_digest)
    assert pair(explicit_classify(adapters=(tampered,))) == (
        "invalid", "invalid_input")
    assert pair(explicit_classify(adapters=(valid, tampered))) == (
        "invalid", "invalid_input")

    partial_result_fact = object.__new__(WorkerObservationV1)
    completed = worker_observation(
        "worker_completed", "observation.reconstruct.completed.0001")
    object.__setattr__(
        partial_result_fact, "_observation_ref", completed.observation_ref)
    object.__setattr__(
        partial_result_fact, "_observation_digest", completed.observation_digest)
    object.__setattr__(
        partial_result_fact, "_observation_kind", "worker_started")
    partial_result = object.__new__(RW0WireWorkerResultV1)
    object.__setattr__(
        partial_result, "_observations", (partial_result_fact, completed))
    assert pair(explicit_classify(result=partial_result)) == (
        "invalid", "invalid_input")


def test_classifier_valid_duplicate_identities_are_checked_after_reconstruction() -> None:
    valid = adapter_observation(
        "process_exited", "observation.valid-duplicate.0001", 0)
    same_value = WorkerObservationV1.from_mapping(valid.to_mapping())
    assert same_value is not valid
    assert same_value.observation_digest == valid.observation_digest
    assert pair(explicit_classify(adapters=(valid, same_value))) == (
        "invalid", "duplicate_fact")

    same_ref_mapping = adapter_observation(
        "process_exited", "observation.valid-duplicate.0002", 0).to_mapping()
    same_ref_mapping.update(
        observation_ref=valid.observation_ref,
        observed_at="2026-08-08T18:00:02Z",
    )
    same_ref = WorkerObservationV1.from_mapping(
        _reseal_single_digest_record("WorkerObservationV1", same_ref_mapping))
    assert same_ref.observation_digest != valid.observation_digest
    assert pair(explicit_classify(adapters=(valid, same_ref))) == (
        "invalid", "duplicate_fact")


def test_classifier_pairwise_precedence_and_unrelated_non_cancellation_fact() -> None:
    valid_result = RW0WireWorkerResultV1._create((
        worker_observation("worker_started", "observation.precedence.started.0001"),
        worker_observation("worker_completed", "observation.precedence.completed.0001"),
    ))
    resource = RW0WireProcessObservationV1.from_mapping(
        process_mapping("resource_limit_exceeded"))
    signal_mapping = process_mapping("signal_delivered")
    signal_mapping.update(
        process_observation_ref="process.observation.signal.0001",
        evidence_ref="evidence.process.signal.0001",
    )
    signal = RW0WireProcessObservationV1.from_mapping(
        seal(signal_mapping, PROCESS_SCHEMA + ".identity",
             "process_observation_digest"))
    deadline = adapter_observation("deadline_elapsed", "observation.precedence.deadline.0001")
    zero = adapter_observation("process_exited", "observation.precedence.zero.0001", 0)
    nonzero = adapter_observation("process_exited", "observation.precedence.nonzero.0001", 1)
    cancel, cancel_delivery = cancellation_graph("precedence")
    request = cancellation_request(cancel, cancel_delivery)
    ack = cancellation_response(
        "cancellation_acknowledged", "observation.precedence.ack.0001",
        cancel, cancel_delivery)
    result_failure = None
    try:
        RW0WireProcessObservationV1.from_mapping({})
    except RW0WireProtocolError as caught:
        result_failure = caught
    assert result_failure is not None

    assert pair(explicit_classify(
        result=valid_result, adapters=(deadline, zero), processes=(resource, signal),
        request=request, cancellation_effect_fence=cancel,
        cancellation_delivery=cancel_delivery)) == (
            "unusable", "resource_limit_exceeded")
    assert pair(explicit_classify(
        result=valid_result, adapters=(deadline, zero), processes=(signal,),
        request=request, cancellation_effect_fence=cancel,
        cancellation_delivery=cancel_delivery)) == ("unusable", "deadline_elapsed")
    assert pair(explicit_classify(
        result=valid_result, adapters=(zero,), processes=(signal,), request=request,
        cancellation_effect_fence=cancel,
        cancellation_delivery=cancel_delivery)) == ("unusable", "signal_delivered")
    assert pair(explicit_classify(
        result=valid_result, adapters=(ack, zero), request=request,
        cancellation_effect_fence=cancel,
        cancellation_delivery=cancel_delivery)) == (
            "unusable", "cancellation_acknowledged")
    assert pair(explicit_classify(result=valid_result, adapters=(nonzero,))) == (
        "unusable", "process_result_contradiction")
    assert pair(explicit_classify(adapters=(nonzero,))) == (
        "unusable", "process_failed")
    assert pair(explicit_classify(adapters=(zero,))) == ("unusable", "result_missing")
    assert pair(explicit_classify(failure=result_failure, adapters=(zero,))) == (
        "unusable", "result_invalid")
    assert pair(explicit_classify(result=valid_result)) == (
        "unusable", "process_evidence_incomplete")

    for processes, adapters, request_value, expected in (
        ((resource,), (zero,), None, "resource_limit_exceeded"),
        ((), (deadline, zero), None, "deadline_elapsed"),
        ((signal,), (zero,), None, "signal_delivered"),
        ((), (zero,), request, "cancellation_request_pending"),
    ):
        assert pair(explicit_classify(
            failure=result_failure, adapters=adapters, processes=processes,
            request=request_value,
            cancellation_effect_fence=cancel if request_value else None,
            cancellation_delivery=cancel_delivery if request_value else None,
        )) == ("unusable", expected)

    unrelated_mapping = deadline.to_mapping()
    unrelated_mapping["program_ref"] = "program.unrelated.0001"
    unrelated = WorkerObservationV1.from_mapping(
        _reseal_single_digest_record("WorkerObservationV1", unrelated_mapping))
    assert pair(explicit_classify(adapters=(unrelated,))) == (
        "invalid", "unrelated_fact")


def test_complete_classification_reason_constructor_matrix() -> None:
    valid = {
        "usable": {"usable"},
        "invalid": {
            "invalid_input", "unrelated_fact", "duplicate_fact", "conflicting_fact",
            "cancellation_graph_mismatch",
        },
        "unusable": {
            "resource_limit_exceeded", "deadline_elapsed", "signal_delivered",
            "cancellation_request_pending", "cancellation_acknowledged",
            "cancellation_rejected", "process_result_contradiction", "process_failed",
            "result_missing", "result_invalid", "process_evidence_incomplete",
        },
    }
    reasons = set().union(*valid.values())
    for classification, accepted in valid.items():
        for reason in reasons:
            if reason in accepted:
                value = RW0WireProcessResultClassificationV1._create(
                    classification, reason)
                assert pair(value) == (classification, reason)
            else:
                with pytest.raises(RW0WireProtocolError) as caught:
                    RW0WireProcessResultClassificationV1._create(
                        classification, reason)
                assert caught.value.reason == "invalid_field_value"


def _visible(text: str):
    ordinary = []
    headings = []
    fence = None
    comment = False
    for number, line in enumerate(text.splitlines()):
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        control = None
        if indent <= 3 and stripped[:1] in (chr(96), "~"):
            run = len(stripped) - len(stripped.lstrip(stripped[0]))
            if run >= 3: control = (stripped[0], run, stripped[run:])
        if fence:
            if control and control[0] == fence[0] and control[1] >= fence[1] and not control[2].strip():
                fence = None
            continue
        if control:
            fence = control[:2]
            continue
        if comment:
            if "-->" in line: comment = False
            continue
        if stripped.startswith("<!--") and "-->" not in stripped:
            comment = True
            continue
        ordinary.append((number, line))
        match = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped) if indent <= 3 else None
        if match: headings.append((number, len(match[1]), match[2].strip()))
    assert fence is None and not comment
    return ordinary, headings


def _status(text: str, root: str, heading: str, level: int) -> str:
    visible, headings = _visible(text)
    assert len([h for h in headings if h[1] == 1]) == 1
    assert headings[0][2] == root
    owners = [h for h in headings if h[1] == level and h[2] == heading]
    assert len(owners) == 1
    begins = [number for number, line in visible if line.strip() == BEGIN]
    ends = [number for number, line in visible if line.strip() == END]
    assert len(begins) == len(ends) == 1
    begin, end = begins[0], ends[0]
    assert owners[0][0] < begin < end
    assert not any(h[0] > owners[0][0] and h[0] < end and h[1] <= level for h in headings)
    body = " ".join(line.strip() for number, line in visible if begin < number < end)
    assert "RW0-B2-Wire now implements" in body
    return " ".join(body.split())


def test_status_owner_and_five_cross_references_are_synchronized() -> None:
    owner = (ROOT / ".docs/rw0-b2-wire-protocol.md").read_text()
    assert owner.startswith("# RW0-B2-Wire Private Protocol\n")
    assert owner.count("## Current status and authority") == 1
    titles = (
        ("RW0 Remote-Contact Phase-Entry Operating Model", "Status, scope, and nonimplementation", 2),
        ("Authority Boundaries", "RW0 remote-contact phase-entry target cross-reference", 3),
        ("C1 Autonomous Software-Development Operating Model", "RW0 remote-contact phase-entry target cross-reference", 3),
        ("Durable State Model", "RW0 remote-contact phase-entry target cross-reference", 3),
        ("Worker Execution Boundary", "RW0 remote-contact phase-entry target cross-reference", 3),
    )
    bodies = [_status((ROOT / path).read_text(), *title)
              for path, title in zip(PATHS, titles, strict=True)]
    assert len(set(bodies)) == 1
    for phrase in (PROFILE_DIGEST,
                   "their protected owner reconstruction and occurrence-work accounting are hardened separately",
                   "Capability is implemented separately as private, pure, no-I/O semantics",
                   ".docs/rw0-b2-capability.md",
                   "does not widen Wire ownership",
                   "private, pure, no-I/O NWPF v1 representational framing",
                   "Physical transport framing and stream/process plumbing remain deferred",
                   "RW0-C/D/E", "Execution Substrate"):
        assert phrase in bodies[0]
    stale = (
        "Exact custodian, transport, framing, Codex seam, schema, "
        "terminal-outcome representation, latch, and physical backends remain deferred."
    )
    for path in PATHS[1:]:
        assert stale not in (ROOT / path).read_text()


def test_visible_status_parser_rejects_duplicate_relocation_and_hidden_controls() -> None:
    source = (ROOT / PATHS[1]).read_text()
    root = "Authority Boundaries"
    heading = "RW0 remote-contact phase-entry target cross-reference"
    assert _status(source, root, heading, 3)
    duplicate = source.replace(END, END + "\n" + BEGIN + "\nextra\n" + END, 1)
    with pytest.raises(AssertionError):
        _status(duplicate, root, heading, 3)
    relocation = source.replace("### " + heading, "### " + heading + "\n### " + heading, 1)
    with pytest.raises(AssertionError):
        _status(relocation, root, heading, 3)
    assert _status(source + "\n~~~text\n" + BEGIN + "\n~~~\n", root, heading, 3)
    ticks = chr(96) * 3
    assert _status(source + "\n" + ticks + "text\n" + END + "\n" + ticks + "\n",
                   root, heading, 3)


def test_private_import_and_public_boundary() -> None:
    path = ROOT / "src/ge_nwp_coordinator/_rw0_wire_protocol_values.py"
    tree = ast.parse(path.read_text())
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert {alias.name for node in imports if isinstance(node, ast.Import) for alias in node.names} == {
        "datetime", "hashlib", "json", "re", "typing"}
    local = [node for node in imports if isinstance(node, ast.ImportFrom) and node.level]
    assert len(local) == 1 and local[0].module == "_worker_execution_semantic_values"
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"open", "exec", "eval", "__import__"} for node in ast.walk(tree))
    import ge_nwp_coordinator as package
    assert not hasattr(package, "RW0WireWorkerResultV1")
    assert not hasattr(package, "wire_profile_mapping")
    capability_path = ROOT / "src/ge_nwp_coordinator/_rw0_worker_mechanism_capability_values.py"
    production_importers = []
    for candidate in (ROOT / "src/ge_nwp_coordinator").rglob("*.py"):
        if candidate == path:
            continue
        source = candidate.read_text()
        if "_rw0_wire_protocol_values" not in source:
            continue
        production_importers.append(candidate)
        assert candidate == capability_path
        owner_imports = [
            node for node in ast.parse(source).body
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "_rw0_wire_protocol_values"
        ]
        assert len(owner_imports) == 1
        assert {alias.name for alias in owner_imports[0].names} == {"wire_profile_mapping"}
    assert production_importers == [capability_path]
    assert "_rw0_worker_mechanism_capability_values" not in path.read_text()
    capability_owner = (ROOT / ".docs/rw0-b2-capability.md").read_text()
    assert capability_owner.count("<!-- RW0_B2_CAPABILITY_OWNER_BEGIN -->") == 1
    assert capability_owner.count("<!-- RW0_B2_CAPABILITY_OWNER_END -->") == 1
    assert "sole detailed owner" in capability_owner
