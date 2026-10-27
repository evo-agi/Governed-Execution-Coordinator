from __future__ import annotations

import builtins
import hashlib
from pathlib import Path

import pytest
from test_rw0_c2_bootstrap_acceptance_guard_semantic_contract import (
    _rw0_c2_current_drift_predecessor,
)

import ge_nwp_coordinator as package
import ge_nwp_coordinator._rw0_phase_entry_semantic_values as phase
import ge_nwp_coordinator._rw0_wire_protocol_values as wire
import ge_nwp_coordinator._rw0_worker_mechanism_capability_values as capability
from ge_nwp_coordinator._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1,
    WorkerObservationV1,
)
from tests.c2a_contract_support import _full_record
from tests.test_rw0_b2_capability_boundaries import PROTECTED_CONTENT_ROWS
from tests.test_rw0_b2_wire_cancellation_control_values import (
    PROFILE_DIGEST_V1,
    PROFILE_REF_V1,
    capsule_operand,
    classifier_kwargs,
    control_graph,
    make_adapter,
    make_process,
    make_request,
)


ROOT = Path(__file__).resolve().parents[1]
STATUS_BEGIN = "<!-- RW0_B2_WIRE_CURRENT_STATUS_BEGIN -->"
STATUS_END = "<!-- RW0_B2_WIRE_CURRENT_STATUS_END -->"
# The exact Wire-stage status below is historical where it places C2 durability
# in the future; the separate current C2 successor is required below.
EXPECTED_STATUS = "RW0-B2-Wire now implements private, pure, no-I/O NWPF v1 representational framing, canonical command/result codecs, closed worker-result grammar, safe supplied cancellation-request and process source-claim values, and pure process/result classification. It also implements the separate private, pure, no-I/O cancellation-control evidence profile `rw0-wire-cancellation-control-v1` with digest `4d6f84552b852a4c4073b4238591afd271072f648424eca9e744def436165288`, exact-current author/validation/review cancellation-control relations, and pure `invalid`/`incomplete`/`finite` supplied-control-evidence classification. The additive cancellation-control profile does not replace or enter the fixed NWPF v1 frames, Capability continues to bind only `rw0-wire-nwpf-v1`, and the profile remains distinct from B1 physical host cancellation-mechanism evidence. Physical transport framing and stream/process plumbing remain deferred, as do pre-read allocation, supervisor/worker implementation, cancellation delivery, concrete direct-local or ES wrapper/correlation mechanics, persistence, source authentication, process proof, CLI/App Server integration, credentials, provider/session behavior, and live execution. The fixed protocol profile is `rw0-wire-nwpf-v1` with digest `470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454`; `.docs/rw0-b2-wire-protocol.md` is the detailed owner. RW0-B2-Wire does not own or alter RW0-B1 or C2A schema, canonical-identity, semantic-outcome, or authority contracts; their protected owner reconstruction and occurrence-work accounting are hardened separately for fail-closed Capability composition. No worker, process, contact, persistence, authority, acceptance, or Codex mechanism is implemented. Capability is implemented separately as private, pure, no-I/O semantics owned by `.docs/rw0-b2-capability.md` and does not widen Wire ownership. RW0-B1, RW0-B2-Wire, and RW0-B2-Capability private semantics are current implemented contracts; RW0-C/D/E durable, transport, process, provider, credential, live-proof, and runtime mechanics remain future, and Execution Substrate retains admission and runtime ownership."
STATUS_PATHS = (
    ROOT / ".docs/rw0-remote-worker-contact-phase-entry.md",
    ROOT / ".docs/authority-boundaries.md",
    ROOT / ".docs/autonomous-software-development-operating-model.md",
    ROOT / ".docs/durable-state-model.md",
    ROOT / ".docs/worker-execution-boundary.md",
)


