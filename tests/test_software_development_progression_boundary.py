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


def _require(condition: bool, diagnostic: str) -> None:
    if not condition:
        raise AssertionError(diagnostic)


def _markdown_fence_candidate(content: str) -> tuple[str, int, str] | None:
    stripped = content.lstrip(" ")
    indent = len(content) - len(stripped)
    if indent > 3 or not stripped or stripped[0] not in "`~":
        return None
    marker = stripped[0]
    run_length = len(stripped) - len(stripped.lstrip(marker))
    if run_length < 3:
        return None
    remainder = stripped[run_length:]
    if marker == "`" and "`" in remainder:
        return None
    return marker, run_length, remainder


def _markdown_closer_suffix_is_ascii_space_tab(suffix: str) -> bool:
    return all(character in {" ", "\t"} for character in suffix)


def _markdown_atx_heading_spans(
    text: str,
    *,
    role: str = "progression.markdown",
) -> tuple[tuple[int, str, int, int], ...]:
    """Parse ATX headings outside closed backtick or tilde fenced blocks."""
    headings: list[tuple[int, str, int, int]] = []
    fence: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.lstrip(" ")
        indent = len(content) - len(stripped)
        candidate = _markdown_fence_candidate(content)
        if candidate is not None:
            marker, run_length, remainder = candidate
            if fence is None:
                fence = (marker, run_length)
                offset += len(line)
                continue
            if (
                marker == fence[0]
                and run_length >= fence[1]
                and _markdown_closer_suffix_is_ascii_space_tab(remainder)
            ):
                fence = None
                offset += len(line)
                continue
        if fence is None and indent <= 3:
            match = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
            if match is not None:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
                _require(bool(title), f"{role}|heading=<atx>|failure=empty")
                headings.append((len(match.group(1)), title, offset, offset + len(line)))
        offset += len(line)
    _require(fence is None, f"{role}|heading=<none>|failure=unbalanced_fence")
    return tuple(headings)


def _markdown_atx_headings(text: str) -> tuple[tuple[int, str], ...]:
    return tuple(
        (level, title)
        for level, title, _start, _end in _markdown_atx_heading_spans(text)
    )


def _unfenced_markdown(text: str, *, role: str) -> str:
    visible: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.lstrip(" ")
        indent = len(content) - len(stripped)
        candidate = _markdown_fence_candidate(content)
        if fence is not None:
            if (
                candidate is not None
                and candidate[0] == fence[0]
                and candidate[1] >= fence[1]
                and _markdown_closer_suffix_is_ascii_space_tab(candidate[2])
            ):
                fence = None
            continue
        if candidate is not None:
            fence = (candidate[0], candidate[1])
            continue
        visible.append(line)
    _require(fence is None, f"{role}|heading=<none>|failure=unbalanced_fence")
    return "".join(visible)


def _bounded_markdown_section(
    text: str,
    heading: str,
    level: int,
    *,
    role: str,
    allow_eof: bool = False,
) -> str:
    headings = _markdown_atx_heading_spans(text, role=role)
    matches = tuple(item for item in headings if item[1] == heading)
    _require(bool(matches), f"{role}|heading={heading}|failure=missing")
    _require(len(matches) == 1, f"{role}|heading={heading}|failure=duplicate")
    selected = matches[0]
    _require(selected[0] == level, f"{role}|heading={heading}|failure=wrong_level")
    selected_index = headings.index(selected)
    boundary = next(
        (
            following
            for following in headings[selected_index + 1 :]
            if following[0] <= selected[0]
        ),
        None,
    )
    _require(
        boundary is not None or allow_eof,
        f"{role}|heading={heading}|failure=missing_same_or_higher_boundary",
    )
    end = len(text) if boundary is None else boundary[2]
    return text[selected[3] : end]


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
        "process framing, transport wrapping, and ES wire mapping for the C2A-frozen worker command/observation/fence/capsule semantic fields",
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
        "The pure semantic-contract prerequisite is now satisfied by the accepted C2A document and the current C2A1 internal no-I/O values and six pure coherence validators",
        "Durable schema, authority verification, process launch, worker execution, observation ingest, acceptance runtime, and Git effect remain unsatisfied required-before-runtime gates",
        "A separately accepted implementation contract must still freeze the applicable runtime, direct-local or ES adapter, transport, and persistence mechanics",
        "before schema, service, worker, adapter, Git/CI, or runtime execution work",
    ):
        assert phrase in open_decisions


