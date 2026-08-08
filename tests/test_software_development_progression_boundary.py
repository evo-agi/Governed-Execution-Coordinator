from pathlib import Path
import re
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ".docs/software-development-progression-boundary.md"
C0_HEADINGS = (
    ("C0-SD-001", "Tranche Boundary"),
    ("C0-SD-002", "Target Status"),
    ("C0-SD-003", "Identity Non-Collapse"),
    ("C0-SD-004", "Current FiniteBacklog Compatibility"),
    ("C0-SD-005", "Immutable Revision History And Explicit Supersession"),
    ("C0-SD-006", "Stale Proposal Containment"),
    ("C0-SD-007", "Attempt, Effect, Delivery, And Invocation Separation"),
    ("C0-SD-008", "Ambiguity And Safe Reconciliation"),
    ("C0-SD-009", "Observations Are Not Semantic Decisions"),
    ("C0-SD-010", "Stop And Cancellation Compatibility"),
    ("C0-SD-011", "Publication Separation"),
    ("C0-SD-012", "Private-Material And Evidence Custody"),
    ("C0-SD-013", "Executable Authority Binding"),
    ("C0-SD-014", "Ambiguity Vocabulary Is Not A Universal State Machine"),
    ("C0-SD-015", "Implementation And Cross-Repository Choices Remain Open"),
)


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _doc() -> str:
    return _text(DOC_PATH)


def _compact(text: str) -> str:
    return " ".join(text.split())


def _markdown_atx_headings(text: str) -> tuple[tuple[int, str], ...]:
    """Parse ATX headings outside closed backtick or tilde fenced blocks."""
    headings: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if indent <= 3 and stripped and stripped[0] in "`~":
            marker = stripped[0]
            run_length = len(stripped) - len(stripped.lstrip(marker))
            remainder = stripped[run_length:]
            if run_length >= 3:
                if fence is None:
                    fence = (marker, run_length)
                    continue
                if marker == fence[0] and run_length >= fence[1] and not remainder.strip():
                    fence = None
                    continue
        if fence is None and indent <= 3:
            match = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
            if match is not None:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
                assert title
                headings.append((len(match.group(1)), title))
    assert fence is None, "unclosed or mismatched fenced code block"
    return tuple(headings)


def _c0_heading_inventory(text: str) -> tuple[tuple[str, str], ...]:
    expected = {
        identifier: f"{identifier} - {title}" for identifier, title in C0_HEADINGS
    }
    observed: list[tuple[str, str]] = []
    for level, heading in _markdown_atx_headings(text):
        identifiers = re.findall(r"C0-SD-\d{3}", heading)
        for identifier in identifiers:
            assert identifier in expected
            assert level == 3
            assert heading == expected[identifier]
            observed.append((identifier, heading.removeprefix(f"{identifier} - ")))
    assert tuple(observed) == C0_HEADINGS
    return tuple(observed)


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
    assert _c0_heading_inventory(_doc()) == C0_HEADINGS