def classify(
    graph,
    *,
    request=None,
    adapters=(),
    processes=(),
):
    return wire.classify_wire_exact_current_cancellation_control(
        request=request,
        adapter_observations=adapters,
        process_observations=processes,
        **classifier_kwargs(graph),
    )


def _pair(result) -> tuple[str, str]:
    return result.classification, result.reason


def test_classifier_complete_precedence_and_coexistence_matrix() -> None:
    graph = control_graph("author_candidate")
    request = make_request(graph)
    facts = {
        "ack": make_adapter(graph, "cancellation_acknowledged"),
        "reject": make_adapter(graph, "cancellation_rejected"),
        "deadline": make_adapter(graph, "deadline_elapsed"),
        "exit": make_adapter(graph, "process_exited", exit_code=0),
        "resource": make_process(graph, "resource_limit_exceeded"),
        "signal": make_process(graph, "signal_delivered"),
    }
    cases = (
        (None, (), (), ("incomplete", "process_evidence_incomplete")),
        (request, (), (), ("incomplete", "cancellation_request_pending")),
        (request, (facts["reject"],), (), ("finite", "cancellation_rejected")),
        (request, (facts["exit"],), (), ("finite", "target_process_exited")),
        (request, (), (facts["resource"],), ("incomplete", "resource_limit_exceeded")),
        (request, (facts["deadline"],), (), ("incomplete", "deadline_elapsed")),
        (request, (), (facts["signal"],), ("incomplete", "signal_delivered")),
        (request, (facts["ack"],), (), ("incomplete", "cancellation_acknowledged")),
        (request, (facts["reject"], facts["exit"]), (), ("finite", "cancellation_rejected")),
        (request, (facts["ack"], facts["exit"]), (), ("finite", "target_process_exited")),
        (request, (facts["exit"],), (facts["signal"],), ("finite", "target_process_exited")),
        (request, (facts["exit"],), (facts["resource"],), ("finite", "target_process_exited")),
        (request, (facts["deadline"], facts["exit"]), (), ("finite", "target_process_exited")),
    )
    for supplied_request, adapters, processes, expected in cases:
        assert _pair(
            classify(
                graph,
                request=supplied_request,
                adapters=adapters,
                processes=processes,
            )
        ) == expected


def test_duplicates_precede_unrelated_conflict_and_graph_mismatch(monkeypatch) -> None:
    graph = control_graph("author_candidate")
    request = make_request(graph)
    acknowledgement = make_adapter(graph, "cancellation_acknowledged")
    unrelated = make_adapter(graph, "delivery_acknowledged")
    rejection = make_adapter(graph, "cancellation_rejected")
    calls = 0
    rebuild = wire._rebuild_c2a

    def counted(value, expected):
        nonlocal calls
        if value is acknowledgement and expected is WorkerObservationV1:
            calls += 1
        return rebuild(value, expected)

    monkeypatch.setattr(wire, "_rebuild_c2a", counted)
    result = classify(
        graph,
        request=None,
        adapters=(acknowledgement, acknowledgement, unrelated, rejection),
    )
    assert _pair(result) == ("invalid", "duplicate_fact")
    assert calls == 2

    rebuilt = WorkerObservationV1.from_mapping(acknowledgement.to_mapping())
    assert acknowledgement is not rebuilt
    assert _pair(
        classify(graph, request=request, adapters=(acknowledgement, rebuilt))
    ) == ("invalid", "duplicate_fact")

    sibling = control_graph("review_candidate")
    unrelated_target = make_adapter(sibling, "deadline_elapsed")
    assert _pair(
        classify(
            graph,
            request=None,
            adapters=(unrelated_target, acknowledgement, rejection),
        )
    ) == ("invalid", "unrelated_fact")