def test_c0_does_not_add_public_surfaces_and_slice1_schema_remains_physical_only() -> None:
    init_text = _text("src/ge_nwp_coordinator/__init__.py")
    pyproject = tomllib.loads(_text("pyproject.toml"))
    migration_0002 = _text(
        "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql"
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
        "development_program_heads",
        "development_program_versions",
        "development_accepted_intent_revisions",
        "development_semantic_attempts",
        "development_effect_intents",
        "development_delivery_attempts",
    ):
        assert token in migration_0002

    for token in (
        "development_objective_revisions",
        "development_work_graph_revisions",
        "development_publication_intents",
        "development_source_observations",
    ):
        assert token not in migration_0002


def _assert_c2b0_progression_overlay(text: str) -> None:
    heading = "C2B0 Accepted Durable Progression Closure"
    role = "progression.c2b0_summary"
    overlay = _compact(
        _unfenced_markdown(
            _bounded_markdown_section(
                text,
                heading,
                2,
                role=role,
                allow_eof=True,
            ),
            role=f"{role}.section",
        )
    )
    decisions = (
        "initialize",
        "accept",
        "repair",
        "replan",
        "terminal_reject",
        "block",
        "redeliver",
        "cancel",
    )
    ordered_surface = ", ".join(f"`{decision}`" for decision in decisions[:-1])
    ordered_surface += f", and `{decisions[-1]}`"
    _require(
        f"The exact ordered decision kinds are {ordered_surface}." in overlay,
        f"{role}|heading={heading}|failure=target_claim_missing",
    )

    for phrase in (
        "`initialize` creates program version 1 of kind `initial` and preassigns the first semantic attempt and candidate",
        "`cancel` is a distinct immutable decision, advances no program version, preassigns a cancellation effect/fence/first delivery",
        "Every durable effect has a non-null immediate `basis_decision_ref`",
        "An author effect uses the exact `initialize`, `repair`, or attempt-selecting `replan` decision",
        "Validation and review reuse the selection decision bound to the existing attempt",
        "Cancellation uses the exact cancel decision and target",
        "`block` and `terminal_reject` cannot substitute as cancellation bases",
        "Bound validation, review, and cancellation effects reuse that attempt, candidate, AttemptFence, originating command, and post-bound author EffectFence",
        "They create no attempt, candidate, second command, author effect, or program version",
        "A new semantic attempt remains possible only after an explicit attempt-selecting Coordinator decision",
    ):
        _require(
            phrase in overlay,
            f"{role}|heading={heading}|failure=target_claim_missing",
        )
    visible = _unfenced_markdown(text, role=role).lower()
    for forbidden in (
        "Exact C2B schema remains wholly open.",
        "0002 is absent.",
        "0003 is installed.",
        "Application generation is currently 3.",
        "No migration number is reserved.",
        "C2B is currently implemented.",
    ):
        _require(
            forbidden.lower() not in visible,
            f"{role}|heading={heading}|failure=contradictory_current_status",
        )


def test_c2b0_progression_overlay_pins_decisions_bases_and_bound_effect_limits() -> None:
    _assert_c2b0_progression_overlay(_doc())


def test_c2b2_current_private_reader_boundary_preserves_progression_nonimplementation() -> None:
    section = _compact(
        _section(
            _doc(),
            "C2B1/C2B2 Current Migration, Pure-Value, And Private-Reader Boundary",
            "C2B0 Accepted Durable Progression Closure",
        )
    )
    for phrase in (
        "private pure no-I/O row/value validation, private reader behavior, and the bounded private C2B3 route-neutral program-genesis family",
        "Slice 1 uses this administrative boundary at application generation 2",
        "Slice 2 adds private pure row/value source for those nineteen tables",
        "no SQLite or SQL in that pure layer",
        "Slice 3 implements exactly twelve private reader roles",
        "Only the mutation-receipt reader has the bounded private C2B3 caller",
        "no package export, public reader, `StateStore`/public `WriterSession` method",
        "exact nine-row/eight-entry genesis family",
        "Durable development progression beyond the exact initialization decision, source-observation ingest, later semantic decisions",
    ):
        assert phrase in section


