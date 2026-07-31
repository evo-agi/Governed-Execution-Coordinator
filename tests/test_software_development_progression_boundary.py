from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ".docs/software-development-progression-boundary.md"


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _doc() -> str:
    return _text(DOC_PATH)


def _compact(text: str) -> str:
    return " ".join(text.split())


def _section(text: str, heading: str, next_heading: str | None = None) -> str:
    marker = f"## {heading}"
    body = text.split(marker, 1)[1]
    if next_heading is not None:
        body = body.split(f"## {next_heading}", 1)[0]
    return body


def test_c0_status_current_reality_and_target_only_nonimplementation() -> None:
    status = _compact(_section(_doc(), "Status And Current Reality", "Relationship To Owner-Neutral And Adjacent Boundaries"))

    for phrase in (
        "C0 changes documentation and contract tests only.",
        "MUST NOT add or change source behavior, schema or migration, dependencies, package exports",
        "services, APIs, IPC, queues, workers, schedulers, adapters",
        "ES or Bridge integration, Codex or model invocation, Git or CI integration",
        "publication behavior, executable-authority issuance, or autonomous progression",
        "does not report a durable development-program model, worker, dispatcher, observation ingest, publication path, repair executor, or autonomous loop as implemented",
        "program-native software-development progression domain owned durably by Coordinator",
        "This is target-only.",
        "Current Coordinator remains the bounded durable coding-work SQLite authority described by current contracts",
        "Reports, traces, generated artifacts, model sessions, model responses, and chat remain non-authoritative",
    ):
        assert phrase in status


def test_adjacent_boundaries_are_referenced_without_creating_universal_kernel() -> None:
    relationship = _compact(
        _section(
            _doc(),
            "Relationship To Owner-Neutral And Adjacent Boundaries",
            "Software-Development Scope And FiniteBacklog Compatibility",
        )
    )

    for phrase in (
        ".docs/worker-execution-boundary.md",
        ".docs/operational-progression-boundary.md",
        "already-frozen owner-neutral mechanics",
        "MUST NOT create or imply one universal queue, backlog, lease, work-item/state grammar, state machine",
        "retry or repair counter, dependency receipt model, global stop, acceptance grammar, effect vocabulary",
        "schema, service, module, worker, scheduler, or reconciler",
        "Software-development target semantics are separately versioned from bounded operational-change semantics.",
    ):
        assert phrase in relationship


def test_c0_clause_inventory_is_complete_and_stable() -> None:
    ids = re.findall(r"^### (C0-SD-\d{3}) - ", _doc(), flags=re.MULTILINE)
    assert ids == [f"C0-SD-{index:03d}" for index in range(1, 16)]


def test_identity_and_program_version_non_collapse_are_pinned() -> None:
    scope = _compact(
        _section(
            _doc(),
            "Software-Development Scope And FiniteBacklog Compatibility",
            "Identity, Revision, Supersession, And Proposal Containment",
        )
    )

    for phrase in (
        "development program",
        "`program_version` or equivalent expected revision",
        "accepted-intent revision",
        "objective revision",
        "work-graph revision",
        "work unit and work-unit revision",
        "future execution-batch identity, if used",
        "semantic attempt",
        "progression decision",
        "effect intent",
        "delivery or dispatch attempt",
        "external invocation or source reference",
        "source observation",
        "semantic acceptance or another semantic decision",
        "publication eligibility",
        "publication intent",
        "publication effect",
        "publication observation",
        "`program_version` is a Coordinator concurrency coordinate",
        "MUST NOT collapse into accepted-intent revision, objective revision, work-graph revision, Git revision, ES lifecycle revision, or source-observation revision",
        "Objective revision is semantically distinct from accepted-intent revision",
        "does not require a separate storage aggregate, API, or table",
    ):
        assert phrase in scope