def test_singleton_conflicts_and_ack_reject_exclusion_are_exact() -> None:
    graph = control_graph()
    request = make_request(graph)
    deadlines = (
        make_adapter(graph, "deadline_elapsed", ref="deadline.one.0001"),
        make_adapter(
            graph,
            "deadline_elapsed",
            ref="deadline.two.0001",
            observed_at="2026-08-08T18:00:04Z",
        ),
    )
    resources = (
        make_process(graph, "resource_limit_exceeded", ref="resource.one.0001"),
        make_process(
            graph,
            "resource_limit_exceeded",
            ref="resource.two.0001",
            observed_at="2026-08-08T18:00:05Z",
        ),
    )
    assert _pair(classify(graph, request=request, adapters=deadlines)) == (
        "invalid", "conflicting_fact"
    )
    assert _pair(classify(graph, request=request, processes=resources)) == (
        "invalid", "conflicting_fact"
    )
    assert _pair(
        classify(
            graph,
            request=request,
            adapters=(
                make_adapter(graph, "cancellation_acknowledged"),
                make_adapter(graph, "cancellation_rejected"),
            ),
        )
    ) == ("invalid", "conflicting_fact")


def test_request_response_and_target_process_dependence_is_exact() -> None:
    graph = control_graph()
    request = make_request(graph)
    for adapters, processes in (
        ((make_adapter(graph, "deadline_elapsed"),), ()),
        ((make_adapter(graph, "process_exited", exit_code=0),), ()),
        ((), (make_process(graph, "resource_limit_exceeded"),)),
        ((), (make_process(graph, "signal_delivered"),)),
    ):
        assert _pair(
            classify(graph, request=None, adapters=adapters, processes=processes)
        ) == ("incomplete", "process_evidence_incomplete")
    for role in ("cancellation_acknowledged", "cancellation_rejected"):
        assert _pair(
            classify(
                graph,
                request=None,
                adapters=(make_adapter(graph, role),),
            )
        ) == ("invalid", "cancellation_graph_mismatch")
    assert _pair(classify(graph, request=request)) == (
        "incomplete", "cancellation_request_pending"
    )
    sibling = control_graph("validate_candidate")
    assert _pair(classify(graph, request=make_request(sibling))) == (
        "invalid", "cancellation_graph_mismatch"
    )


def test_every_outer_and_cardinality_boundary_is_exact(monkeypatch) -> None:
    graph = control_graph()
    request = make_request(graph)
    ack = make_adapter(graph, "cancellation_acknowledged")
    signal = make_process(graph, "signal_delivered")

    class TupleSubclass(tuple):
        pass

    malformed = (
        {"request": object(), "adapters": (), "processes": ()},
        {"request": request, "adapters": [], "processes": ()},
        {"request": request, "adapters": (), "processes": []},
        {"request": request, "adapters": TupleSubclass(), "processes": ()},
        {"request": request, "adapters": (ack,) * 5, "processes": ()},
        {"request": request, "adapters": (), "processes": (signal,) * 3},
        {"request": request, "adapters": (None,), "processes": ()},
        {"request": request, "adapters": (), "processes": (None,)},
    )
    for case in malformed:
        assert _pair(classify(graph, **case)) == ("invalid", "invalid_input")
    assert _pair(
        wire.classify_wire_exact_current_cancellation_control(
            request=request,
            adapter_observations=(),
            process_observations=(),
            target_capsule_manifest=None,
            **{
                key: value
                for key, value in classifier_kwargs(graph).items()
                if key != "target_capsule_manifest"
            },
        )
    ) == ("invalid", "invalid_input")

    maximum_adapters = (
        make_adapter(graph, "cancellation_acknowledged"),
        make_adapter(graph, "cancellation_rejected"),
        make_adapter(graph, "deadline_elapsed"),
        make_adapter(graph, "process_exited", exit_code=0),
    )
    maximum_processes = (
        make_process(graph, "resource_limit_exceeded"),
        make_process(graph, "signal_delivered"),
    )
    monkeypatch.setattr(wire, "_CANCELLATION_CONTROL_WORK_TEST_EXTRA_UNITS", 0)
    assert _pair(
        classify(
            graph,
            request=request,
            adapters=maximum_adapters,
            processes=maximum_processes,
        )
    ) == ("invalid", "conflicting_fact")
    monkeypatch.setattr(wire, "_CANCELLATION_CONTROL_WORK_TEST_EXTRA_UNITS", -1)
    assert _pair(
        classify(
            graph,
            request=request,
            adapters=maximum_adapters,
            processes=maximum_processes,
        )
    ) == ("invalid", "invalid_input")


