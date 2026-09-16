from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


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


def _markdown_atx_headings(
    text: str,
    *,
    role: str = "architecture.markdown",
) -> tuple[tuple[int, str, int, int], ...]:
    """Parse bounded ATX headings outside backtick or tilde fenced blocks."""
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
    role: str = "architecture.document",
    allow_eof: bool = False,
) -> str:
    headings = _markdown_atx_headings(text, role=role)
    matches = [item for item in headings if item[1] == heading]
    _require(bool(matches), f"{role}|heading={heading}|failure=missing")
    _require(len(matches) == 1, f"{role}|heading={heading}|failure=duplicate")
    selected = matches[0]
    _require(selected[0] == level, f"{role}|heading={heading}|failure=wrong_level")
    selected_index = headings.index(selected)
    boundaries = tuple(
        following
        for following in headings[selected_index + 1 :]
        if following[0] <= level
    )
    _require(
        bool(boundaries) or allow_eof,
        f"{role}|heading={heading}|failure=missing_same_or_higher_boundary",
    )
    end = len(text) if not boundaries else boundaries[0][2]
    return text[selected[3] : end]


_C2B3D_ARCHITECTURE_BEGIN = "<!-- C2B3_NARROWED_ARCHITECTURE_BEGIN -->"
_C2B3D_ARCHITECTURE_END = "<!-- C2B3_NARROWED_ARCHITECTURE_END -->"
_C2B3D_ARCHITECTURE_HEADING = "C2B3 vertical-slice governing narrowing"
_C2B3D_ARCHITECTURE_SUMMARY_START = (
    "Coordinator remains durable-progression authority only."
)
_C2B3D_IMPLEMENTATION_COMMIT = "5e544622e5f46ddc78294322471b4fcbd2ad9172"
_SECTION_41_IMPLEMENTATION_COMMIT = "394d625aa63935140eeaf88ecff6f59f0547cb7e"


def _architecture_heading_chain(
    headings: tuple[tuple[int, str, int, int], ...],
    selected: tuple[int, str, int, int],
) -> tuple[tuple[int, str], ...]:
    stack: list[tuple[int, str, int, int]] = []
    for heading in headings:
        if heading[2] > selected[2]:
            break
        while stack and stack[-1][0] >= heading[0]:
            stack.pop()
        stack.append(heading)
    return tuple((heading[0], heading[1]) for heading in stack)


def _extract_c2b3d_architecture_summary(text: str) -> tuple[int, int, str]:
    role = "architecture.c2b3d_summary"
    headings = _markdown_atx_headings(text, role=role)
    selected_matches = tuple(
        heading for heading in headings if heading[1] == _C2B3D_ARCHITECTURE_HEADING
    )
    _require(
        len(selected_matches) == 1,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=count",
    )
    selected = selected_matches[0]
    _require(
        selected[0] == 2,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=wrong_level",
    )
    _require(
        _architecture_heading_chain(headings, selected)
        == (
            (1, "NWP Coordinator Architecture"),
            (2, _C2B3D_ARCHITECTURE_HEADING),
        ),
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=heading_chain",
    )
    visible = _unfenced_markdown(text, role=role)
    for marker in (_C2B3D_ARCHITECTURE_BEGIN, _C2B3D_ARCHITECTURE_END):
        _require(
            text.count(marker) == visible.count(marker) == 1,
            f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=marker_count",
        )
    begin = text.index(_C2B3D_ARCHITECTURE_BEGIN)
    end_marker = text.index(_C2B3D_ARCHITECTURE_END)
    _require(
        text[begin + len(_C2B3D_ARCHITECTURE_BEGIN) : selected[2]] == "\n",
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=begin_boundary",
    )
    _require(
        text[end_marker + len(_C2B3D_ARCHITECTURE_END) :] == "\n",
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=end_boundary",
    )
    _require(
        visible.count(_C2B3D_ARCHITECTURE_SUMMARY_START) == 1,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=summary_count",
    )
    summary_start = text.index(
        _C2B3D_ARCHITECTURE_SUMMARY_START,
        selected[3],
        end_marker,
    )
    _require(
        text[summary_start - 2 : summary_start] == "\n\n",
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=paragraph_start",
    )
    nested_headings = tuple(
        heading
        for heading in headings
        if selected[3] <= heading[2] < end_marker
    )
    _require(
        not nested_headings,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=nested_heading",
    )
    summary = text[summary_start:end_marker]
    _require(
        summary.endswith("Exact later-phase values and\nevidence layouts remain deferred.\n"),
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=paragraph_end",
    )
    _require(
        "COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE" not in summary,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=cross_reference_overlap",
    )
    return summary_start, end_marker, summary