def test_finite_backlog_v1_remains_compatibility_not_target_truth() -> None:
    scope = _compact(
        _section(
            _doc(),
            "Software-Development Scope And FiniteBacklog Compatibility",
            "Identity, Revision, Supersession, And Proposal Containment",
        )
    )

    for phrase in (
        "`FiniteBacklog` v1 remains unchanged as the current immutable, closed-world, digest-bound coding-work compatibility contract",
        "not target program truth",
        "accepted-intent truth",
        "objective truth",
        "work-graph truth",
        "semantic-attempt truth",
        "effect truth",
        "semantic-acceptance truth",
        "publication truth",
        "or the enduring target execution-batch model",
        "maps `FiniteBacklog` v1 to a future execution-batch concept",
        "adapts it into program-native work",
        "replaces it with a versioned successor",
        "retires it through an explicit migration",
    ):
        assert phrase in scope


def test_immutable_revisions_supersession_lineage_and_stale_proposals() -> None:
    revisions = _compact(
        _section(
            _doc(),
            "Identity, Revision, Supersession, And Proposal Containment",
            "Attempts, Effects, Delivery, And Invocation",
        )
    )

    for phrase in (
        "Accepted-intent, objective, work-graph, and work-unit revisions MUST append immutably",
        "rather than rewrite prior durable truth",
        "MUST explicitly identify what is selected, preserved, amended, superseded, split, merged, abandoned, or cancelled",
        "Supersession MAY be partial.",
        "Split and merge operations preserve explicit lineage.",
        "Previously accepted results MAY remain usable when an explicit progression decision preserves their semantic relevance.",
        "does not select a graph schema, dependency grammar, or persistence layout",
        "MUST bind the Coordinator `program_version` or equivalent expected revision on which it was based",
        "A stale proposal remains evidence only.",
        "explicit re-evaluation, rejection, rebasing, or another new Coordinator decision",
        "Model sessions and model responses are not durable program truth.",
    ):
        assert phrase in revisions


def test_attempt_effect_delivery_invocation_and_special_progression_are_separate() -> None:
    attempts = _compact(
        _section(
            _doc(),
            "Attempts, Effects, Delivery, And Invocation",
            "Observations, Ambiguity, And Reconciliation",
        )
    )

    for phrase in (
        "productive semantic attempt",
        "one or more durable implementation, validation, or review effect intents",
        "zero or more delivery or dispatch attempts",
        "zero or more source-owned invocation or run references",
        "A new semantic attempt requires an explicit Coordinator progression decision.",
        "Re-delivering or reconciling one durable effect does not itself create a new semantic attempt.",
        "A repair is normally a new semantic attempt.",
        "Cancellation and publication may reuse generic effect/delivery mechanics",
        "not automatically children of the productive semantic attempt",
        "cancellation progression decision",
        "cancellation effect intent",
        "cancellation receipt and later source observation",
        "publication progression decision",
        "publication effect intent",
        "Git or owner-source publication observations",
        "does not select worker commands, transport DTOs, retry budgets, or dispatch protocols",
    ):
        assert phrase in attempts


def test_ambiguity_preserves_effect_intent_and_does_not_define_es_algorithm() -> None:
    observations = _compact(
        _section(
            _doc(),
            "Observations, Ambiguity, And Reconciliation",
            "Stop, Cancellation, Publication, Authority, And Custody",
        )
    )

    for phrase in (
        "A lost acknowledgement preserves the original durable effect intent",
        "creates an ambiguous external outcome",
        "Reconciliation, query, waiting, containment, or a later delivery attempt remains associated with that same effect intent",
        "allowed only when the owning action or transport contract establishes that re-delivery is safe",
        "Ambiguity alone never authorizes blind retry",
        "never proves admission",
        "never proves non-admission",
        "MUST NOT assume or specify the in-flight ES reliable-submit or Nomad-reconciliation algorithm",
    ):
        assert phrase in observations


