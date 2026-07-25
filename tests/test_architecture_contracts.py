from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.split())


def test_docs_are_source_of_truth_and_pin_p1_scope() -> None:
    agents = _compact(_text("AGENTS.md"))
    contract = _compact(_text(".docs/a2-p1-contract.md"))
    architecture = _compact(_text(".docs/architecture.md"))
    assert "If `.docs/` exists, always treat `.docs/` as the source of truth." in agents
    for phrase in (
        "bounded internal durable SQLite mutation authority",
        "internal durable writer issuance",
        "writer-fenced transition/global-stop apply",
        "private atomic transition persistence",
        "private atomic global-stop persistence",
        "verification of already-persisted operator-decision receipts",
        "idempotency, CAS, exact replay",
        "commit uncertainty",
        "cannot self-authorize",
        "Reports are projections only",
        "does not own or implement a worker",
        "decision-receipt provisioner",
        "executable authorization issuer",
        "Historical tranche freeze",
    ):
        assert phrase in agents or phrase in contract or phrase in architecture


def test_repository_name_independence_is_documented() -> None:
    naming = _text(".docs/repository-naming.md")
    architecture = _text(".docs/architecture.md")
    assert "Current repository name: Governed Execution Coordinator." in architecture
    assert "schema, authority, or durable identifiers" in architecture
    assert "Schema ids and durable identities must remain independent of repo display" in naming


def test_schema_ids_do_not_embed_repository_display_name() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    assert "governed-execution.nwp-standing-lease.v1" in source
    assert "governed-execution.nwp-work-item-state.v1" in source
    assert "Governed Execution Coordinator" not in source