def _assert_c2b3d_architecture_summary_text(summary: str) -> None:
    role = "architecture.c2b3d_summary"
    normalized = _compact(summary)
    _require(
        normalized.count(_C2B3D_IMPLEMENTATION_COMMIT) == 1,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=c2b3d_commit",
    )
    _require(
        _SECTION_41_IMPLEMENTATION_COMMIT not in normalized,
        f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=section41_commit_substitution",
    )
    for required in (
        _C2B3D_ARCHITECTURE_SUMMARY_START,
        "The private C2B3D implementation was introduced and is committed at",
        "Git owns the committed object and ref fact",
        "independent acceptance, audit, validation, provenance, and report records remain external evidence rather than Coordinator durable authority or effect permission",
        "exactly ten author-effect rows and nine supplied graph entries",
        "planned `direct_local_bootstrap` delivery as inert intent",
        "performs no dispatch, worker, capsule, credential, network, Git, Bridge, or ES effect",
        "Exact later-phase values and evidence layouts remain deferred.",
    ):
        _require(
            required in normalized,
            f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=required",
        )
    lowered = normalized.lower()
    for forbidden in (
        "private c2b3d candidate",
        "current working tree contains",
        "uncommitted candidate",
        "awaits fresh independent audit",
        "pending fresh independent audit",
        "independent acceptance remains pending",
        "reports own git truth",
        "audit acceptance is coordinator durable authority",
        "model output grants effect permission",
        "c2b3d performs worker",
    ):
        _require(
            forbidden not in lowered,
            f"{role}|heading={_C2B3D_ARCHITECTURE_HEADING}|failure=forbidden",
        )


def _assert_c2b3d_architecture_summary_document(text: str) -> str:
    _start, _end, summary = _extract_c2b3d_architecture_summary(text)
    _assert_c2b3d_architecture_summary_text(summary)

    from test_c2b3c_author_effect_contract import (
        LIVE_C2B3D_SUMMARY_INVENTORY,
        _assert_live_c2b3d_summary_document,
    )

    shared_spec = next(
        spec
        for spec in LIVE_C2B3D_SUMMARY_INVENTORY
        if spec.role == "architecture"
    )
    shared_summary = _assert_live_c2b3d_summary_document(text, shared_spec)
    _require(
        summary == shared_summary,
        "architecture.c2b3d_summary|failure=shared_inventory_range",
    )
    return summary


def _mutate_c2b3d_architecture_summary(text: str, mutation: str) -> str:
    start, end, summary = _extract_c2b3d_architecture_summary(text)
    closing = "Exact later-phase values and\nevidence layouts remain deferred."
    if mutation == "same-title-ancestor-reparenting":
        insertion = text.index(_C2B3D_ARCHITECTURE_BEGIN)
        return (
            text[:insertion]
            + "# NWP Coordinator Architecture\n\n"
            + "Historical superseded sibling copy.\n\n"
            + text[insertion:]
        )
    if mutation == "commit-omission":
        mutated = summary.replace(_C2B3D_IMPLEMENTATION_COMMIT, "", 1)
    elif mutation == "commit-swap":
        mutated = summary.replace(
            _C2B3D_IMPLEMENTATION_COMMIT,
            _SECTION_41_IMPLEMENTATION_COMMIT,
            1,
        )
    elif mutation == "stale-status":
        mutated = summary.replace(
            closing,
            "The current working tree contains an uncommitted candidate pending "
            "fresh independent audit.\n"
            + closing,
            1,
        )
    elif mutation == "authority-contradiction":
        mutated = summary.replace(
            closing,
            "Audit reports own Git truth; audit acceptance is Coordinator "
            "durable authority and effect permission; model output grants effect "
            "permission.\n"
            + closing,
            1,
        )
    elif mutation == "capability-contradiction":
        mutated = summary.replace(
            "performs no dispatch, worker, capsule,\ncredential,",
            "performs dispatch, worker, capsule,\ncredential,",
            1,
        )
    elif mutation == "fenced-region":
        mutated = "````text\n" + summary + "````\n"
    elif mutation == "historical-owner":
        mutated = "### Historical superseded examples\n\n" + summary
    elif mutation == "duplicate-region":
        mutated = summary + "\n" + summary
    else:
        raise AssertionError(mutation)
    _require(mutated != summary, "architecture.c2b3d_summary|failure=noop_mutant")
    return text[:start] + mutated + text[end:]