def test_c2b0_progression_overlay_is_fence_aware_and_bounded() -> None:
    text = _doc()
    required = "The exact ordered decision kinds are"
    fenced_only = text.replace(required, f"```text\n{required}\n````\n", 1)
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_progression_overlay(fenced_only)
    assert str(rejected.value) == (
        "progression.c2b0_summary|heading=C2B0 Accepted Durable Progression Closure|failure=target_claim_missing"
    )

    boundary = text.replace(
        "Status: `ACCEPTED TARGET CONTRACT`; the C0 historical statements above remain\nhistorical and durable C2B progression remains unimplemented.\n\nThe exact ordered decision kinds are",
        "Status: `ACCEPTED TARGET CONTRACT`; the C0 historical statements above remain\nhistorical and durable C2B progression remains unimplemented.\n\n# Relocated Progression\n\nThe exact ordered decision kinds are",
        1,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_progression_overlay(boundary)
    assert str(rejected.value) == (
        "progression.c2b0_summary|heading=C2B0 Accepted Durable Progression Closure|failure=target_claim_missing"
    )

    contradictory = text + "\n# Contradictory Current Status\n\nC2B is currently implemented.\n"
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_progression_overlay(contradictory)
    assert str(rejected.value) == (
        "progression.c2b0_summary|heading=C2B0 Accepted Durable Progression Closure|failure=contradictory_current_status"
    )


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_authority_bypass() -> None:
    text = _doc()
    mutation = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_progression_overlay(mutation)
    assert str(rejected.value) == (
        "progression.c2b0_summary|heading=C2B0 Accepted Durable Progression Closure|failure=contradictory_current_status"
    )

    valid_tilde = text + "\n~~~bad`info\nC2B is currently implemented.\n~~~\n"
    _assert_c2b0_progression_overlay(valid_tilde)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_duplicate_heading_bypass() -> None:
    text = _doc()
    mutation = (
        text
        + "\n```bad`info\n## C2B0 Accepted Durable Progression Closure\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_progression_overlay(mutation)
    assert str(rejected.value) == (
        "progression.c2b0_summary|heading=C2B0 Accepted Durable Progression Closure|failure=duplicate"
    )


def test_progression_markdown_closer_suffix_is_ascii_space_tab_only() -> None:
    for valid_suffix in ("", " ", "\t", " \t"):
        sample = f"~~~text\n## Hidden\n~~~{valid_suffix}\n## Visible\n"
        headings = _markdown_atx_heading_spans(sample, role="progression.repair3")
        assert tuple(item[1] for item in headings) == ("Visible",)

    for invalid_suffix in ("\u00a0", "\u2003", "not-a-closer"):
        closed_later = (
            "~~~text\n"
            f"~~~{invalid_suffix}\n"
            "C2B is currently implemented.\n"
            "## C2B0 Accepted Durable Progression Closure\n"
            "~~~\n"
        )
        assert _markdown_atx_heading_spans(
            closed_later,
            role="progression.repair3",
        ) == ()
        assert _unfenced_markdown(
            closed_later,
            role="progression.repair3",
        ) == ""

        with pytest.raises(AssertionError) as rejected:
            _markdown_atx_heading_spans(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="progression.repair3",
            )
        assert str(rejected.value) == (
            "progression.repair3|heading=<none>|failure=unbalanced_fence"
        )


def test_narrowed_vertical_slice_progression_ceiling_and_prerequisites_are_exact() -> None:
    document = _doc()
    document_compact = _compact(document)
    assert document.count("<!-- C2B3_NARROWED_PROGRESSION_BEGIN -->") == 1
    assert document.count("<!-- C2B3_NARROWED_PROGRESSION_END -->") == 1
    for expected in (
        "Initialization is route-neutral",
        "author-effect delivery selects the first",
        "`direct_local_bootstrap` bounded direct/non-ES route",
        "one qualified remote Linux host",
        "No Mac fallback or third adapter kind exists.",
        "It is not a frozen program/tranche count.",
        "at most one productive acceptance",
        "at most one isolated feature-",
        "zero push/remote-ref/PR/merge/deploy/publication effects",
        "no blind retry after ambiguity",
        "`qualified_remote_host_readiness_evidence_gate` requires accepted owning-process evidence",
        "one remote Linux host is qualified before real retrieval",
        "process-separated worker or Codex invocation",
        "not identity, authority, progression truth, runtime truth, or permission for Mac or Coordinator-host fallback",
        "`accepted_clean_exact_es_oid_and_owning_repository_contract_adoption_evidence_gate` requires an accepted clean exact ES Git OID",
        "accepted owning-ES-repository contract/adoption evidence",
        "Chat or model reports cannot substitute for either intrinsic gate.",
        "now owns the exact route-neutral initialization, nine-row/eight-entry graph",
        "remain just-in-time questions",
        "planned `direct_local_bootstrap` delivery is not dispatch",
        "Those external-effect questions remain unauthorized.",
    ):
        assert expected in document_compact
    for forbidden in (
        "WorkSpecCustodyReceiptV1",
        "VerifiedAuthorityResultV1",
        "LocalGitCommandV1",
        "LocalGitDeliveryV1",
        "LocalGitObservationV1",
        "canonical_positive_vectors",
        "prerequisite_00061",
        "prerequisite_00054",
    ):
        assert forbidden not in document