def test_observations_are_not_acceptance_repair_replan_publication_or_completion() -> None:
    observations = _compact(
        _section(
            _doc(),
            "Observations, Ambiguity, And Reconciliation",
            "Stop, Cancellation, Publication, Authority, And Custody",
        )
    )

    for phrase in (
        "External observations are source-attributed facts or evidence.",
        "an observation MUST NOT directly advance desired state or become semantic acceptance, repair, replan, publication, or program completion",
        "source observation != semantic acceptance",
        "successful process exit != accepted change",
        "ES terminal state != accepted work",
        "validation success != publication",
        "Git commit or ref != program completion",
        "cancellation receipt != termination proof",
        "source termination observation != successful cancellation semantics",
        "Acceptance, retry, repair, replan, block, supersession, abandonment, and publication progression are explicit Coordinator decisions.",
    ):
        assert phrase in observations


def test_global_stop_compatibility_avoids_evaluator_or_error_precedence_claims() -> None:
    stop = _compact(
        _section(
            _doc(),
            "Stop, Cancellation, Publication, Authority, And Custody",
            "Required Gates, Explicit Non-Claims, And Open Decisions",
        )
    )

    for phrase in (
        "Current coding `global_stop` remains unchanged.",
        "strongest current coding-effect authority gate under present contracts",
        "MUST NOT weaken, reinterpret, clear, replace, or generalize its current authority",
        "A stop directive, cancellation intent, cancellation receipt, source termination observation, and semantic abandonment or acceptance remain distinct.",
        "Future program-, work-, attempt-, effect-, or invocation-scoped stops are additive target concepts.",
        "Their hierarchy, precedence, authorization, and exact permissions remain open.",
        "does not define evaluator ordering, returned-reason priority, or interaction with `stage_not_enabled`",
    ):
        assert phrase in stop

    for forbidden in (
        "always evaluated first",
        "determines every returned denial reason",
        "overrides the existing `stage_not_enabled` response order",
        "`global_stop` overrides `stage_not_enabled`",
    ):
        assert forbidden not in stop


def test_publication_private_material_and_report_privacy_boundaries_are_pinned() -> None:
    custody = _compact(
        _section(
            _doc(),
            "Stop, Cancellation, Publication, Authority, And Custody",
            "Required Gates, Explicit Non-Claims, And Open Decisions",
        )
    )

    for phrase in (
        "Semantic acceptance creates publication eligibility at most.",
        "semantic acceptance, publication eligibility, publication progression decision, publication intent, publication effect, Git object/ref/push/PR truth, publication observation, and publication acceptance or completion decision distinct",
        "Git and owner repositories retain object/ref and action truth",
        "does not select Git credentials, Git commands, branch policy, PR policy, publication transport, or publisher placement",
        "Durable Coordinator program truth may contain only the minimal normalized intent, objective or work descriptions, classifications, decisions, hashes, and safe opaque references",
        "Durable does not mean public",
        "Raw prompts, model transcripts, Codex JSONL, unrestricted logs, command output, workspaces, raw diffs, raw retained-result bodies, credentials, endpoints, local paths, and trust material remain separate evidence or custody material",
        "would not make those bytes program authority or semantic-acceptance truth",
        "Public reports and projections remain more restrictive and must preserve current report privacy contracts.",
    ):
        assert phrase in custody


def test_external_executable_authority_binding_and_non_issuance_are_pinned() -> None:
    custody = _compact(
        _section(
            _doc(),
            "Stop, Cancellation, Publication, Authority, And Custody",
            "Required Gates, Explicit Non-Claims, And Open Decisions",
        )
    )

    for phrase in (
        "Planning, proposal formation, and non-effectful reasoning may exist without executable authority.",
        "Before an execution-producing effect becomes eligible for dispatch",
        "before any execution-producing external I/O",
        "durable effect intent MUST bind an immutable, externally issued, scope-compatible authority reference or verified decision",
        "Coordinator MUST NOT mint, renew, widen, reinterpret, or silently reuse executable authority",
        "only when its immutable scope and ceilings expressly permit that use",
        "each binding is explicit",
        "does not select issuer, verifier deployment, encoding, signer, trust root, revocation transport, or wire protocol",
    ):
        assert phrase in custody