def _assert_c2b0_durable_current_target_contract(text: str) -> None:
    role = "architecture.durable_state"
    headings = _markdown_atx_headings(text, role=role)
    first_section = next((item for item in headings if item[0] == 2), None)
    _require(
        first_section is not None,
        "architecture.durable_state|heading=<current-status>|failure=missing_h2_boundary",
    )
    assert first_section is not None
    current = _compact(_unfenced_markdown(text[: first_section[2]], role=f"{role}.current"))
    target = _compact(
        _unfenced_markdown(
            _bounded_markdown_section(
                text,
                "C2B0 Accepted Durable-Development Target",
                2,
                role=role,
                allow_eof=True,
            ),
            role=f"{role}.target",
        )
    )
    for phrase in (
        "current implemented database is application generation 2 with terminal catalog entry `0003_cognitive_proposal_and_selection_state`",
        "migration 0001 and 0002 bytes, history, and table meanings remain unchanged",
        "C2B1 supplies bounded administrative migration mechanics",
        "C2B2 Slice 1 adds only the frozen physical nineteen-table core",
        "Slice 2 adds private pure no-I/O row/value contracts for those nineteen tables",
        "Slice 3 adds exactly twelve private reader roles over those values",
        "All twelve now have the private C2B3D author-effect caller",
        "mutation-receipt reader also retains the private VS1B initialization caller",
        "Sections 41 and 42 govern the exact migration-0003 physical schema and the private pre-execution proposal-selection runtime",
        "No public C2B reader, bound-effect mutation, observation ingest, post-execution progression runtime",
        "C2B3's private initialization and author-effect establishment mutations plus the Section 41 pre-execution selection mutation are the implemented C2B durable family behaviors",
        "cumulative physical tip is now migration 0003 at unchanged application generation 2",
        "private-reader layer remains exactly twelve private roles and twenty-four bounded query contracts",
        "later Section 41 runtime composes with a bounded seven-role subset",
        "C2B2 did not implement or acquire ownership of migration 0003 or Section 41",
        "reader reports and projections remain neither durable program truth nor effect authority",
    ):
        _require(
            phrase in current,
            "architecture.durable_state|heading=<current-status>|failure=current_target_distinction",
        )
    for phrase in (
        "CURRENT IMPLEMENTED CONTRACT` for the bounded private VS1B genesis, C2B3D author-effect, and Section 41 pre-execution proposal-selection families",
        "C2B2 Slice 1 has implemented the migration-0002 physical core at application generation 2",
        "Slice 2 can purely validate already-fetched tuples as private row values",
        "Slice 3 implements twelve private reader roles; all have the bounded C2B3D caller",
        "mutation-receipt role also has the private VS1B caller",
        "migration-0003 cognitive proposal-selection families",
        "implemented cumulative generation-2 schema comprises",
        "migration 0003 contributes nine tables and eighteen triggers",
        "Bound-effect and post-execution C2B mutation/replay/recovery",
    ):
        _require(
            phrase in target,
            "architecture.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=target_status",
        )
    visible = _unfenced_markdown(text, role=role).lower()
    for forbidden in (
        "a future C2B would require a separately accepted durable schema",
        "no migration number is reserved here",
        "Exact future state shape, schema, migrations",
        "Exact C2B schema remains wholly open.",
        "C2B is currently implemented.",
        "Migration 0003 remains absent.",
        "Migration 0004 is installed current schema.",
        "0002 is absent.",
        "0003 is only a target.",
        "Application generation is currently 3.",
        "No migration number is reserved.",
        "The cumulative physical tip is now migration 0002.",
        "Only their mutation-receipt role has the bounded private C2B3 genesis caller.",
        "Non-genesis C2B reader integration, mutation, replay/recovery, and progression behavior remain target-only.",
    ):
        _require(
            forbidden.lower() not in visible,
            "architecture.durable_state|heading=<current-status>|failure=stale_or_installed_claim",
        )