def test_exit_codes_minus_255_zero_and_255_are_equally_finite() -> None:
    graph = control_graph("review_candidate")
    request = make_request(graph)
    for exit_code in (-255, 0, 255):
        result = classify(
            graph,
            request=request,
            adapters=(
                make_adapter(
                    graph,
                    "process_exited",
                    ref=f"exit.code.{exit_code}.0001".replace("-", "minus."),
                    exit_code=exit_code,
                ),
            ),
        )
        assert _pair(result) == ("finite", "target_process_exited")


def test_hostile_manifest_reconstruction_cycles_aliases_and_large_integers_fail_bounded(monkeypatch) -> None:
    def outcome(mutator) -> tuple[str, str]:
        graph = control_graph("validate_candidate")
        mutator(graph.manifest)
        return _pair(classify(graph, request=make_request(graph)))

    def cycle(manifest):
        object.__setattr__(manifest, "_entries", (manifest,))

    def aliases(manifest):
        entry = manifest.entries[0]
        object.__setattr__(manifest, "_entries", (entry, entry, entry))

    def huge_integer(manifest):
        entry = manifest.entries[0]
        object.__setattr__(entry, "_before_byte_length", 10 ** 5000)

    for mutator in (cycle, aliases, huge_integer):
        assert outcome(mutator) == ("invalid", "invalid_input")

    selected = control_graph("validate_candidate")
    object.__setattr__(
        selected.manifest, "_portable_capsule_digest", "f" * 64
    )
    owner_reconstruct = wire._reconstruct_exact_worker_execution_value

    def selected_bypass(value, expected, budget=None):
        if value is selected.manifest:
            return value, {}
        return owner_reconstruct(value, expected, budget)

    with monkeypatch.context() as selected_patch:
        selected_patch.setattr(
            wire, "_reconstruct_exact_worker_execution_value", selected_bypass
        )
        assert _pair(
            classify(selected, request=make_request(selected))
        )[0] == "invalid"

    class_wide = control_graph("author_candidate")
    object.__setattr__(class_wide.target, "_effect_fence_digest", "e" * 64)
    with monkeypatch.context() as class_patch:
        class_patch.setattr(wire, "_rebuild_c2a", lambda value, expected: value)
        assert _pair(
            classify(class_wide, request=make_request(class_wide))
        )[0] == "invalid"


def test_classifier_privacy_and_foreign_exception_sanitization_are_exact(monkeypatch) -> None:
    graph = control_graph()
    secret = "credential-private-payload"

    def foreign(value):
        raise RuntimeError(secret)

    monkeypatch.setattr(wire, "_validated_request", foreign)
    result = classify(graph, request=make_request(graph))
    assert _pair(result) == ("invalid", "invalid_input")
    assert secret not in repr(result) and secret not in str(result)
    assert secret not in repr(result.to_mapping())

    def interrupt(value):
        raise KeyboardInterrupt

    monkeypatch.setattr(wire, "_validated_request", interrupt)
    with pytest.raises(KeyboardInterrupt):
        classify(graph, request=make_request(graph))