def test_docs_pin_authority_boundaries() -> None:
    text = _compact(_text(".docs/authority-boundaries.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))
    for phrase in (
        "Bridge remains worker/evidence adapter only",
        "Control Plane remains relevant only to current maintained MVP/demo compatibility, migration, filming, freeze, reference, or retirement context",
        "CP does not become A2 coding-work state owner and is not part of the target autonomous-development topology",
        "Execution Substrate remains execution admission/runtime authority",
        "Maintenance Agent remains maintenance authority",
        "Infrastructure Manager remains readiness, provenance, profile, diagnostics",
        "does not create durable A2 state",
        "Receipt provisioning remains a separately governed operator/repo-policy integration seam",
        "no public, orchestration, worker, service, connector, CLI, or cross-repository authority is added",
    ):
        assert phrase in text

    target_topology = worker.split("## Target Topology", 1)[1].split(
        "## Desired Development State", 1
    )[0]
    assert "Worker Execution Boundary" in target_topology
    assert "Execution Substrate" in target_topology
    assert "CP" not in target_topology


def test_docs_pin_closed_schemas_fixed_p1_gates_and_typed_projections() -> None:
    contract = _text(".docs/a2-p1-contract.md")
    durable = _text(".docs/durable-state-model.md")
    architecture = _text(".docs/architecture.md")
    lease = _text(".docs/lease-identity-and-authorization.md")
    assert "Unknown fields, misspelled" in lease
    assert "before canonicalization and before digest comparison" in lease
    assert "P1 exposes no production API" in contract
    assert "stage_not_enabled" in durable
    assert "Report projections are closed typed models" in architecture
    assert "test-only fixture policy" not in contract


def test_historical_p1_contract_is_not_current_whole_repo_status() -> None:
    contract = _compact(_text(".docs/a2-p1-contract.md"))
    architecture = _compact(_text(".docs/architecture.md"))
    assert "Historical tranche freeze" in contract
    assert "must not be read as the current whole-repository implementation status" in contract
    assert "P1/P1.1 remains historical contract context, not the current whole-repository status" in architecture
    assert "The public `StateStore` remains unwidened" in architecture


def test_worker_boundary_separates_current_implementation_from_target() -> None:
    agents = _compact(_text("AGENTS.md"))
    architecture = _compact(_text(".docs/architecture.md"))
    durable = _compact(_text(".docs/durable-state-model.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))

    assert "Status: target contract/design record only." in worker
    assert "This document enables no runtime implementation, no wire schema, no transport, and no placement." in worker
    assert "Coordinator currently owns bounded internal durable SQLite mutation authority for coding-work state." in worker
    assert "The public `StateStore` remains unwidened." in worker
    assert "Coordinator currently has no worker, scheduler, queue consumer, dispatcher, reconciler, public service/API, Codex invocation, Execution Substrate handoff" in worker
    assert "Strategic target direction is separate from current implementation facts." in architecture
    assert "Coordinator is intended to become the durable autonomy core for software development progression" in architecture
    assert "This target direction is not implemented by the current code and does not authorize execution." in architecture
    assert "This repository currently implements none of those placements, no dispatcher, no reconciler, no service/API/IPC, no ES call" in agents
    assert "The current finite-backlog, standing-lease, zero-only budget, READY-only dependency, and disabled-stage contracts remain current v1 behavior but are not frozen as the target model." in durable


def test_worker_boundary_pins_target_fact_ownership_and_non_authority() -> None:
    authority = _compact(_text(".docs/authority-boundaries.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))

    for phrase in (
        "Coordinator-owned target facts include:",
        "semantic attempt identity",
        "desired progression",
        "durable dispatch intent",
        "retry or repair decision",
        "cancellation intent",
        "reconciliation decision",
        "evidence requirements",
        "acceptance progression",
        "Externally owned facts include:",
        "ES admission decision",
        "ES `run_id`",
        "ES/Nomad lifecycle observation",
        "ES cancel-request receipt",
        "terminal runtime observation",
        "retained-result reference",
        "adapter invocation/session reference",
        "Git object/ref identity",
        "validation observation",
        "Retaining a reference does not transfer ownership of the external fact.",
    ):
        assert phrase in worker

    assert "A worker adapter, widened Bridge adapter, or future gateway may own only bounded placement-specific protocol mechanics" in authority
    assert "It must not own durable work selection, scheduling policy, semantic retry or repair authority, acceptance, ES admission, runtime lifecycle truth, Git truth, validation truth, or hidden program state." in authority


def test_worker_boundary_keeps_placement_open_and_bridge_non_mandatory() -> None:
    readme = _compact(_text("README.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))
    placement = worker.split("## Placement Alternatives", 1)[1].split(
        "## Private Material And Safe Projections", 1
    )[0]

    assert "in-process Coordinator adapter" in placement
    assert "explicitly widened Bridge adapter" in placement
    assert "separate stateless gateway" in placement
    assert "Placement is a deployment and implementation decision after placement-neutral contracts exist." in placement
    assert "A separate gateway is not justified merely for conceptual neatness." in placement
    assert "Bridge is not selected as mandatory adapter placement by this tranche." in placement
    assert "Bridge is not selected as mandatory future worker placement by this tranche." in readme


def test_worker_boundary_pins_effect_ordering_and_attempt_semantics() -> None:
    authority = _compact(_text(".docs/authority-boundaries.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))

    for phrase in (
        "External I/O does not occur inside the SQLite mutation transaction.",
        "A recoverable durable effect intent must exist before an external dispatch effect is attempted.",
        "Delivery acknowledgement is not runtime admission.",
        "An ES submit receipt is not semantic work acceptance.",
        "An unknown dispatch outcome remains unknown until it is reconciled.",
        "Transport redelivery is not a new semantic attempt.",
        "A new semantic attempt requires a Coordinator decision.",
        "Observations cannot silently advance desired state without Coordinator evaluation.",
        "This document does not freeze outbox/inbox as mandatory.",
        "Equivalent designs must satisfy the same recovery and authority invariants.",
    ):
        assert phrase in worker

    assert "External I/O must not occur inside the SQLite mutation transaction boundary." in authority


def test_worker_boundary_records_es_submit_ambiguity_as_blocker() -> None:
    authority = _compact(_text(".docs/authority-boundaries.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))

    for phrase in (
        "The current ES public submit contract returns an internally generated `run_id` after successful submit.",
        "The current public contract does not expose a caller-supplied submit idempotency key, dispatch command identity, or query-by-dispatch-command recovery path.",
        "An accepted submit whose response is lost can therefore be ambiguous to a caller.",
        "ES submit ambiguity is a blocker to reliable real dispatch.",
        "Reliable real dispatch requires an ES-owned idempotency, correlation, or recovery decision, or an explicitly bounded bootstrap exception.",
        "This Coordinator document does not define that ES contract.",
    ):
        assert phrase in worker

    assert "Coordinator must not compensate by inventing a second ES lifecycle store, scraping Nomad as its own authority, or treating trace/request IDs as recovery authority." in authority
    assert "scraping Nomad as Coordinator authority" in worker
    assert "storing a parallel submitted-execution lifecycle truth" in worker


def test_worker_boundary_pins_private_projection_limits_and_negative_non_claims() -> None:
    worker = _compact(_text(".docs/worker-execution-boundary.md"))
    negative = worker.split("## Explicit Non-Claims", 1)[1].split(
        "## Required-Before-Real-Dispatch Gates", 1
    )[0]

    assert "Public reports must not contain raw prompts, raw Codex JSONL, raw logs, credentials, trust material, local absolute paths, private endpoints, retained bundles, or arbitrary runtime payloads." in worker
    assert "Retained bundles remain ES-owned opaque results." in worker
    assert "Raw/private context-package or worker-input storage is not decided by this tranche" in worker

    for phrase in (
        "no worker or Codex invocation",
        "no scheduler",
        "no dispatcher or reconciler",
        "no service/API/IPC",
        "no schema or migration",
        "no outbox/inbox implementation",
        "no ES call",
        "no Bridge widening",
        "no selected gateway service",
        "no connector dependency",
        "no Development Program prerequisite",
        "no full event-sourcing decision",
        "no direct-local-Codex target path",
        "no runtime-profile selection",
        "no authority issuance implementation",
        "no publication behavior",
    ):
        assert phrase in negative


def test_current_status_drift_corrections_are_documented() -> None:
    durable = _compact(_text(".docs/durable-state-model.md"))
    operations = _compact(_text(".docs/sqlite-operations-and-recovery.md"))

    assert "B3c4b adds private atomic transition persistence, B3c4c adds guarded public transition delegation, B4b adds private global-stop persistence, and B4c adds guarded public global-stop delegation." in durable
    assert "The public `StateStore` remains unwidened; internal `WriterSession` mutation is not a general public `StateStore` backend or service." in durable
    assert "The code still has no dispatch, semantic attempt, runtime-observation, result-ingest, outbox/inbox, worker, scheduler, queue, Codex, ES handoff, or runtime lifecycle storage." in durable
    assert "Public global-stop mutation now delegates through the guarded B4c public wrapper to B4b private atomic global-stop persistence." in operations
    assert "The public wrappers own no SQL, receipt verification, evaluator, sequence allocation, write, rollback, COMMIT, or uncertainty handling" in operations