def _assert_candidate_capsule_durable_state_contract(text: str) -> None:
    section = _compact(
        _bounded_markdown_section(
            text,
            "C1 Candidate-Capsule Durable-State Boundary",
            2,
        )
    )
    assertions = (
        "For candidate-capsule material, future Coordinator durable state may retain only a safe capsule digest/reference and the Coordinator-owned progression decisions that bind it.",
        "Capsule bytes, mutable workspace material, local paths, and bearer retrieval credentials remain outside Coordinator SQLite.",
        "This capsule-material restriction does not exclude accepted future durable program, revision, work-item, semantic-attempt, effect, source-observation, acceptance, repair/replan, publication-eligibility, publication, or other safe Coordinator-owned progression facts.",
        "This target-only statement adds no current schema or implementation.",
    )
    for assertion in assertions:
        assert assertion in section
    assert section == " ".join(assertions)

    assert "Future Coordinator state may hold only" not in _compact(text)
    for opposite in (
        "Coordinator SQLite may retain candidate-capsule bytes.",
        "Candidate-capsule bytes may be stored in Coordinator SQLite.",
        "Mutable workspace material may be retained in Coordinator SQLite.",
        "Bearer retrieval credentials may be retained in Coordinator SQLite.",
    ):
        assert opposite not in section


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


def test_architecture_pins_runtime_floor_and_fixture_physical_semantic_split() -> None:
    architecture = _compact(_text(".docs/architecture.md"))
    durable = _compact(_text(".docs/durable-state-model.md"))
    agents = _compact(_text("AGENTS.md"))
    readme = _compact(_text("README.md"))

    for phrase in (
        "administrative runtime-capability preflight is derived from the maximum immutable catalog target",
        "require SQLite `3.37.0` before state-root creation, common-lock acquisition, writable open, `BEGIN`, or mutation",
        "temporary current-generation-2 database at terminal migration `0003_cognitive_proposal_and_selection_state`",
        "historical schema-0001 B3/B4 graph",
        "All nineteen C2B core tables and all nine cognitive proposal-selection tables remain empty",
        "`.docs/b3-tests-only-coherent-fixtures.md`",
    ):
        assert phrase in architecture

    assert "current-generation-2 database at terminal migration `0003_cognitive_proposal_and_selection_state`" in durable
    assert "maximum immutable catalog capability" in agents
    assert "current-generation-2 database at terminal migration 0003" in readme
    for stale in (
        "temporary managed schema-0001 database",
        "not an executable transition proof, and not migration 0002",
    ):
        assert stale not in " ".join((architecture, durable, agents, readme))


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
        "Bridge remains the current guarded adapter/evidence surface",
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

    assert "Status: target runtime contract/design record with a current C2A1 pure-value prerequisite." in worker
    assert "This document enables no runtime implementation, no transport or process-framing implementation, no process launch, and no dispatch." in worker
    assert "C2A freezes the pure semantic schemas without creating a runtime wire protocol" in worker
    assert "C2A1 implements only the internal immutable values and six named pure coherence validators." in worker
    assert "This document selects target worker source/process placement and a staged direct-local-to-ES route without implementing either." in worker
    assert "Coordinator currently owns bounded internal durable SQLite mutation authority for coding-work state." in worker
    assert "The public `StateStore` remains unwidened." in worker
    assert "Coordinator currently has no worker, scheduler, queue consumer, dispatcher, reconciler, public service/API, Codex invocation, Execution Substrate handoff" in worker
    assert "Strategic target direction is separate from current implementation facts." in architecture
    assert "Coordinator may later become the component-level durable progression owner for governed programs admitted to its target operating model" in architecture
    assert "separately versioned software-development and bounded operational-change domain contracts" in architecture
    assert "The current coding domain remains intact and coding-work-specific." in architecture
    assert "This target direction is not implemented by the current code and does not authorize execution." in architecture
    assert "C2A freezes the first-slice semantic schemas" in architecture
    assert "C2A1 now implements the nine internal immutable values and six named pure coherence validators" in architecture
    assert "This pure layer adds no durable schema, process, adapter, worker, executable authorization, ingest, capsule custody, Git effect, direct-local behavior, or ES routing." in architecture
    assert "This repository currently implements no direct-local adapter, worker supervisor, worker process, dispatcher, reconciler, service/API/IPC, ES call" in agents
    assert "The current finite-backlog, standing-lease, zero-only budget, READY-only dependency, and disabled-stage contracts remain current v1 compatibility behavior but are not frozen as the target model." in durable
    assert "C2A freezes the semantic field, identity, digest, and relation contracts and creates no durable state." in durable
    assert "C2A1 implements only internal immutable no-I/O values and the six named pure coherence validators" in durable
    _assert_c2b0_durable_current_target_contract(
        _text(".docs/durable-state-model.md")
    )


def test_c2b0_current_and_target_status_are_consistent() -> None:
    text = _text(".docs/durable-state-model.md")
    _assert_c2b0_durable_current_target_contract(text)

    fenced_stale = (
        text
        + "\n```text\nA future C2B would require a separately accepted durable schema.\n"
        + "No migration number is reserved here.\n```\n"
    )
    _assert_c2b0_durable_current_target_contract(fenced_stale)


