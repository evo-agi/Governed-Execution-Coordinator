from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.split())


def _section(text: str, heading: str, next_heading: str | None = None) -> str:
    body = text.split(heading, 1)[1]
    if next_heading is not None:
        body = body.split(next_heading, 1)[0]
    return body


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
    agents = _compact(_text("AGENTS.md"))
    architecture = _compact(_text(".docs/architecture.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))
    for phrase in (
        "Bridge remains worker/evidence adapter only",
        "Control Plane remains relevant only to current maintained MVP/demo compatibility, migration, filming, freeze, reference, or retirement context",
        "CP does not become A2 coding-work state owner and is not part of the target autonomous-development topology",
        "Execution Substrate remains execution admission/runtime authority",
        "Maintenance Agent currently retains only its bounded current-contract scan, proposal, approval-record, route-matrix/eligibility handling, and bounded foreground invocation behavior",
        "MA is not selected as the general authorization issuer, renewal authority, deployment authority, runtime/lifecycle authority, or durable operational-progression owner",
        "Infrastructure Manager outputs remain readiness evidence, bootstrap provenance, diagnostics, and profile/support evidence",
        "IM is not durable progression, operational acceptance, owner-route, orchestration, or runtime authority",
        "MA/IM survival, migration, or retirement remains open",
        "does not create durable A2 state",
        "Receipt provisioning remains a separately governed operator/repo-policy integration seam",
        "no public, orchestration, worker, service, connector, CLI, or cross-repository authority is added",
    ):
        assert phrase in text

    combined_current_docs = " ".join((agents, architecture, text))
    assert "Maintenance Agent remains maintenance authority" not in combined_current_docs
    assert "Infrastructure Manager remains readiness, provenance, and diagnostics authority" not in combined_current_docs
    assert "Infrastructure Manager remains readiness, provenance, profile, diagnostics, and support-bundle authority" not in combined_current_docs

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
    assert "Coordinator may later become the component-level durable progression owner for governed programs admitted to its target operating model" in architecture
    assert "separately versioned software-development and bounded operational-change domain contracts" in architecture
    assert "The current coding domain remains intact and coding-work-specific." in architecture
    assert "This target direction is not implemented by the current code and does not authorize execution." in architecture
    assert "This repository currently implements none of those placements, no dispatcher, no reconciler, no service/API/IPC, no ES call" in agents
    assert "The current finite-backlog, standing-lease, zero-only budget, READY-only dependency, and disabled-stage contracts remain current v1 behavior but are not frozen as the target model." in durable


def test_operational_progression_boundary_pins_target_only_current_reality_and_worker_boundary() -> None:
    operational = _text(".docs/operational-progression-boundary.md")
    architecture = _compact(_text(".docs/architecture.md"))
    agents = _compact(_text("AGENTS.md"))
    status = _compact(_section(operational, "## 1. Status And Purpose", "## 2. Current Non-Implementation Reality"))
    current = _compact(_section(operational, "## 2. Current Non-Implementation Reality", "## 3. Bounded Operational-Change Domain Definition"))
    relationship = _compact(_section(operational, "## 21. Relationship To The Coding-Specific Worker Execution Boundary"))

    for phrase in (
        "Status: target contract/design record only.",
        "does not implement operational progression, change coding-work runtime behavior, or authorize any effect",
        "sole component-level durable progression authority for governed programs admitted to its target operating model",
        "conceptual shared owner-neutral progression kernel",
        "separately versioned software-development and bounded operational-change domain contracts",
    ):
        assert phrase in status

    for phrase in (
        "Current implementation remains coding-work-specific bounded durable SQLite mutation authority only.",
        "Current `WriterSession` issuance/fencing, transition/global-stop mutation, receipt verification, idempotency, CAS, exact replay, rollback, one COMMIT attempt, commit uncertainty, and retry remain current coding facts.",
        "The public `StateStore` remains unwidened.",
        "Current finite backlog, coding lease, transition, dependency, repair, budget, disabled-stage, and coding `global_stop` contracts remain current implementation facts.",
        "Coordinator currently has no operational-change domain model, operational schema, worker, scheduler, queue consumer, dispatcher, service/API/IPC, ES handoff, operational observation ingest, repair executor, bootstrap executor, publication path, or live operational effect.",
        "Reports remain projections and do not become authority or truth.",
    ):
        assert phrase in current

    assert "The Worker Execution Boundary remains coding-specific and unchanged." in relationship
    assert "No current coding schema, backlog, lease, transition, or `global_stop` is generalized by this document." in relationship
    assert "Worker Execution Boundary remains coding-specific and untouched" in agents
    assert ".docs/operational-progression-boundary.md" in architecture


def test_operational_progression_boundary_pins_domain_and_shared_mechanics_limits() -> None:
    operational = _text(".docs/operational-progression-boundary.md")
    domain = _compact(_section(operational, "## 3. Bounded Operational-Change Domain Definition", "## 4. Shared Owner-Neutral Mechanics Versus Domain-Specific Semantics"))
    shared = _compact(_section(operational, "## 4. Shared Owner-Neutral Mechanics Versus Domain-Specific Semantics", "## 5. Identity And Correlation Non-Collapse"))
    architecture = _compact(_text(".docs/architecture.md"))

    for phrase in (
        "A bounded operational-change program is one finite objective to change, repair, roll back, compensate, contain, bootstrap, or recover a named target",
        "immutable owner action-contract reference",
        "immutable externally issued authority reference",
        "explicit target and desired-generation references",
        "source-attributed preconditions and observations",
        "finite attempt/effect ceilings",
        "explicit acceptance, stop, and operator-intervention conditions",
        "not: - a global desired-environment object",
        "not: - a global desired-environment object; - a continuous drift reconciler",
        "a broad shell/SSH/sudo/helper lane",
        "hidden progression in MA, IM, Bridge, CP, chat, reports, or artifacts",
    ):
        assert phrase in domain

    for phrase in (
        "This list is conceptual.",
        "It creates no schema, module, service, queue, worker, scheduler, reconciler, or source package.",
        "It does not make current coding source a generic kernel.",
        "Software-development and bounded operational-change domains must not share one undifferentiated backlog, lease, work-item/state vocabulary, retry/repair counter, dependency receipt model, global-stop singleton, acceptance grammar, effect vocabulary, or publication/completion rule.",
    ):
        assert phrase in shared

    assert "The target does not select a generic environment controller, topology controller, universal scheduler, capability registry, background probe loop, continuous drift reconciler" in architecture


def test_operational_progression_boundary_pins_authority_and_identity_non_collapse() -> None:
    operational = _text(".docs/operational-progression-boundary.md")
    authority = _compact(_text(".docs/authority-boundaries.md"))
    identities = _compact(_section(operational, "## 5. Identity And Correlation Non-Collapse", "## 6. Safe References And Private Material"))
    safe_refs = _compact(_section(operational, "## 6. Safe References And Private Material", "## 7. External Operational Authorization"))
    auth_section = _compact(_section(operational, "## 7. External Operational Authorization", "## 8. Owner Action-Contract References"))
    owner_contract = _compact(_section(operational, "## 8. Owner Action-Contract References", "## 9. Source Observations, Freshness, Conflict, And Unknown Outcomes"))

    for phrase in (
        "Coordinator program/objective ID",
        "semantic operation ID",
        "effect-intent ID",
        "external authority ID",
        "owner action-contract ID/version",
        "ES reliable-submit key",
        "ES `run_id`",
        "`lifecycle_projection.revision`",
        "CP workflow/run/attempt ID",
        "Bridge/session/assignment/report ID",
        "request/trace/transport/correlation ID",
        "may be explicitly correlated but do not collapse",
    ):
        assert phrase in identities

    for phrase in (
        "Raw credentials, keys, biometric material, TLS/SPIFFE/Vault/WebAuthn/Codex/OpenAI/API-key material",
        "private environment files, unrestricted logs, support-bundle bodies, retained bundle bodies, and private paths/endpoints remain outside Coordinator durable/public state",
        "Persistence, reports, Bridge ledgers, IM profiles/bundles, MA proposals, CP projections/messages, `.out`, retained bundles, trace IDs, request IDs, delivery receipts, and adapter/session records do not become truth by storage.",
    ):
        assert phrase in safe_refs

    for phrase in (
        "Coordinator may verify and bind allowlisted immutable authority references.",
        "Coordinator may not mint, renew, widen, translate, reinterpret, or self-supersede operational authority.",
        "A digest proves byte identity only.",
        "Owner-blocked routes remain blocked.",
        "selects no issuer, verifier, trust root, representation, wire format, credential form, revocation mechanism, or custody topology",
        "externally issued, immutable by Coordinator, owner/route/target/effect scoped, attempt/effect bounded",
        "CP WebAuthn and MA biometric/lease designs are not adopted as the general operational authorization model.",
    ):
        assert phrase in auth_section
        assert phrase in authority or phrase in auth_section

    for phrase in (
        "route/action identity/version",
        "supported target kind",
        "privilege/runtime-profile/identity/secret/signing requirements",
        "idempotency/re-entry",
        "post-check/acceptance inputs",
        "repair/rollback/compensation/containment/manual-recovery behavior",
        "privacy, redaction, receipts, and evidence retention",
        "The owner contract, not Coordinator, defines:",
        "Binding a reference does not transfer owner-route meaning or privilege to Coordinator.",
    ):
        assert phrase in owner_contract

    for phrase in (
        "Git and owning repository retain desired bytes and owner action definitions",
        "owning route/component repository retains action meaning, route eligibility, preconditions, privilege and runtime-profile requirements",
        "external owner/policy authority retains grant issuance and effect ceilings",
        "target Coordinator may safely verify and bind allowlisted immutable authority references and own durable progression decisions",
        "Execution Substrate retains authentication, reliable keyed submit when that future contract is implemented, admission, runtime handoff, lifecycle projection, cancellation-request, and retained-result boundaries",
        "runtime/provider/host source retains observed runtime facts",
        "Control Plane retains current MVP/demo workflow and exact-scope controls only",
        "Bridge/connector retains transport, session, and report evidence only",
        "Git retains object and ref truth",
    ):
        assert phrase in authority


def test_operational_progression_boundary_pins_observations_effects_stop_and_es_gate() -> None:
    operational = _text(".docs/operational-progression-boundary.md")
    observations = _compact(_section(operational, "## 9. Source Observations, Freshness, Conflict, And Unknown Outcomes", "## 10. Required Progression Distinctions"))
    distinctions = _compact(_section(operational, "## 10. Required Progression Distinctions", "## 11. Delivery Retry, Semantic Retry, Repair, Rollback, Compensation,"))
    effects = _compact(_section(operational, "## 11. Delivery Retry, Semantic Retry, Repair, Rollback, Compensation,", "## 12. Operational Domain And Named-Target Scoped Stop"))
    stop = _compact(_section(operational, "## 12. Operational Domain And Named-Target Scoped Stop", "## 13. Owner-Exposed Dependency Vocabulary"))
    dependencies = _compact(_section(operational, "## 13. Owner-Exposed Dependency Vocabulary", "## 14. ES Reliable-Submit Future Gate"))
    es_gate = _compact(_section(operational, "## 14. ES Reliable-Submit Future Gate", "## 15. Bootstrap And Catastrophic-Recovery Exception Requirements"))

    for phrase in (
        "source owner/version, observation ID/revision, target, observed generation/state",
        "observation time, receipt time, authenticity/integrity mechanism, owner-specific freshness, semantic class, safe evidence reference, and redaction class",
        "Missing, stale, unverifiable, target-mismatched, conflicting, late-unbound, or inconclusive evidence remains unknown or blocked.",
    ):
        assert phrase in observations

    assert "desired target generation, admitted owner action, durable effect intent, delivery acknowledgement, runtime/provider observation, post-check observation, acceptance decision, blocked decision, operator-intervention decision, and stop/cancellation intent" in distinctions
    assert "advances desired state without Coordinator evaluation under the admitted domain contract" in distinctions

    for phrase in (
        "delivery retry;",
        "semantic retry;",
        "repair;",
        "rollback;",
        "compensation;",
        "containment;",
        "manual recovery/operator intervention.",
        "Every repair, rollback, compensation, containment, cancellation, and bootstrap effect requires its own durable effect intent before I/O",
    ):
        assert phrase in effects

    assert "Current coding `global_stop` remains untouched." in stop
    assert "operational-domain and named-target scoped" in stop
    assert "A stop intent or cancellation receipt does not prove termination." in stop
    assert "Cross-domain emergency super-stop remains open and non-implemented." in stop
    assert "does not reuse the current coding dependency receipt model as the operational dependency model" in dependencies

    for phrase in (
        "Reliable operational effects through ES are future-only.",
        "ES must independently authenticate, default, validate runtime profile, admit, reliably correlate/recover submit",
        "Operational acceptance remains separate.",
        "Current reliable-submit target docs/model/ADR do not mean implementation.",
        "current unkeyed submit plus blind retry",
        "Coordinator Nomad scraping",
        "Bridge/session/report correlation as recovery truth",
        "trace/request IDs as submit identity",
        "provider IDs as semantic attempt identity",
        "parallel Coordinator or adapter lifecycle truth",
    ):
        assert phrase in es_gate


def test_operational_progression_boundary_pins_bootstrap_sensors_gateway_nonclaims_and_open_decisions() -> None:
    operational = _text(".docs/operational-progression-boundary.md")
    bootstrap = _compact(_section(operational, "## 15. Bootstrap And Catastrophic-Recovery Exception Requirements", "## 16. Sensors May Propose But Not Reconcile"))
    sensors = _compact(_section(operational, "## 16. Sensors May Propose But Not Reconcile", "## 17. Gateway And Adapter Placement Alternatives"))
    gateway = _compact(_section(operational, "## 17. Gateway And Adapter Placement Alternatives", "## 18. Required-Before-Source Gates"))
    gates = _compact(_section(operational, "## 18. Required-Before-Source Gates", "## 19. Explicit Non-Claims"))
    nonclaims = _compact(_section(operational, "## 19. Explicit Non-Claims", "## 20. Open Decisions"))
    open_decisions = _compact(_section(operational, "## 20. Open Decisions", "## 21. Relationship To The Coding-Specific Worker Execution Boundary"))

    for phrase in (
        "A bootstrap or catastrophic-recovery label is not permission.",
        "exact owner/component",
        "exact route/action/version",
        "program/operation/attempt/effect identities",
        "immutable external authority",
        "rollback/compensation/containment/manual recovery",
        "explicit ambiguous/unknown outcome",
        "later owner-source reconciliation",
        "no success without positive owner post-check",
        "must not authorize broad shell, SSH, sudo, arbitrary helper dispatch, credential brokerage, hidden reconciliation, or route widening",
    ):
        assert phrase in bootstrap

    assert "Sensors, probes, reports, Bridge sessions, MA scans, IM diagnostics, CP projections, CI results, and owner-system observations may propose evidence or candidate progression inputs." in sensors
    assert "They do not reconcile operational state, advance desired state, clear stops, accept effects, or close unknown outcomes by themselves." in sensors

    for phrase in (
        "in-process Coordinator adapter",
        "explicitly widened Bridge adapter after separate owner-repo work/audit",
        "separate stateless gateway",
        "This document selects none of them.",
        "must not own durable progression, scheduling, retry, repair, acceptance, ES admission, runtime lifecycle truth, Git truth, validation truth, or hidden program state",
    ):
        assert phrase in gateway

    assert "Before source, schema, service, worker, adapter, gateway, effect-engine, bootstrap, or runtime work" in gates

    for phrase in (
        "no current operational implementation",
        "no source model",
        "no schema or migration",
        "no worker/scheduler/dispatcher/reconciler",
        "no service/API/IPC",
        "no outbox/inbox",
        "no ES call",
        "no Bridge widening",
        "no selected gateway",
        "no authorization issuer or verifier implementation",
        "no observation transport",
        "no stop storage",
        "no bootstrap executor",
        "no effect engine",
        "no first route",
        "no privileged host action",
        "no MA/IM migration decision",
        "no production topology",
        "no continuous drift loop",
        "no current reliable ES operational dispatch",
    ):
        assert phrase in nonclaims

    for index, phrase in enumerate(
        (
            "bounded operational-change domain versioning and exact boundary",
            "external authorization issuer",
            "verifier and trust root",
            "grant representation and wire format",
            "credential form and custody topology",
            "exact operational state vocabulary",
            "schema and storage",
            "observation transport and reconciliation path",
            "stop storage and precedence",
            "cross-domain emergency super-stop",
            "ES reliable-submit implementation details",
            "bootstrap or catastrophic-recovery route",
            "repair, rollback, compensation, containment, and manual-recovery semantics",
            "first owner route/action",
            "gateway or adapter placement",
            "effect engine implementation or explicit no-engine decision",
            "MA/IM survival, migration, or retirement",
            "production topology",
        ),
        start=1,
    ):
        assert f"{index}. {phrase}" in open_decisions


def test_operational_progression_tranche_does_not_add_runtime_or_schema_surfaces() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src/ge_nwp_coordinator").rglob("*.py"))
    schemas = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "schemas").rglob("*") if path.is_file())

    assert not re.search(
        r"OperationalChange|operational_change|BootstrapExecutor|RepairExecutor|background_reconciler|ExecutionSubstrateClient|BridgeAdapter|Gateway",
        source + "\n" + schemas,
    )
    assert not re.search(
        r"CREATE TABLE .*operational|CREATE TABLE .*outbox|CREATE TABLE .*inbox|CREATE TABLE .*dispatch|CREATE TABLE .*runtime",
        schemas,
    )


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