def test_c0_clause_inventory_rejects_identifier_and_heading_mutations() -> None:
    text = _doc()
    first = "### C0-SD-001 - Tranche Boundary"
    second = "### C0-SD-002 - Target Status"
    fenced_shadow = (
        text
        + "\n```markdown\n"
        + "### C0-SD-999 - Fenced Unknown\n"
        + "### C0-SD-001 — Fenced Alternate Duplicate\n"
        + "```\n"
    )
    assert _c0_heading_inventory(fenced_shadow) == C0_HEADINGS

    swapped_titles = text.replace(
        first,
        "### C0-SD-001 - Target Status",
        1,
    ).replace(
        second,
        "### C0-SD-002 - Tranche Boundary",
        1,
    )
    reordered = text.replace(first, "### C0-SD-TEMP", 1).replace(
        second,
        first,
        1,
    ).replace("### C0-SD-TEMP", second, 1)
    mutations = (
        text + "\n### C0-SD-001 — Tranche Boundary\n",
        text + "\n ### C0-SD-001: Tranche Boundary\n",
        text + "\n### C0-SD-999 - Unknown Clause\n",
        text + "\n" + first + "\n",
        text.replace(first, "### C0-SD-001 - Wrong Title", 1),
        swapped_titles,
        text.replace(first, "### C0-SD-001 - Tranche boundary", 1),
        text.replace(first + "\n", "", 1),
        reordered,
        text + "\n```markdown\n### C0-SD-999 - Unclosed Fence\n",
        text + "\n```markdown\n### C0-SD-999 - Mismatched Fence\n~~~\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _c0_heading_inventory(mutation)


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
        "The worker invocation authors candidate bytes",
        "a capsule builder acting at the worker boundary seals a canonical manifest, blobs, and portable digest",
        "a private, immutable, content-addressed worker-side store outside the mutable worktree and Coordinator SQLite has physical custody",
        "Coordinator may retain only a safe capsule digest/reference and progression decisions",
        "Reviewer retrieval is read-only, attempt-bound, and capsule-bound",
        "later ES transport or retention is opaque",
        "A capsule digest is not a path, endpoint, bearer retrieval credential, authorization proof, acceptance decision, or Git identity",
        "one local feature-branch Git commit after Coordinator semantic acceptance and a separately selected Git effect",
        "The worker must not silently commit during authoring.",
        "Push, remote-ref mutation, PR creation, merge, and deployment are blocked first-slice effects",
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
        "durable effect intent MUST bind an immutable, externally issued, scope-compatible standing authority reference or verified decision",
        "External standing-policy authority authors the immutable grant, revocation or expiry, applicable global-stop directives, and effect ceilings.",
        "Coordinator MUST NOT mint, renew, widen, reinterpret, or silently reuse that external standing authority",
        "Coordinator may derive a narrower subordinate attempt/effect authorization record and issue a fence within the verified parent grant",
        "binds the parent grant and exact program version, work item, semantic attempt, and effect",
        "cannot exceed or outlive the parent",
        "fails closed on absence, staleness, expiry, revocation, ambiguity, or insufficiency",
        "is not a new grant issuer",
        "only when its immutable scope and ceilings expressly permit bounded reuse",
        "each subordinate binding is explicit",
        "The external authority does not write Coordinator SQLite directly",
        "Coordinator's durable record does not become independent external authority",
        "Current subordinate-authorization runtime behavior remains absent.",
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


def test_c1_supersedes_c0_first_slice_architecture_choices() -> None:
    open_decisions = _compact(_section(_doc(), "Required Gates, Explicit Non-Claims, And Open Decisions"))

    for phrase in (
        "C1 supersedes C0's open alternatives for the first software-development slice",
        "worker source and initial release machinery live in the Coordinator repository",
        "the worker runs as a separate OS process",
        "a bounded direct-local bootstrap/proof route precedes later ES routing through the same versioned contracts",
        "Bridge and Bridge Core are not worker owners",
        "the first private immutable content-addressed capsule has worker-side custody",
        "external standing authority and subordinate Coordinator records are distinct",
        "the maximum effect is one local feature-branch Git commit after acceptance",
    ):
        assert phrase in open_decisions


def test_remaining_implementation_and_cross_repository_details_stay_open() -> None:
    open_decisions = _compact(_section(_doc(), "Required Gates, Explicit Non-Claims, And Open Decisions"))

    for phrase in (
        "The remaining implementation details are exact schema and migration design",
        "current-state tables versus event sourcing",
        "outbox/inbox design",
        "service/API/IPC/queue/scheduler mechanics",
        "worker package, executable, build, supervisor, credential, and IPC mechanics",
        "worker command/observation/fence and capsule DTO fields and wire encoding",
        "ES request/response/correlation/query/cancellation/result-ingest wire contracts",
        "model provider, model protocol, and prompt transport",
        "authority issuer/verifier deployment, encoding, signer, trust root, revocation transport, and credential form",
        "Git commands, branch naming, commit-message format, credentials, CI transport, and publisher implementation",
        "capsule path, storage technology, encryption, garbage collection, retention, serialization, and recovery",
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
        "C0 and C1 accept the semantic and staged architecture direction",
        "a separately accepted implementation contract must freeze the applicable versioned worker command/observation/fence/capsule contract, authority binding, safe-reference policy, observation semantics, effect and retry semantics, stop semantics, direct-local or ES adapter contract, and privacy posture",
        "before source, schema, service, worker, adapter, Git/CI, or runtime execution work",
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