def test_ambiguity_vocabulary_is_distinctions_not_universal_state_machine() -> None:
    open_decisions = _compact(_section(_doc(), "Required Gates, Explicit Non-Claims, And Open Decisions"))

    for phrase in (
        "intended, durably recorded, eligible, delivery attempted, acknowledged, externally admitted, observed, terminal observed, semantically accepted, stale, conflicting, blocked, superseded, abandoned, and ambiguous or unknown",
        "These are semantic distinctions.",
        "They are not a mandatory enum, a universal linear lifecycle, or a shared cross-domain state machine.",
        "Different effects and source contracts may expose different subsets.",
        "An ambiguous effect outcome means an external effect may or may not have crossed its boundary.",
        "An unknown or inconclusive observation means available evidence cannot establish the relevant source fact.",
        "MUST NOT collapse those cases",
    ):
        assert phrase in open_decisions


def test_implementation_and_cross_repository_choices_remain_open() -> None:
    open_decisions = _compact(_section(_doc(), "Required Gates, Explicit Non-Claims, And Open Decisions"))

    for phrase in (
        "leaves open schema and migration design",
        "current-state tables versus event sourcing",
        "outbox/inbox design",
        "service/API/IPC/queue/scheduler placement",
        "worker and adapter implementation",
        "Bridge versus gateway versus in-process placement",
        "ES request/response/correlation/query/cancellation/result-ingest wire contracts",
        "model provider, model protocol, prompt transport",
        "authorization issuer/verifier deployment, trust root",
        "Git and CI transports",
        "raw private evidence custody",
        "CP/IM/MA migration, retirement, or integration",
        "stop precedence",
        "final program-completion semantics when intent can continue evolving",
        "C0 and a later strictly pure, transport-neutral Coordinator domain model do not require an ES repository change.",
        "Concrete ES-backed dispatch, reconciliation, cancellation, runtime observation, result ingest, and unattended execution require separately accepted ES and cross-repository contracts.",
    ):
        assert phrase in open_decisions


def test_required_before_source_gates_preserve_c0_non_implementation_scope() -> None:
    open_decisions = _compact(_section(_doc(), "Required Gates, Explicit Non-Claims, And Open Decisions"))

    for phrase in (
        "Required-before-source gates remain future tranche gates",
        "a later tranche must explicitly accept the relevant domain vocabulary, authority binding, safe reference policy, observation semantics, effect and retry semantics, stop semantics, ES or non-ES transport contract, and privacy posture",
        "before source, schema, service, worker, adapter, gateway, Git/CI, or runtime execution work",
    ):
        assert phrase in open_decisions


def test_c0_does_not_add_public_package_dependency_or_schema_surfaces() -> None:
    init_text = _text("src/ge_nwp_coordinator/__init__.py")
    pyproject = tomllib.loads(_text("pyproject.toml"))
    schema_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "schemas", ROOT / "src" / "ge_nwp_coordinator" / "sqlite_migrations")
        for path in root.rglob("*")
        if path.is_file()
    )

    assert pyproject["project"]["dependencies"] == []
    assert "scripts" not in pyproject.get("project", {})

    for token in (
        "DevelopmentProgram",
        "ProgramVersion",
        "AcceptedIntentRevision",
        "ObjectiveRevision",
        "WorkGraphRevision",
        "SemanticAttempt",
        "EffectIntent",
        "DeliveryAttempt",
        "PublicationIntent",
        "SoftwareDevelopmentProgressionBoundary",
    ):
        assert f'"{token}"' not in init_text

    for token in (
        "development_programs",
        "accepted_intent_revisions",
        "objective_revisions",
        "work_graph_revisions",
        "semantic_attempts",
        "effect_intents",
        "delivery_attempts",
        "publication_intents",
        "source_observations",
    ):
        assert token not in schema_sources