def test_module_remains_private_no_export_no_caller_and_no_io(monkeypatch) -> None:
    assert wire.__all__ == ()
    for name in (
        "RW0WireCancellationControlClassificationV1",
        "cancellation_control_profile_mapping",
        "validate_wire_exact_current_cancellation_request_relation",
        "validate_wire_exact_current_process_observation_relation",
        "validate_wire_exact_current_cancellation_response_relation",
        "classify_wire_exact_current_cancellation_control",
    ):
        assert hasattr(wire, name)
        assert not hasattr(package, name)

    def forbidden_io(*args, **kwargs):
        raise AssertionError("I/O attempted")

    monkeypatch.setattr(builtins, "open", forbidden_io)
    graph = control_graph()
    profile = wire.cancellation_control_profile_mapping()
    result = classify(graph, request=make_request(graph))
    assert profile["profile_ref"] == PROFILE_REF_V1
    assert _pair(result) == ("incomplete", "cancellation_request_pending")


def test_five_status_projections_and_owner_contract_are_synchronized() -> None:
    wire_path = '.docs/rw0-b2-wire-protocol.md'
    _rw0_c2_current_drift_predecessor(wire_path, (ROOT / wire_path).read_bytes())
    for path in STATUS_PATHS:
        text = path.read_text(encoding="utf-8")
        assert text.count(STATUS_BEGIN) == text.count(STATUS_END) == 1
        body = text.split(STATUS_BEGIN, 1)[1].split(STATUS_END, 1)[0]
        assert body == "\n" + EXPECTED_STATUS + "\n"
        assert body.count("\n") == 2
        capability_marker = "<!-- RW0_B2_CAPABILITY_CURRENT_STATUS_BEGIN -->"
        assert text.index(STATUS_END) < text.index(capability_marker)
    owner = (ROOT / ".docs/rw0-b2-wire-protocol.md").read_text(encoding="utf-8")
    for heading in (
        "## Additive cancellation-control value",
        "## Exact-current cancellation-control relations",
        "## Supplied cancellation-control classifier",
        "## Cancellation-control profile identity",
        "## Cancellation-control reconstruction and work bounds",
        "## Cancellation-control nonclaims",
    ):
        assert owner.count(heading) == 1
    assert PROFILE_REF_V1 in owner and PROFILE_DIGEST_V1 in owner
    registry = STATUS_PATHS[0].read_text(encoding="utf-8")
    assert sum(
        line.startswith("| RW0-B2-Wire |") for line in registry.splitlines()
    ) == 1
    assert "| rw0-wire-cancellation-control-v1 |" not in registry


def test_capability_b1_and_c2a_identifiers_do_not_churn() -> None:
    assert wire.wire_profile_mapping()["profile_ref"] == "rw0-wire-nwpf-v1"
    assert wire.wire_profile_mapping()["profile_digest"] == (
        "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
    )
    assert capability._WIRE_PROFILE_REF == "rw0-wire-nwpf-v1"
    assert capability._WIRE_PROFILE_DIGEST == (
        "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
    )
    assert phase.RW0PhaseEntryBasisV1._SCHEMA == (
        "governed-execution.nwp-rw0-phase-entry-basis.v1"
    )
    assert phase.RW0TerminalOutcomeV1._SCHEMA == (
        "governed-execution.nwp-rw0-terminal-outcome-value.v1"
    )
    manifest = CandidateCapsuleManifestV1.from_mapping(
        _full_record("CandidateCapsuleManifestV1")
    )
    assert manifest.schema_id == (
        "governed-execution.nwp-candidate-capsule-manifest.v1"
    )
    assert manifest.portable_capsule_digest == (
        "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c"
    )


def test_capability_p01_row_matches_final_wire_identity() -> None:
    source = ROOT / "src/ge_nwp_coordinator/_rw0_wire_protocol_values.py"
    raw = source.read_bytes()
    rows = [row for row in PROTECTED_CONTENT_ROWS if row[0] == "P01"]
    assert len(rows) == 1
    row = rows[0]
    assert row[1] == "src/ge_nwp_coordinator/_rw0_wire_protocol_values.py"
    assert row[2] == len(raw)
    assert row[3] == hashlib.sha256(raw).hexdigest()
    assert row[4:] == (
        ("authority_non_effect",),
        "protected Wire implementation",
    )