def test_c2b0_stale_current_target_forms_are_rejected_in_memory() -> None:
    text = _text(".docs/durable-state-model.md")
    mutations = (
        text + "\nA future C2B would require a separately accepted durable schema.\n",
        text + "\nNo migration number is reserved here.\n",
        text + "\nExact future state shape, schema, migrations remain wholly open.\n",
        text + "\nC2B is currently implemented.\n",
        text + "\nMigration 0003 remains absent.\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_c2b0_durable_current_target_contract(mutation)
        assert str(rejected.value) == (
            "architecture.durable_state|heading=<current-status>|failure=stale_or_installed_claim"
        )

    target_claim = "The implemented cumulative generation-2 schema comprises"
    fenced_target_only = text.replace(
        target_claim,
        f"```text\n{target_claim}\n```",
        1,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_durable_current_target_contract(fenced_target_only)
    assert str(rejected.value) == (
        "architecture.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=target_status"
    )


def test_c2b0_current_target_status_rejects_all_additive_stale_claims() -> None:
    text = _text(".docs/durable-state-model.md")
    stale_claims = (
        "Exact C2B schema remains wholly open.",
        "0002 is absent.",
        "Migration 0003 remains absent.",
        "Migration 0004 is installed current schema.",
        "Application generation is currently 3.",
        "No migration number is reserved.",
        "C2B is currently implemented.",
    )
    for stale in stale_claims:
        with pytest.raises(AssertionError) as rejected:
            _assert_c2b0_durable_current_target_contract(text + f"\n{stale}\n")
        assert str(rejected.value) == (
            "architecture.durable_state|heading=<current-status>|failure=stale_or_installed_claim"
        )

    fenced = text + "\n~~~example`info\n" + "\n".join(stale_claims) + "\n~~~\n"
    _assert_c2b0_durable_current_target_contract(fenced)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_authority_bypass() -> None:
    text = _text(".docs/durable-state-model.md")
    mutation = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_durable_current_target_contract(mutation)
    assert str(rejected.value) == (
        "architecture.durable_state|heading=<current-status>|failure=stale_or_installed_claim"
    )

    valid_tilde = text + "\n~~~bad`info\nC2B is currently implemented.\n~~~\n"
    _assert_c2b0_durable_current_target_contract(valid_tilde)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_duplicate_heading_bypass() -> None:
    text = _text(".docs/durable-state-model.md")
    mutation = (
        text
        + "\n```bad`info\n## C2B0 Accepted Durable-Development Target\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_durable_current_target_contract(mutation)
    assert str(rejected.value) == (
        "architecture.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=duplicate"
    )


def test_architecture_markdown_closer_suffix_is_ascii_space_tab_only() -> None:
    for valid_suffix in ("", " ", "\t", " \t"):
        sample = f"~~~text\n## Hidden\n~~~{valid_suffix}\n## Visible\n"
        headings = _markdown_atx_headings(sample, role="architecture.repair3")
        assert tuple(item[1] for item in headings) == ("Visible",)

    for invalid_suffix in ("\u00a0", "\u2003", "not-a-closer"):
        closed_later = (
            "~~~text\n"
            f"~~~{invalid_suffix}\n"
            "C2B is currently implemented.\n"
            "## C2B0 Accepted Durable-Development Target\n"
            "~~~\n"
        )
        assert _markdown_atx_headings(
            closed_later,
            role="architecture.repair3",
        ) == ()
        assert _unfenced_markdown(
            closed_later,
            role="architecture.repair3",
        ) == ""

        with pytest.raises(AssertionError) as rejected:
            _markdown_atx_headings(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="architecture.repair3",
            )
        assert str(rejected.value) == (
            "architecture.repair3|heading=<none>|failure=unbalanced_fence"
        )


def test_architecture_markdown_missing_heading_has_bounded_diagnostic() -> None:
    text = _text(".docs/durable-state-model.md")
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_durable_current_target_contract(
            "````text\n" + text + "````\n"
        )
    assert str(rejected.value) == (
        "architecture.durable_state|heading=<current-status>|failure=missing_h2_boundary"
    )


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

    assert "The bounded direct-local supervisor/adapter and later ES adapter may own only bounded process and transport protocol mechanics" in authority
    assert "They must not own durable work selection, scheduling policy, semantic retry or repair authority, acceptance, ES admission, runtime lifecycle truth, Git truth, validation truth, or hidden program state." in authority


def test_worker_boundary_pins_staged_placement_and_bridge_non_ownership() -> None:
    readme = _compact(_text("README.md"))
    worker = _compact(_text(".docs/worker-execution-boundary.md"))
    placement = worker.split("## Accepted Staged Placement And Credential Boundary", 1)[1].split(
        "## Private Material And Safe Projections", 1
    )[0]

    assert "worker source and release machinery held in the Coordinator repository" in placement
    assert "launches a separate OS worker process" in placement
    assert "The authoritative Coordinator process never executes implementation work in-process." in placement
    assert "Bridge and Bridge Core are not worker implementation owners, adapters, or triggers for the first slice." in placement
    assert "A separate stateless gateway is not selected." in placement
    assert "must not receive a `WriterSession`, writer proof, Coordinator database path, or unrestricted Coordinator credentials" in placement
    assert "Bridge is not the worker owner." in readme


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
    worker_text = _text(".docs/worker-execution-boundary.md")
    start_heading = "## Explicit Non-Claims"
    end_heading = "## Required-Before-Execution Gates"
    assert worker_text.count(start_heading) == 1
    assert worker_text.count(end_heading) == 1
    start = worker_text.index(start_heading) + len(start_heading)
    end = worker_text.index(end_heading)
    assert start < end
    negative = _compact(worker_text[start:end])
    worker = _compact(worker_text)

    assert "Public reports must not contain raw prompts, raw Codex JSONL, raw logs, credentials, trust material, local absolute paths, private endpoints, retained bundles, or arbitrary runtime payloads." in worker
    assert "The first-slice candidate capsule is private, immutable, content-addressed, worker-side, outside the mutable worktree, and outside Coordinator SQLite." in worker
    assert "Coordinator retains only a safe digest/reference and progression decisions." in worker
    assert "Later ES transport or retention is opaque." in worker

    for phrase in (
        "no implemented worker, supervisor, process launch, or Codex invocation",
        "no scheduler",
        "no dispatcher or reconciler",
        "no service/API/IPC",
        "no schema or migration",
        "no outbox/inbox implementation",
        "no ES call",
        "no Bridge widening",
        "no Bridge or Bridge Core worker ownership",
        "no gateway service",
        "no connector dependency",
        "no Development Program prerequisite",
        "no full event-sourcing decision",
        "no implemented direct-local worker route",
        "no runtime-profile selection",
        "no model/provider client",
        "no capsule builder or store implementation",
        "no subordinate-authorization runtime",
        "no Git effect or publication behavior",
        "no validation, review, or repair executor",
        "no autonomous loop",
    ):
        assert phrase in negative


def test_current_status_drift_corrections_are_documented() -> None:
    durable_text = _text(".docs/durable-state-model.md")
    durable = _compact(durable_text)
    operations = _compact(_text(".docs/sqlite-operations-and-recovery.md"))

    _assert_candidate_capsule_durable_state_contract(durable_text)
    assert "B3c4b adds private atomic transition persistence, B3c4c adds guarded public transition delegation, B4b adds private global-stop persistence, and B4c adds guarded public global-stop delegation." in durable
    assert "The public `StateStore` remains unwidened; internal `WriterSession` mutation is not a general public `StateStore` backend or service." in durable
    assert "The author-effect family durably represents one semantic attempt, fences, author command, pending authority evaluation, effect/delivery heads, planned delivery, and receipt; none is dispatch or executable permission." in durable
    assert "introduced and committed at `5e544622e5f46ddc78294322471b4fcbd2ad9172`" in durable
    assert "Git owns the committed object and ref fact" in durable
    assert "external evidence rather than Coordinator durable authority or effect permission" in durable
    assert "The code still has no runtime observation, result ingest, outbox/inbox, worker, scheduler, queue, Codex, ES handoff, or runtime lifecycle storage." in durable
    assert "Public global-stop mutation now delegates through the guarded B4c public wrapper to B4b private atomic global-stop persistence." in operations
    assert "The public wrappers own no SQL, receipt verification, evaluator, sequence allocation, write, rollback, COMMIT, or uncertainty handling" in operations

    architecture = _text(".docs/architecture.md")
    _assert_c2b3d_architecture_summary_document(architecture)
    for mutation in (
        "commit-omission",
        "commit-swap",
        "stale-status",
        "authority-contradiction",
        "capability-contradiction",
        "fenced-region",
        "historical-owner",
        "duplicate-region",
    ):
        mutant = _mutate_c2b3d_architecture_summary(architecture, mutation)
        with pytest.raises(
            AssertionError,
            match=r"architecture\.c2b3d_summary\|",
        ):
            _assert_c2b3d_architecture_summary_document(mutant)

    from test_c2b3c_author_effect_contract import (
        LIVE_C2B3D_SUMMARY_INVENTORY,
        _assert_live_c2b3d_summary_document,
        _broken_title_chain_summary_checker,
    )

    shared_spec = next(
        spec
        for spec in LIVE_C2B3D_SUMMARY_INVENTORY
        if spec.role == "architecture"
    )
    same_title_ancestor = _mutate_c2b3d_architecture_summary(
        architecture,
        "same-title-ancestor-reparenting",
    )
    _broken_title_chain_summary_checker(same_title_ancestor, shared_spec)
    with pytest.raises(
        AssertionError,
        match=r"C2B3C_STATUS_INVALID:architecture:",
    ):
        _assert_c2b3d_architecture_summary_document(same_title_ancestor)
    with pytest.raises(
        AssertionError,
        match=r"C2B3C_STATUS_INVALID:architecture:",
    ):
        _assert_live_c2b3d_summary_document(same_title_ancestor, shared_spec)


def test_candidate_capsule_durable_state_section_rejects_structural_drift() -> None:
    text = _text(".docs/durable-state-model.md")
    heading = "## C1 Candidate-Capsule Durable-State Boundary"
    boundary = "## P1.1 Atomic Apply Contract"
    required_source = (
        "Capsule bytes, mutable workspace material, local paths, and bearer\n"
        "retrieval credentials remain outside Coordinator SQLite."
    )
    required_statement = required_source.replace("\n", " ")

    fenced_duplicate = f"```text\n{heading}\n```\n\n{text}"
    _assert_candidate_capsule_durable_state_contract(fenced_duplicate)

    mutations = (
        text.replace(heading, f"{heading}\n\n{heading}", 1),
        text.replace(required_source, "", 1) + f"\n\n{required_statement}\n",
        text.replace(
            heading,
            f"{heading}\n\nCoordinator SQLite may retain candidate-capsule bytes.",
            1,
        ),
        text + "\nFuture Coordinator state may hold only a safe reference.\n",
        text.split(f"\n{boundary}", 1)[0] + "\n",
        text.replace(boundary, "### P1.1 Atomic Apply Contract", 1),
        text.replace(boundary, "P1.1 Atomic Apply Contract", 1),
        f"```text\n{text}",
        f"~~~text\n{text}\n```\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _assert_candidate_capsule_durable_state_contract(mutation)


def test_c2b0_target_topology_reuses_current_private_authority_without_implementation() -> None:
    architecture_text = _text(".docs/architecture.md")
    administration = _compact(
        _unfenced_markdown(
            _bounded_markdown_section(
                architecture_text,
                "C2B1/C2B2 SQLite Administration And Pure Row Values",
                2,
                role="architecture.current_reader_composition",
            ),
            role="architecture.current_reader_composition.section",
        )
    )
    for phrase in (
        "exactly twelve private roles and twenty-four bounded query contracts",
        "All twelve roles have the bounded private C2B3D author-effect caller",
        "mutation-receipt role also retains the private VS1B program-initialization caller",
        "later Section 41 selection runtime composes with a bounded seven-role subset",
        "Those later callers do not widen the reader query contract",
        "C2B2 did not implement or acquire ownership of migration 0003 or Section 41",
        "reader reports and projections remain neither durable program truth nor effect authority",
    ):
        assert phrase in administration
    assert "only the mutation-receipt reader has the bounded private C2B3 caller" not in administration
    architecture = _compact(
        _unfenced_markdown(
            _bounded_markdown_section(
                architecture_text,
                "C2B0 Accepted Durable-State Target Topology",
                2,
                role="architecture.summary",
                allow_eof=True,
            ),
            role="architecture.summary.section",
        )
    )
    owner_text = _text(".docs/c2b-durable-development-state.md")
    owner = _compact(
        _bounded_markdown_section(
            owner_text,
            "12. Complete Target Mutation Families",
            2,
            role="architecture.c2b0_owner",
        )
        + _bounded_markdown_section(
            owner_text,
            "27. Explicit Nonimplementation",
            2,
            role="architecture.c2b0_owner",
            allow_eof=True,
        )
    )

    for phrase in (
        "broader C2B0 topology remains an accepted target",
        "All twelve roles have the bounded private C2B3D production caller",
        "mutation-receipt role also retains the VS1B production caller",
        "existing Coordinator SQLite database",
        "existing concrete writer issuance/fencing authority",
        "operation guard",
        "shared mutation slot",
        "single transaction controller",
        "no second database, writer, controller, session authority, generic mutation dispatcher",
        "public `StateStore` widening",
        "public `WriterSession` widening",
        "Slice 2 provides private pure row/value source for its nineteen tables",
        "Slice 3 provides exactly twelve private reader roles with no public surface; all twelve have the bounded C2B3D caller",
        "route-neutral nine-row/eight-entry program-genesis family",
        "ten-row/nine-entry author-effect family",
        "same-command replay and readback-only commit-outcome resolution",
    ):
        assert phrase in architecture

    for phrase in (
        "_establish_development_author_effect_intent",
        "_establish_development_bound_effect_intent",
        "C2B0 implements none of them.",
        "C2B0 creates no source module, SQL, schema object, migration, database row",
    ):
        assert phrase in owner


def test_narrowed_vertical_slice_architecture_is_governing_not_schema_freeze() -> None:
    architecture = _text(".docs/architecture.md")
    architecture_compact = _compact(architecture)
    owner = _text(".docs/c2b-durable-development-state.md")
    frozen_owner = owner.partition("\n## 42.")[0]
    assert architecture.count("<!-- C2B3_NARROWED_ARCHITECTURE_BEGIN -->") == 1
    assert architecture.count("<!-- C2B3_NARROWED_ARCHITECTURE_END -->") == 1
    narrowed = architecture.split(
        "<!-- C2B3_NARROWED_ARCHITECTURE_BEGIN -->",
        1,
    )[1].split("<!-- C2B3_NARROWED_ARCHITECTURE_END -->", 1)[0]

    def assert_committed_private_narrowing(candidate: str) -> None:
        _assert_c2b3d_architecture_summary_text(candidate)

    assert_committed_private_narrowing(narrowed)
    narrowing_mutants = (
        narrowed.replace("5e544622e5f46ddc78294322471b4fcbd2ad9172", "", 1),
        narrowed.replace(
            "5e544622e5f46ddc78294322471b4fcbd2ad9172",
            "394d625aa63935140eeaf88ecff6f59f0547cb7e",
            1,
        ),
        narrowed.replace(
            "Git owns the committed object and ref fact",
            "Audit reports own the committed object and ref fact",
            1,
        ),
        narrowed.replace(
            "performs no dispatch, worker, capsule,\ncredential,",
            "performs dispatch, worker, capsule,\ncredential,",
            1,
        ),
        narrowed + "\nThe current working tree contains an uncommitted candidate.\n",
        narrowed
        + "\nAudit reports own Git truth; audit acceptance is Coordinator durable "
        "authority.\n",
    )
    for mutant in narrowing_mutants:
        assert mutant != narrowed
        with pytest.raises(AssertionError):
            assert_committed_private_narrowing(mutant)
    for expected in (
        "Initialization is route-neutral.",
        "Route selection occurs only at author-effect delivery",
        "`direct_local_bootstrap` bounded direct/non-ES compatibility path",
        "one qualified remote Linux host",
        "It does not mean the user's Mac, the Coordinator host, or physical colocation",
        "introduces no third adapter kind",
        "The worker receives no Coordinator SQLite or writer access.",
        "At most one productive bootstrap acceptance",
        "one later isolated local feature-branch commit",
        "push, remote-ref mutation, PR, merge, deployment, and publication remain zero",
        "exactly nine state rows and eight supplied graph entries",
        "private readback-only uncertainty resolution",
        "Exact later-phase values and evidence layouts remain deferred.",
    ):
        assert expected in architecture_compact
    for expected in (
        '"initialization_route_neutral": True',
        '"first_route": "direct_local_bootstrap"',
        '"third_adapter_kind_introduced": False',
        '"raw_WorkSpec_in_Coordinator_SQLite": False',
        '"retrieval_bearer_authority_in_Coordinator_SQLite": False',
        '"mandatory_program_or_tranche_count_frozen": False',
        '"qualified_remote_host_readiness_evidence_gate": (',
        '"accepted_clean_exact_es_oid_and_owning_repository_contract_adoption_evidence_gate": (',
    ):
        assert expected in frozen_owner
    for forbidden in (
        "WorkSpecCustodyReceiptV1",
        "VerifiedAuthorityResultV1",
        "LocalGitObservationV1",
        "canonical_positive_vectors",
        "CREATE TABLE",
        '"prerequisite_00061":',
        '"prerequisite_00054":',
    ):
        assert forbidden not in frozen_owner
