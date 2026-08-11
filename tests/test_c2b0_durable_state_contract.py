from dataclasses import dataclass
from pathlib import Path
import re
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"

SECTION_HEADINGS = (
    "1. Status, Classification, And Layering",
    "2. One Database, One Writer, And Fact Ownership",
    "3. Identity Non-Collapse",
    "4. Hybrid Durable Representation",
    "5. Program Genesis",
    "6. Exact Decision-Kind Inventory",
    "7. Distinct Cancel Decision",
    "8. Decision-To-Effect Basis",
    "9. Originating Author-Command Cardinality",
    "10. Author-Effect Establishment",
    "11. Bound-Effect Establishment",
    "12. Complete Target Mutation Families",
    "13. Source Invocation, Observation, And Ingest",
    "14. Unknown Outcome And Redelivery",
    "15. Coding Global-Stop Matrix",
    "16. Private WorkSpec Custody",
    "17. C2A Value Persistence Matrix",
    "18. Authority Evaluation",
    "19. First-Slice One-Shot Latch",
    "20. Migration-Framework Strategy",
    "21. Migration 0002",
    "22. Migration 0003",
    "23. Exact Schema Totals",
    "24. Exact Explicit Indexes",
    "25. Transaction And Replay Algebra",
    "26. Exact Target Tranche Sequence",
    "27. Explicit Nonimplementation",
)

DECISION_KINDS = (
    "initialize",
    "accept",
    "repair",
    "replan",
    "terminal_reject",
    "block",
    "redeliver",
    "cancel",
)

DECISION_VERSION_EFFECTS = (
    "initialize: creates version 1",
    "accept: appends an accepted program version",
    "repair: appends a program version and preassigns a successor attempt/candidate",
    "replan: appends accepted-intent/work revision and program-version state",
    "terminal_reject: appends a terminal-rejected version",
    "block: appends a blocked version",
    "redeliver: no program-version advance",
    "cancel: no program-version advance",
)

MUTABLE_HEADS = (
    "development_program_heads",
    "development_work_item_heads",
    "development_effect_heads",
    "development_delivery_heads",
    "development_observation_ref_heads",
    "development_first_slice_latch",
)

TABLES_0002 = (
    "development_program_heads",
    "development_program_versions",
    "development_accepted_intent_revisions",
    "development_work_item_heads",
    "development_work_item_revisions",
    "development_program_version_work_items",
    "development_revision_edges",
    "development_work_spec_bindings",
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_authority_evaluations",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
    "development_decisions",
    "development_mutation_receipts",
)

TABLES_0003 = (
    "development_source_invocations",
    "development_candidate_capsule_bindings",
    "development_source_observation_claims",
    "development_observation_ref_heads",
    "development_observation_ingests",
    "development_observation_quarantines",
    "development_decision_evidence_bindings",
    "development_publication_eligibility",
    "development_first_slice_latch",
)

EXPLICIT_INDEXES = (
    "uq_development_effect_intents_author_command",
    "idx_development_source_observation_claims_digest",
)

CANCELLATION_EVIDENCE_ROLES = (
    "cancel_target_effect",
    "cancel_target_effect_fence",
    "cancel_target_capsule",
    "cancel_source_directive",
    "cancel_source_evidence",
)

DISPOSITIONS = (
    "duplicate_exact",
    "conflict_quarantined",
    "ambiguous_quarantined",
    "stale_retained",
    "late_retained",
    "recorded",
)

OBSERVATION_INGEST_STEPS = (
    "1. C2A1 record-local validation",
    "2. actual durable graph validation",
    "3. preserve source-authored claim",
    "4. compare prior observation identity/digest",
    "5. classify source-owner relation",
    "6. append Coordinator ingest disposition",
    "7. evaluate semantic progression separately",
)

MUTATION_FAMILIES = (
    "_initialize_development_program",
    "_establish_development_author_effect_intent",
    "_establish_development_bound_effect_intent",
    "_ingest_development_source_observation",
    "_record_development_progression_decision",
)

RECOVERY_FAMILIES = (
    "_resolve_development_program_initialization_commit_outcome",
    "_resolve_development_author_effect_establishment_commit_outcome",
    "_resolve_development_bound_effect_establishment_commit_outcome",
    "_resolve_development_source_observation_ingest_commit_outcome",
    "_resolve_development_progression_decision_commit_outcome",
)

TRANCHES = ("C2B0", "C2B1", "C2B2", "C2B3", "C2B4", "C2B5", "C2B6")

TRIGGER_ARITHMETIC = (
    "0002: 15 immutable tables * no-update/no-delete = 30",
    "0003: 7 immutable tables * no-update/no-delete = 14",
    "0003: latch no-delete = 1",
    "0003: latch one-way update guard = 1",
)

MIGRATION_PATHS = (
    "C2B2 fresh installation: 0001 -> 0002",
    "C2B4-or-later fresh installation: 0001 -> 0002 -> 0003",
    "C2B2 upgrade from exact 0001: apply only 0002",
    "C2B4-or-later upgrade from exact 0001: apply 0002 then 0003",
    "C2B4-or-later upgrade from exact 0002: apply only 0003",
)

ORDINARY_OPEN_RULES = (
    "exact complete catalog history",
    "exact current terminal sequence and migration ID",
    "terminal migration compatibility containing the current application generation",
    "complete final-schema verification",
)

MIGRATION_TRANSACTION_PATHS = (
    "C2B2 fresh installation transaction: [0001, 0002]",
    "C2B4-or-later fresh installation transaction: [0001, 0002, 0003]",
    "C2B2 upgrade from exact 0001 transaction: [0002]",
    "C2B4-or-later upgrade from exact 0001 transaction: [0002, 0003]",
    "C2B4-or-later upgrade from exact 0002 transaction: [0003]",
)

MIGRATION_TRANSACTION_COMPONENTS = (
    "DDL",
    "managed invariant changes",
    "matching migration-history insertion",
)

MIGRATION_RECOVERY_STEPS = (
    "close the uncertain connection",
    "reopen through the migration recovery path",
    "reread the complete exact migration history",
    "reread the complete live-schema invariants",
    "compare both the exact prior supported prefix and exact intended completed suffix tip",
)

MIGRATION_COMMITTED_EXACT = (
    "committed_exact",
    "history equals the prior prefix plus the complete intended suffix",
    "every suffix row matches packaged sequence, ID, checksum, compatibility bounds, and destructive flag",
    "live schema equals the complete intended terminal-tip schema",
    "the prior prefix remains unchanged",
    "no partial, extra, unknown, or divergent object exists",
)

MIGRATION_DEFINITELY_NOT_COMMITTED = (
    "definitely_not_committed",
    "history equals the exact prior supported prefix",
    "live schema equals the exact prior supported-prefix schema",
    "no intended suffix history row exists",
    "no intended suffix schema object or invariant exists",
    "no partial or unexpected object exists",
)

MIGRATION_UNRESOLVED = (
    "unresolved",
    "history and schema disagree",
    "only part of the intended suffix is present",
    "history-only suffix evidence exists",
    "schema-only suffix evidence exists",
    "an unknown or divergent history row exists",
    "an unexpected schema object exists",
    "either exact verification cannot be completed",
)

SQLITE_MIGRATION_DEFINITIONS = (
    "0002_development_program_and_effect_state: [2,2], non-destructive, 19 tables, 30 triggers, 1 explicit index, no seed rows",
    "0003_development_observation_and_progression_state: [2,2], non-destructive, 9 tables, 16 triggers, 1 explicit index, one available latch seed",
)

SQLITE_MIGRATION_SCHEMA_TOTALS = (
    "0001: 11 user tables, 0 explicit indexes, 16 triggers",
    "0002: 30 user tables, 1 explicit index, 46 triggers",
    "0003: 39 user tables, 2 explicit indexes, 62 triggers",
)

MIGRATION_FORBIDDEN_CLAIMS = (
    "c2b2 remains generation 1.",
    "c2b2 becomes generation 3.",
    "c2b3 prematurely installs 0003.",
    "c2b4 becomes generation 3.",
    "c2b4 drops to generation 1.",
    "c2b4 omits 0003.",
    "fresh installation applies only the terminal migration.",
    "fresh installation skips 0001.",
    "fresh installation skips 0002.",
    "ordinary open accepts 0001 before explicit migration.",
    "ordinary tip-0003 open accepts 0002.",
    "explicit migration accepts a gap.",
    "explicit migration accepts an unknown row.",
    "explicit migration accepts a checksum mismatch.",
    "explicit migration accepts divergent bounds.",
    "explicit migration accepts partial history or schema.",
    "c2b4 upgrade from exact 0001 commits 0002 before starting 0003.",
    "matching migration history alone is committed_exact even when the live schema differs.",
    "matching live schema alone is committed_exact even when migration history differs.",
    "after an unresolved migration commit, the suffix is automatically rerun.",
    "history and live-schema disagreement is committed_exact.",
    "a partial intended suffix is committed_exact.",
    "an unknown or divergent migration-history row is committed_exact.",
    "an unexpected live-schema object is committed_exact.",
    "incomplete exact history or live-schema verification is committed_exact.",
    "after an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
)

LATCH_CONTRACT = (
    "latch_ref: direct_local_first_productive_acceptance",
    "scope: global Coordinator bootstrap",
    "initial state: available",
    "initial version: 0",
    "final state: consumed",
    "final version: 1",
    "reset: forbidden",
    "delete: forbidden",
    "reuse: forbidden",
)

LATCH_SEED_CONTRACT = (
    "latch_ref: direct_local_first_productive_acceptance",
    "state: available",
    "version: 0",
    "consumed bindings: null",
)

LATCH_DECLARATION_INVENTORY = (
    "latch_ref: direct_local_first_productive_acceptance",
    "reuse: forbidden",
    "latch_ref: direct_local_first_productive_acceptance",
)

SCHEMA_TOTALS = (
    "schema 0001: 11 user tables, 0 explicit application indexes, 16 triggers",
    "schema tip 0002: 30 user tables, 1 explicit application index, 46 triggers",
    "schema tip 0003: 39 user tables, 2 explicit application indexes, 62 triggers",
)

MIGRATION_ADDITION_TOTALS = (
    "0002: 19 tables, 30 triggers, 1 explicit index",
    "0003: 9 tables, 16 triggers, 1 explicit index",
)

TRIGGER_SCHEMA_ROLE_CLAIMS = (
    "schema 0001: 11 user tables, 0 explicit application indexes, 16 triggers",
    "schema tip 0002: 30 user tables, 1 explicit application index, 46 triggers",
    "schema tip 0003: 39 user tables, 2 explicit application indexes, 62 triggers",
)

TRIGGER_MIGRATION_ADDITION_ROLE_CLAIMS = (
    "0002: 19 tables, 30 triggers, 1 explicit index",
    "0003: 9 tables, 16 triggers, 1 explicit index",
)

TRIGGER_AGGREGATE_ROLE_CLAIMS = (
    "C2B adds exactly twenty-eight tables, forty-six triggers, and two explicit indexes.",
)

TRANCHE_LINES = (
    "C2B0: documentation and direct documentation-contract tests only",
    "C2B1: application generation 1; terminal tip 0001; migration-framework reset only; no SQL or database change",
    "C2B2: application generation advances to 2; terminal tip 0002; migration 0002; core records, base decision envelope, initialize-decision representation, private readers; no mutation API",
    "C2B3: application generation 2; terminal tip 0002; program initialization, author-effect establishment, private delegation and recovery; no external I/O",
    "C2B4: application generation 2; terminal tip 0003; migration 0003; observation/evidence/non-initialize-decision/eligibility/latch contracts and readers; initialize representation remains C2B2-owned; no new mutation API",
    "C2B5: application generation 2; terminal tip 0003; source-observation ingest, cancel and redeliver decisions, bound validation/review/cancellation effects, knowledge and recovery; no external I/O",
    "C2B6: application generation 2; terminal tip 0003; accept, repair, replan, terminal_reject, block, publication eligibility, latch, version/head recovery; no external I/O",
)


def _text(path: Path | str) -> str:
    selected = path if isinstance(path, Path) else ROOT / path
    return selected.read_text(encoding="utf-8")


def _owner() -> str:
    return _text(OWNER_PATH)


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


def _markdown_fence_closes(
    candidate: tuple[str, int, str] | None,
    *,
    marker: str,
    opener_length: int,
) -> bool:
    return (
        candidate is not None
        and candidate[0] == marker
        and candidate[1] >= opener_length
        and _markdown_closer_suffix_is_ascii_space_tab(candidate[2])
    )


@dataclass(frozen=True)
class _TopLevelFencedBlock:
    marker: str
    opener_length: int
    info: str
    opening_line: str
    closing_line: str
    opening_line_number: int
    closing_line_number: int
    start_offset: int
    end_offset: int
    content_start_offset: int
    content_end_offset: int
    content: str


def _markdown_scan(
    text: str,
    *,
    role: str,
) -> tuple[tuple[tuple[int, str, int, int], ...], str]:
    """Return real ATX headings and unfenced Markdown with bounded diagnostics."""
    headings: list[tuple[int, str, int, int]] = []
    unfenced: list[str] = []
    fence: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.lstrip(" ")
        indent = len(content) - len(stripped)
        fence_candidate = _markdown_fence_candidate(content)

        if fence is not None:
            if _markdown_fence_closes(
                fence_candidate,
                marker=fence[0],
                opener_length=fence[1],
            ):
                fence = None
            offset += len(line)
            continue

        if fence_candidate is not None:
            fence = (fence_candidate[0], fence_candidate[1])
            offset += len(line)
            continue

        unfenced.append(line)
        if indent <= 3:
            match = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
            if match is not None:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
                _require(bool(title), f"{role}|heading=<atx>|failure=empty")
                headings.append((len(match.group(1)), title, offset, offset + len(line)))
        offset += len(line)

    _require(fence is None, f"{role}|heading=<none>|failure=unbalanced_fence")
    return tuple(headings), "".join(unfenced)


def _top_level_fenced_blocks(
    text: str,
    *,
    role: str,
) -> tuple[_TopLevelFencedBlock, ...]:
    """Read the finite top-level fenced-block surface used by C2B0 inventories."""
    blocks: list[_TopLevelFencedBlock] = []
    fence: tuple[str, int, str, str, int, int, int] | None = None
    offset = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        content = line.rstrip("\r\n")
        candidate = _markdown_fence_candidate(content)
        if fence is None:
            if candidate is not None:
                marker, opener_length, info = candidate
                fence = (
                    marker,
                    opener_length,
                    info,
                    line,
                    line_number,
                    offset,
                    offset + len(line),
                )
            offset += len(line)
            continue

        marker, opener_length, info, opening_line, opening_line_number, start, content_start = fence
        if _markdown_fence_closes(
            candidate,
            marker=marker,
            opener_length=opener_length,
        ):
            blocks.append(
                _TopLevelFencedBlock(
                    marker=marker,
                    opener_length=opener_length,
                    info=info,
                    opening_line=opening_line,
                    closing_line=line,
                    opening_line_number=opening_line_number,
                    closing_line_number=line_number,
                    start_offset=start,
                    end_offset=offset + len(line),
                    content_start_offset=content_start,
                    content_end_offset=offset,
                    content=text[content_start:offset],
                )
            )
            fence = None
        offset += len(line)

    _require(
        fence is None,
        f"{role}|block=<none>|failure=unbalanced_fence",
    )
    return tuple(blocks)


def _unfenced_markdown(text: str, *, role: str) -> str:
    return _markdown_scan(text, role=role)[1]


def _section(text: str, heading: str) -> str:
    role = "c2b0.owner"
    headings, _unfenced = _markdown_scan(text, role=role)
    matches = tuple(item for item in headings if item[1] == heading)
    _require(bool(matches), f"{role}|heading={heading}|failure=missing")
    _require(len(matches) == 1, f"{role}|heading={heading}|failure=duplicate")
    selected = matches[0]
    _require(selected[0] == 2, f"{role}|heading={heading}|failure=wrong_level")
    selected_index = headings.index(selected)
    boundaries = tuple(
        following
        for following in headings[selected_index + 1 :]
        if following[0] <= selected[0]
    )
    if boundaries:
        end = boundaries[0][2]
    else:
        _require(
            heading == SECTION_HEADINGS[-1],
            f"{role}|heading={heading}|failure=missing_same_or_higher_boundary",
        )
        end = len(text)
    return text[selected[3] : end]


def _section_prose(text: str, heading: str) -> str:
    return _compact(
        _unfenced_markdown(
            _section(text, heading),
            role=f"c2b0.owner.section.{heading}",
        )
    )


def _summary_section(text: str, heading: str, *, role: str) -> str:
    headings, _unfenced = _markdown_scan(text, role=role)
    matches = tuple(item for item in headings if item[1] == heading)
    _require(bool(matches), f"{role}|heading={heading}|failure=missing")
    _require(len(matches) == 1, f"{role}|heading={heading}|failure=duplicate")
    selected = matches[0]
    _require(selected[0] == 2, f"{role}|heading={heading}|failure=wrong_level")
    selected_index = headings.index(selected)
    boundary = next(
        (
            following
            for following in headings[selected_index + 1 :]
            if following[0] <= selected[0]
        ),
        None,
    )
    end = len(text) if boundary is None else boundary[2]
    return text[selected[3] : end]


def _assert_summary_target(
    text: str,
    *,
    role: str,
    heading: str,
    required: str,
) -> None:
    section = _compact(
        _unfenced_markdown(
            _summary_section(text, heading, role=role),
            role=f"{role}.section",
        )
    )
    _require(
        required in section,
        f"{role}|heading={heading}|failure=target_claim_missing",
    )
    visible = _unfenced_markdown(text, role=role).lower()
    for forbidden in (
        "no migration number is reserved here",
        "No migration number is reserved.",
        "Exact C2B schema remains wholly open.",
        "C2B is currently implemented.",
        "C2B migrations 0002 and 0003 are installed.",
        "0002 is installed.",
        "0003 is installed.",
        "Application generation is currently 2.",
    ):
        _require(
            forbidden.lower() not in visible,
            f"{role}|heading={heading}|failure=contradictory_current_status",
        )


def _assert_sqlite_migration_summary(text: str) -> None:
    role = "c2b0.sqlite_migration"
    heading = "C2B0 Target Migration Sequence"
    section = _summary_section(text, heading, role=role)
    prose = _compact(_unfenced_markdown(section, role=f"{role}.section"))
    blocks = _text_blocks(section)
    for phrase in (
        "no target SQL is installed",
        "application generation and managed database tip remain 1/`0001_initial`",
        "C2B1 is a framework-only source/test reset with no SQL or database change",
        "C2B2 advances implemented application generation from 1 to 2",
        "terminal catalog tip becomes 0002",
        "C2B3 remains generation 2 with terminal tip 0002",
        "C2B4 adds migration 0003 while retaining application generation 2",
        "C2B5 and C2B6 remain generation 2 with terminal tip 0003",
        "historical migration 0001 remains `[1,1]`, while 0002 and 0003 are `[2,2]`",
        "Ordinary open never silently migrates and never accepts an older prefix",
        "one exact non-empty supported older catalog prefix",
        "gaps, unknown or partial rows, and divergent bounds or flags are rejected",
        "one exact contiguous suffix leading to the current terminal tip",
        "the complete intended packaged suffix is one administrative transaction",
        "Failure before commit restores the complete exact prior supported prefix",
        "If an administrative commit attempt raises, migration recovery must",
        "An `unresolved` result forbids automatic rerun and automatic append of a missing remainder",
        "generation-1 binary rejects sequences 2 and 3 as newer and unsupported",
        "generation-2 terminal-0002 binary ordinarily opens exact 0002 and rejects 0003 as newer",
        "generation-2 terminal-0003 binary ordinarily opens exact 0003",
        "no cumulative schema snapshot is introduced",
    ):
        _require(
            phrase in prose,
            f"{role}|heading={heading}|failure=generation_prefix_or_rollback",
        )
    _require(
        blocks
        == (
            MIGRATION_PATHS,
            MIGRATION_TRANSACTION_PATHS,
            MIGRATION_TRANSACTION_COMPONENTS,
            MIGRATION_RECOVERY_STEPS,
            MIGRATION_COMMITTED_EXACT,
            MIGRATION_DEFINITELY_NOT_COMMITTED,
            MIGRATION_UNRESOLVED,
            SQLITE_MIGRATION_DEFINITIONS,
            SQLITE_MIGRATION_SCHEMA_TOTALS,
        ),
        f"{role}|heading={heading}|failure=transaction_or_recovery_mapping",
    )
    lowered = prose.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS:
        _require(
            forbidden not in lowered,
            f"{role}|heading={heading}|failure=forbidden_migration_claim",
        )


def _assert_owner_structure(text: str) -> None:
    role = "c2b0.owner"
    headings, _unfenced = _markdown_scan(text, role=role)
    h1 = tuple(title for level, title, _start, _end in headings if level == 1)
    h2 = tuple(title for level, title, _start, _end in headings if level == 2)
    _require(
        h1 == ("C2B Durable Development State",),
        "c2b0.owner|heading=C2B Durable Development State|failure=missing_duplicate_or_relocated",
    )
    _require(
        h2 == SECTION_HEADINGS,
        "c2b0.owner|heading=<inventory>|failure=missing_duplicate_reordered_or_relocated",
    )
    for heading in SECTION_HEADINGS[:-1]:
        _section(text, heading)
    _section(text, SECTION_HEADINGS[-1])


def _text_blocks(section: str) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(line for line in block.content.splitlines() if line)
        for block in _top_level_fenced_blocks(section, role="c2b0.text_blocks")
        if block.info.strip(" \t") == "text"
    )


def _semantic_inventory_text(section: str, *, role: str) -> str:
    visible = _unfenced_markdown(section, role=role)
    block_text = "\n".join("\n".join(block) for block in _text_blocks(section))
    return visible + "\n" + block_text


def _replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1
    return text.replace(old, new, 1)


def _inventory_pseudo_closer_mutation(
    text: str,
    *,
    final_item: str,
    hidden_addition: str,
    closer_suffix: str,
) -> str:
    return _replace_once(
        text,
        final_item + "\n```",
        final_item
        + "\n```"
        + closer_suffix
        + "\n"
        + hidden_addition
        + "\n````",
    )


def _outer_nonsemantic_inventory_examples(hidden_addition: str) -> str:
    return (
        "~~~~example\n"
        "```text\n"
        + hidden_addition
        + "\n```\n"
        "~~~~\n\n"
        "````example\n"
        "~~~text\n"
        + hidden_addition
        + "\n~~~\n"
        "````\n"
    )


def _insert_before_owner_heading(
    text: str,
    *,
    next_heading: str,
    insertion: str,
) -> str:
    marker = "\n## " + next_heading + "\n"
    return _replace_once(text, marker, "\n" + insertion + marker)


def _assert_decision_and_cancel_contract(text: str) -> None:
    decisions = _section(text, SECTION_HEADINGS[5])
    cancel = _compact(_section(text, SECTION_HEADINGS[6]))
    _require(
        _text_blocks(decisions) == (DECISION_KINDS, DECISION_VERSION_EFFECTS),
        "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory",
    )
    _require(
        re.search(r"\bretry\b", _section_prose(text, SECTION_HEADINGS[5]), re.IGNORECASE)
        is None,
        "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=ninth_kind",
    )
    assert "cancel: no program-version advance" in decisions
    assert "`cancel` is a real immutable Coordinator decision" in cancel
    assert "Targets of class `cancel_effect` or `local_git_commit` are rejected." in cancel
    assert "An author target forbids the paired capsule fields." in cancel
    assert "A validation or review target requires the exact paired capsule-manifest ref and portable digest." in cancel
    assert "creates no version, attempt, candidate, command, effect, delivery, observation" in cancel
    for forbidden in (
        "block substitutes for cancel",
        "cancel creates a semantic attempt",
        "cancel creates a candidate",
        "cancel creates a WorkerCommandV1",
        "author target requires capsule fields",
    ):
        assert forbidden not in cancel


def _assert_basis_and_effect_contract(text: str) -> None:
    basis = _compact(_section(text, SECTION_HEADINGS[7]))
    cardinality = _compact(_section(text, SECTION_HEADINGS[8]))
    author = _compact(_section(text, SECTION_HEADINGS[9]))
    bound = _compact(_section(text, SECTION_HEADINGS[10]))
    assert "basis_decision_ref TEXT NOT NULL" in basis
    assert "REFERENCES development_decisions(decision_ref)" in basis
    assert "exact initialize, repair, or attempt-selecting replan decision" in basis
    assert "exact selection decision already bound to the existing attempt" in basis
    assert "exact cancel decision that preassigned the cancellation effect" in basis
    assert "`block` and `terminal_reject` cannot be a cancellation basis." in basis
    assert "`accept` and `redeliver` cannot be an author basis." in basis
    assert "development_effect_intents.command_ref: non-unique foreign key" in cardinality
    assert "one author_candidate effect per command" in cardinality
    assert "two originating commands for K1 is rejected" in cardinality
    assert "semantic attempt candidate identity through the attempt graph" in author
    assert "one originating WorkerCommandV1" in author
    for required_existing in (
        "existing semantic attempt",
        "existing candidate",
        "existing AttemptFence",
        "existing originating command",
        "existing post-bound author EffectFence",
    ):
        assert required_existing in bound
    assert "It creates no new semantic attempt, candidate, `WorkerCommandV1`, author effect, program version" in bound
    assert "Cancellation CAS-updates the target effect knowledge to `cancellation_effect_established`." in bound
    compacted_text = _compact(text).lower()
    for forbidden in (
        "basis_decision_ref TEXT NULL",
        "validation creates a second semantic attempt",
        "review creates a second WorkerCommandV1",
        "development_effect_intents.command_ref: unique foreign key",
        "two author effects per command are permitted",
    ):
        assert forbidden.lower() not in compacted_text


def _assert_stop_contract(text: str) -> None:
    section = _section(text, SECTION_HEADINGS[14])
    blocks = _text_blocks(section)
    matrix = next(block for block in blocks if block[0] == "initialize program: block")
    required = (
        "establish author effect: block",
        "establish validation effect: block",
        "establish review effect: block",
        "redeliver productive effect: block",
        "ingest source observation: permit",
        "record cancel decision: permit",
        "establish cancellation effect and initial cancellation delivery: permit",
        "redeliver an existing cancellation effect: permit",
        "perform external cancellation: not implemented",
    )
    for rule in required:
        assert rule in matrix
    compact = _compact(section)
    assert "`coding_global_stop_active` and creates no receipt" in compact
    assert "`global_stop_version_conflict` and creates no receipt" in compact
    assert "Exact replay of an already committed operation precedes fresh stop/head checks" in compact


def _assert_privacy_contract(text: str) -> None:
    custody = _compact(_section(text, SECTION_HEADINGS[15]))
    values = _compact(_section(text, SECTION_HEADINGS[16]))
    assert "The physical custodian is explicitly deferred." in custody
    assert "Coordinator SQLite is a safe-reference holder, not a private-material store." in custody
    assert "A safe ref is not retrieval authority." in custody
    assert "SQLite cannot reconstruct the private WorkSpec." in custody
    assert "Restart-safe author establishment and worker launch remain blocked" in custody
    assert "WorkSpecV1: safe projection only; exclude objective, requirements, exclusions" in values
    assert "CapsuleEntryV1: persist nothing" in values
    assert "Candidate and capsule bytes, capsule entries, paths, modes, file digests, lengths" in values
    for forbidden in (
        "C2B may retain objective text",
        "A safe ref is retrieval authority",
        "SQLite can reconstruct the private WorkSpec",
        "CapsuleEntryV1: persist complete mapping",
    ):
        assert forbidden not in _compact(text)


def _assert_schema_contract(text: str) -> None:
    migration_0001 = _section_prose(text, SECTION_HEADINGS[19])
    migration_0002 = _section(text, SECTION_HEADINGS[20])
    migration_0003 = _section(text, SECTION_HEADINGS[21])
    totals_section = _section(text, SECTION_HEADINGS[22])
    totals = _section_prose(text, SECTION_HEADINGS[22])
    indexes = _section(text, SECTION_HEADINGS[23])
    assert "Migration `0001_initial` retains immutable bytes, checksum, history, and meanings." in migration_0001, (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=0001_immutability"
    )
    assert "C2B1 is a framework-only source/test reset: it adds no SQL or database change" in migration_0001, (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=c2b1_scope"
    )
    blocks_0002 = _text_blocks(migration_0002)
    blocks_0003 = _text_blocks(migration_0003)
    semantic_0002 = _semantic_inventory_text(
        migration_0002,
        role="c2b0.schema.migration_0002",
    )
    semantic_0003 = _semantic_inventory_text(
        migration_0003,
        role="c2b0.schema.migration_0003",
    )
    semantic_totals = _semantic_inventory_text(
        totals_section,
        role="c2b0.schema.totals",
    )
    semantic_indexes = _semantic_inventory_text(
        indexes,
        role="c2b0.schema.indexes",
    )
    trigger_semantics = "\n".join((semantic_0002, semantic_0003, semantic_totals))
    trigger_lines = tuple(line.strip() for line in trigger_semantics.splitlines())
    schema_role_claims = tuple(
        line
        for line in trigger_lines
        if re.match(r"^schema(?: tip)? [0-9]{4}[ \t]*:", line, re.IGNORECASE)
        and "trigger" in line.lower()
    )
    _require(
        schema_role_claims == TRIGGER_SCHEMA_ROLE_CLAIMS,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_role_inventory",
    )
    migration_addition_role_claims = tuple(
        line
        for line in trigger_lines
        if re.match(r"^000[0-9][ \t]*:[ \t]*[0-9]+[ \t]+tables[ \t]*,", line, re.IGNORECASE)
        and "trigger" in line.lower()
    )
    _require(
        migration_addition_role_claims == TRIGGER_MIGRATION_ADDITION_ROLE_CLAIMS,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_role_inventory",
    )
    aggregate_role_claims = tuple(
        _compact(match.group(0))
        for match in re.finditer(
            r"\bC2B(?:[ \t]+also)?[ \t]+adds\b[^.]*\btriggers\b[^.]*\.",
            trigger_semantics,
            re.IGNORECASE,
        )
    )
    _require(
        aggregate_role_claims == TRIGGER_AGGREGATE_ROLE_CLAIMS,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_role_inventory",
    )
    _require(
        blocks_0002.count(TABLES_0002) == 1,
        "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
    )
    _require(
        blocks_0003.count(TABLES_0003) == 1,
        "c2b0.schema|heading=22. Migration 0003|failure=table_inventory",
    )
    _require(
        _text_blocks(indexes) == (EXPLICIT_INDEXES,),
        "c2b0.schema|heading=24. Exact Explicit Indexes|failure=index_inventory",
    )
    identifiers_0002 = set(re.findall(r"\bdevelopment_[a-z0-9_]+\b", semantic_0002))
    identifiers_0003 = set(re.findall(r"\bdevelopment_[a-z0-9_]+\b", semantic_0003))
    _require(
        identifiers_0002 == set(TABLES_0002),
        "c2b0.schema|heading=21. Migration 0002|failure=additive_table_inventory",
    )
    _require(
        identifiers_0003 == set(TABLES_0003),
        "c2b0.schema|heading=22. Migration 0003|failure=additive_table_inventory",
    )
    _require(
        "C2B adds exactly twenty-eight tables, forty-six triggers, and two explicit indexes." in totals,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=addition_totals",
    )
    arithmetic_blocks = tuple(
        block
        for block in _text_blocks(totals_section)
        if block and block[0].startswith("0002: 15 immutable tables")
    )
    _require(
        len(arithmetic_blocks) == 1,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
    )
    arithmetic = arithmetic_blocks[0]
    _require(
        arithmetic == TRIGGER_ARITHMETIC,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
    )
    _require(
        _text_blocks(totals_section)
        == (SCHEMA_TOTALS, MIGRATION_ADDITION_TOTALS, TRIGGER_ARITHMETIC),
        "c2b0.schema|heading=23. Exact Schema Totals|failure=closed_totals_blocks",
    )
    arithmetic_claims = tuple(
        line.strip()
        for line in "\n".join(
            (semantic_0002, semantic_0003, semantic_totals)
        ).splitlines()
        if re.match(r"^[ \t]*000[0-9][ \t]*:", line, re.IGNORECASE)
    )
    _require(
        arithmetic_claims == MIGRATION_ADDITION_TOTALS + TRIGGER_ARITHMETIC,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=additive_trigger_arithmetic",
    )
    _require(
        "one available latch row" in totals,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=latch_seed",
    )
    visible = _unfenced_markdown(text, role="c2b0.owner")
    _require(
        "third_explicit_index" not in visible,
        "c2b0.schema|heading=24. Exact Explicit Indexes|failure=extra_index",
    )
    _require(
        "one broad migration" not in visible,
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=broad_migration",
    )
    index_identifiers = set(
        re.findall(r"\b(?:idx|uq)_[a-z0-9_]+\b", semantic_indexes)
    )
    _require(
        index_identifiers == set(EXPLICIT_INDEXES),
        "c2b0.schema|heading=24. Exact Explicit Indexes|failure=additive_index",
    )
    trigger_identifier_sections = semantic_0002 + semantic_0003 + semantic_totals
    _require(
        re.search(
            r"\b[a-z0-9]+(?:_[a-z0-9]+)*_trigger(?:_[a-z0-9]+)*\b",
            trigger_identifier_sections,
        )
        is None,
        "c2b0.schema|heading=23. Exact Schema Totals|failure=additive_trigger",
    )
    lowered_schema = _compact(
        semantic_0002 + semantic_0003 + semantic_totals + semantic_indexes
    ).lower()
    for forbidden in (
        "migration 0002 also creates an additional table",
        "migration 0003 also creates an additional table",
        "migration 0003 also creates an extra trigger",
        "one trigger is omitted",
        "the latch update is unrestricted",
        "a third explicit index is added",
        "a reporting index is added",
        "a lineage index is added",
        "a browsing index is added",
        "an analytics index is added",
    ):
        _require(
            forbidden not in lowered_schema,
            "c2b0.schema|heading=<inventory>|failure=additive_schema_claim",
        )
    mutable = set(MUTABLE_HEADS) - {"development_first_slice_latch"}
    immutable = (set(TABLES_0002) | set(TABLES_0003)) - set(MUTABLE_HEADS)
    for table in mutable:
        _require(
            f"{table} is immutable" not in lowered_schema,
            "c2b0.schema|heading=<inventory>|failure=mutable_immutable_swap",
        )
    for table in immutable:
        _require(
            f"{table} is mutable" not in lowered_schema,
            "c2b0.schema|heading=<inventory>|failure=mutable_immutable_swap",
        )


def _assert_tranche_contract(text: str) -> None:
    section = _section(text, SECTION_HEADINGS[25])
    blocks = _text_blocks(section)
    _require(
        bool(blocks),
        "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=missing_sequence",
    )
    block = blocks[0]
    _require(
        tuple(line.split(":", 1)[0] for line in block) == TRANCHES,
        "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=labels",
    )
    _require(
        block == TRANCHE_LINES,
        "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=ownership_or_generation",
    )
    prose = _section_prose(text, SECTION_HEADINGS[25])
    assert "Productive redelivery is blocked by active stop" in prose
    assert "cancellation redelivery remains risk-reducing and permitted" in prose
    lowered = prose.lower()
    for forbidden in (
        "c2b4 owns initialize decision representation.",
        "c2b4 is the first tranche where durable decision rows are representable.",
        "c2b3 introduces a separate development_initialization_decisions table.",
        "c2b4 and c2b5 both own source-observation ingest.",
        "no tranche owns bound validation or review effect establishment.",
        "c2b4 and c2b5 both own the same mechanic.",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=additive_ownership",
        )


def _assert_current_target_status(text: str) -> None:
    status = _section_prose(text, SECTION_HEADINGS[0])
    required = (
        "The current implemented application generation remains 1",
        "the packaged catalog and managed database tip remain `0001_initial`",
        "schema 0001 is unchanged",
        "The accepted C2B target reserves migrations",
        "`0002_development_program_and_effect_state`",
        "`0003_development_observation_and_progression_state`",
        "exact target responsibilities and inventories are frozen below",
        "No 0002/0003 SQL, catalog entry, schema object, installed migration, application-generation change",
        "C2B reader, writer, mutation, transaction, ingest",
    )
    for phrase in required:
        _require(
            phrase in status,
            "c2b0.status|heading=1. Status, Classification, And Layering|failure=current_target_distinction",
        )
    visible = _unfenced_markdown(text, role="c2b0.owner").lower()
    for stale in (
        "no migration number is reserved here",
        "no migration number is reserved.",
        "exact future state shape, schema, migrations",
        "exact c2b schema remains wholly open.",
        "c2b is currently implemented",
        "migrations 0002 and 0003 are currently installed",
        "0002 is installed.",
        "0003 is installed.",
        "application generation is currently 2.",
    ):
        _require(
            stale not in visible,
            "c2b0.status|heading=1. Status, Classification, And Layering|failure=stale_or_current_claim",
        )


def _assert_application_generation_contract(text: str) -> None:
    strategy = _section_prose(text, SECTION_HEADINGS[19])
    for phrase in (
        "C2B1 is a framework-only source/test reset: it adds no SQL or database change",
        "the implemented application generation remains 1",
        "current catalog and terminal tip remain `0001_initial`",
        "C2B2 advances the implemented application generation from 1 to 2",
        "catalog terminal tip becomes 0002",
        "C2B3 remains application generation 2 with terminal migration 0002",
        "C2B4 adds migration 0003 while retaining application generation 2",
        "terminal tip becomes 0003",
        "C2B5 and C2B6 remain application generation 2 with terminal migration 0003",
    ):
        assert phrase in strategy, (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation"
        )
    lowered = strategy.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS[:6]:
        _require(
            forbidden not in lowered,
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation",
        )
    _assert_tranche_contract(text)


def _assert_cumulative_migration_contract(text: str) -> None:
    strategy_section = _section(text, SECTION_HEADINGS[19])
    strategy = _section_prose(text, SECTION_HEADINGS[19])
    assert MIGRATION_PATHS in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=cumulative_paths"
    )
    assert ORDINARY_OPEN_RULES in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=open_or_prefix_rule"
    )
    assert MIGRATION_TRANSACTION_PATHS in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=complete_suffix_transaction"
    )
    assert MIGRATION_TRANSACTION_COMPONENTS in _text_blocks(strategy_section), (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=complete_suffix_transaction"
    )
    for phrase in (
        "Ordinary product or writer open requires all of the following",
        "Ordinary open never silently migrates and never accepts an older prefix.",
        "one exact non-empty supported older catalog prefix",
        "exact packaged checksum and metadata",
        "no gaps, unknown rows, partial rows, or divergent bounds or flags",
        "one exact contiguous packaged suffix leads to the current terminal tip",
        "migration-eligible only; it is not ordinarily product-openable before migration",
        "the complete intended packaged suffix is one administrative transaction",
        "No suffix migration may commit before a later migration in the same selected suffix is attempted",
        "Ordinary product or writer open never performs migration",
    ):
        assert phrase in strategy, (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=open_or_prefix_rule"
        )
    lowered = strategy.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS[6:17]:
        _require(
            forbidden not in lowered,
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_prefix_or_suffix_claim",
        )


def _assert_migration_failure_and_history_contract(text: str) -> None:
    strategy_section = _section(text, SECTION_HEADINGS[19])
    strategy = _section_prose(text, SECTION_HEADINGS[19])
    for phrase in (
        "Every installed migration row remains immutable",
        "sequence, migration ID, checksum, compatibility bounds, and destructive flag",
        "Historical `0001_initial` therefore remains `[1,1]`",
        "migrations 0002 and 0003 are each `[2,2]`",
        "do not require every historical row to include the running application generation",
        "Every migration selected for that suffix contributes all of the following to the same administrative transaction",
        "Failure before commit restores the complete exact prior supported prefix",
        "never rewrites 0001",
        "If an administrative commit attempt raises, migration recovery must",
        "An `unresolved` result forbids automatic rerun and automatic append of a missing remainder",
        "An operator or separately accepted recovery must complete before another migration attempt",
    ):
        assert phrase in strategy, (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=history_or_rollback"
        )
    blocks = _text_blocks(strategy_section)
    _require(
        blocks
        == (
            ORDINARY_OPEN_RULES,
            MIGRATION_PATHS,
            MIGRATION_TRANSACTION_PATHS,
            MIGRATION_TRANSACTION_COMPONENTS,
            MIGRATION_RECOVERY_STEPS,
            MIGRATION_COMMITTED_EXACT,
            MIGRATION_DEFINITELY_NOT_COMMITTED,
            MIGRATION_UNRESOLVED,
        ),
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping",
    )
    lowered = strategy.lower()
    for forbidden in MIGRATION_FORBIDDEN_CLAIMS[16:]:
        _require(
            forbidden not in lowered,
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim",
        )


def _assert_decision_tranche_ownership(text: str) -> None:
    migration_0002 = _section_prose(text, SECTION_HEADINGS[20])
    for phrase in (
        "C2B2 owns and lands both the base decision envelope and initialize-decision row treatment",
        "without adding a mutation API",
        "C2B3 later uses that representation for program initialization",
        "C2B4 adds only non-initialize, evidence-bearing decision contracts",
        "it neither owns initialize representation nor is the first point at which a durable decision row is representable",
        "not a generic decision metadata bag",
    ):
        assert phrase in migration_0002, (
            "c2b0.tranches|heading=21. Migration 0002|failure=decision_representation_ownership"
        )
    lowered = migration_0002.lower()
    for forbidden in (
        "c2b4 owns initialize decision representation.",
        "c2b4 is the first tranche where durable decision rows are representable.",
        "c2b3 introduces a separate development_initialization_decisions table.",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.tranches|heading=21. Migration 0002|failure=additive_decision_ownership",
        )
    _assert_tranche_contract(text)


def _assert_observation_ingest_authority(text: str) -> None:
    observation_section = _section(text, SECTION_HEADINGS[12])
    observation = _section_prose(text, SECTION_HEADINGS[12])
    for phrase in (
        "A source observation is a source-authored record and digest.",
        "An ingest disposition is a Coordinator-authored classification.",
        "A progression decision is a separate Coordinator-authored semantic judgment.",
        "No observation or disposition directly authorizes acceptance, repair, replan, redelivery, publication, or program completion.",
    ):
        assert phrase in observation, (
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=authorship_or_acceptance_collapse"
        )
    _require(
        _text_blocks(observation_section) == (OBSERVATION_INGEST_STEPS, DISPOSITIONS),
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory",
    )
    lowered = observation.lower()
    for forbidden in (
        "source observation and ingest disposition share one authorship identity",
        "source observation and coordinator ingest disposition use one identity and author row",
        "coordinator authors source observations",
        "the source authors coordinator ingest dispositions",
        "an ingest disposition directly creates accept",
        "an ingest disposition directly creates semantic acceptance",
        "an ingest disposition directly creates repair",
        "an ingest disposition directly creates replan",
        "an ingest disposition directly creates publication eligibility",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=additive_authorship_or_acceptance",
        )
    _require(
        re.search(r"\baccepted\b", observation, re.IGNORECASE) is None,
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory",
    )


def _assert_global_latch_scope(text: str) -> None:
    latch = _section(text, SECTION_HEADINGS[18])
    blocks = _text_blocks(latch)
    contracts = tuple(
        block for block in blocks if block and block[0].startswith("latch_ref:")
    )
    _require(
        len(contracts) == 1,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=contract_inventory",
    )
    contract = contracts[0]
    _require(
        contract == LATCH_CONTRACT,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope",
    )
    _require(
        blocks == (contract,),
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=contract_inventory",
    )
    _require(
        "scope: per program" not in contract,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=per_program_scope",
    )
    latch_prose = _unfenced_markdown(
        latch,
        role="c2b0.owner.section.19. First-Slice One-Shot Latch",
    )
    lowered = _compact(latch_prose).lower()
    _require(
        re.search(r"^[ \t]*(?:latch_ref|reuse)[ \t]*:", latch_prose, re.IGNORECASE | re.MULTILINE)
        is None,
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=additive_scope_or_lifecycle",
    )
    migration_0003 = _section(text, SECTION_HEADINGS[21])
    seed_contracts = tuple(
        block
        for block in _text_blocks(migration_0003)
        if block and re.match(r"^latch_ref[ \t]*:", block[0], re.IGNORECASE)
    )
    _require(
        len(seed_contracts) == 1,
        "c2b0.semantic|heading=22. Migration 0003|failure=latch_seed_binding",
    )
    _require(
        seed_contracts[0] == LATCH_SEED_CONTRACT,
        "c2b0.semantic|heading=22. Migration 0003|failure=latch_seed_binding",
    )
    owner_semantics = _semantic_inventory_text(
        text,
        role="c2b0.semantic.latch_owner",
    )
    declarations = tuple(
        line.strip()
        for line in owner_semantics.splitlines()
        if re.match(r"^[ \t]*(?:latch_ref|reuse)[ \t]*:", line, re.IGNORECASE)
    )
    _require(
        declarations == LATCH_DECLARATION_INVENTORY,
        "c2b0.semantic|heading=<owner>|failure=latch_declaration_inventory",
    )
    for forbidden in (
        "the latch is per-program durable truth",
        "the latch is per-program-version durable truth",
        "the latch is per-work-item durable truth",
        "the consumed latch may be reset to available",
        "the latch is reusable",
        "the latch row may be deleted",
        "the latch row may be recreated",
        "the latch is scheduler-authoritative",
        "the latch is queue-authoritative",
        "the latch is general program truth",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=additive_scope_or_lifecycle",
        )


def _assert_closed_ledger_metadata_and_trigger_contract(text: str) -> None:
    hybrid = _section_prose(text, SECTION_HEADINGS[3])
    migration_0002 = _section_prose(text, SECTION_HEADINGS[20])
    migration_0003 = _section_prose(text, SECTION_HEADINGS[21])
    assert "C2B rejects one mutable aggregate JSON row, fully mutable normalized history, one generic event ledger" in hybrid, (
        "c2b0.semantic|heading=4. Hybrid Durable Representation|failure=generic_event_ledger"
    )
    assert "not a generic decision metadata bag" in migration_0002, (
        "c2b0.semantic|heading=21. Migration 0002|failure=generic_decision_bag"
    )
    assert "closed role-specific relation, not a metadata bag" in migration_0003, (
        "c2b0.semantic|heading=22. Migration 0003|failure=generic_evidence_bag"
    )
    migration_0003_section = _section(text, SECTION_HEADINGS[21])
    _require(
        _text_blocks(migration_0003_section).count(CANCELLATION_EVIDENCE_ROLES) == 1,
        "c2b0.semantic|heading=22. Migration 0003|failure=evidence_role_inventory",
    )
    lowered = " ".join((hybrid, migration_0002, migration_0003)).lower()
    for forbidden in (
        "c2b also uses one generic event ledger as durable program truth",
        "c2b uses one generic event ledger as durable program truth",
        "c2b also uses one generic evidence metadata bag",
        "c2b also uses one generic decision json bag",
        "decision evidence permits arbitrary role strings",
        "durable decisions permit arbitrary payload json metadata",
        "decision payloads are open-ended",
    ):
        _require(
            forbidden not in lowered,
            "c2b0.semantic|heading=<closed-structure>|failure=additive_generic_structure",
        )
    _assert_schema_contract(text)


def _assert_mutation_and_recovery_family_contract(text: str) -> None:
    section = _section(text, SECTION_HEADINGS[11])
    blocks = _text_blocks(section)
    _require(
        blocks == (MUTATION_FAMILIES, RECOVERY_FAMILIES),
        "c2b0.families|heading=12. Complete Target Mutation Families|failure=closed_blocks",
    )
    identifiers = set(
        re.findall(
            r"(?<![A-Za-z0-9])_[a-z][a-z0-9_]*",
            _semantic_inventory_text(section, role="c2b0.families"),
        )
    )
    _require(
        identifiers == set(MUTATION_FAMILIES + RECOVERY_FAMILIES),
        "c2b0.families|heading=12. Complete Target Mutation Families|failure=additive_family",
    )


def test_owner_is_unique_and_section_inventory_is_exact() -> None:
    text = _owner()
    _assert_owner_structure(text)
    owner_headings = tuple(
        path
        for path in (ROOT / ".docs").glob("*.md")
        if path.read_text(encoding="utf-8").startswith("# C2B Durable Development State\n")
    )
    assert owner_headings == (OWNER_PATH,)


def test_current_versus_target_and_one_writer_are_explicit() -> None:
    text = _owner()
    _assert_current_target_status(text)
    status = _section_prose(text, SECTION_HEADINGS[0])
    authority = _compact(_section(text, SECTION_HEADINGS[1]))
    for phrase in (
        "Classification: `ACCEPTED TARGET CONTRACT`.",
        "C2B0 changes documentation and direct documentation-contract tests only.",
        "The current implementation is absent.",
        "The current implemented application generation remains 1",
        "one existing Coordinator SQLite database",
        "one existing writer issuance and fencing authority",
        "one existing operation guard",
        "one existing mutation slot",
        "one existing transaction controller",
        "no second database, writer, session authority, transaction controller",
        "Persistence of a reference or digest never transfers authorship",
    ):
        assert phrase in status or phrase in authority


def test_identity_and_hybrid_representation_are_closed() -> None:
    identities = _section(_owner(), SECTION_HEADINGS[2])
    hybrid = _compact(_section(_owner(), SECTION_HEADINGS[3]))
    assert len(_text_blocks(identities)[0]) == 21
    assert MUTABLE_HEADS in _text_blocks(_section(_owner(), SECTION_HEADINGS[3]))
    assert "one-way `available` to `consumed` transition" in hybrid
    assert "one generic event ledger" in hybrid
    assert "reuse of `work_items` or `transition_events` as target truth" in hybrid


def test_program_genesis_and_deferred_cycle_are_exact() -> None:
    genesis = _compact(_section(_owner(), SECTION_HEADINGS[4]))
    for phrase in (
        "real immutable `initialize` decision",
        "program_version_number: 1",
        "program_version_kind: initial",
        "creating_decision_ref: required and non-null",
        "initial program head revision: 0",
        "preassigned semantic attempt: required",
        "preassigned candidate: required",
        "It creates no semantic-attempt row, effect, command, delivery, observation",
        "`DEFERRABLE INITIALLY DEFERRED`",
        "Foreign keys are never disabled.",
    ):
        assert phrase in genesis


def test_decisions_cancel_basis_and_effect_roles_are_exact() -> None:
    text = _owner()
    _assert_decision_and_cancel_contract(text)
    _assert_basis_and_effect_contract(text)


def test_mutation_and_recovery_family_inventories_are_independent_literals() -> None:
    section = _section(_owner(), SECTION_HEADINGS[11])
    blocks = _text_blocks(section)
    assert blocks == (MUTATION_FAMILIES, RECOVERY_FAMILIES)
    assert "not public package APIs or stable external methods" in _compact(section)
    assert "C2B0 implements none of them." in section
    _assert_mutation_and_recovery_family_contract(_owner())


def test_observation_disposition_and_redelivery_boundaries_are_exact() -> None:
    _assert_observation_ingest_authority(_owner())
    observation = _section(_owner(), SECTION_HEADINGS[12])
    redelivery = _compact(_section(_owner(), SECTION_HEADINGS[13]))
    assert DISPOSITIONS in _text_blocks(observation)
    assert "Source-observation identity is `(observation_ref, observation_digest)`." in observation
    assert "A malformed observation creates no claim, disposition, receipt, or head change." in _compact(observation)
    assert "No observation or disposition directly authorizes acceptance, repair, replan, redelivery, publication, or program completion." in _compact(observation)
    for phrase in (
        "Unknown source observation",
        "Coordinator redeliver decision",
        "successor delivery attempt",
        "actual redelivery remain distinct",
        "C2B does not perform redelivery",
        "timeout-as-failure",
        "Bridge recovery authority",
    ):
        assert phrase in redelivery


def test_split_stop_matrix_is_exact() -> None:
    _assert_stop_contract(_owner())


def test_workspec_and_c2a_value_privacy_are_exact() -> None:
    _assert_privacy_contract(_owner())


def test_authority_evaluation_and_latch_are_non_authoritative_and_one_shot() -> None:
    authority = _compact(_section(_owner(), SECTION_HEADINGS[17]))
    latch = _compact(_section(_owner(), SECTION_HEADINGS[18]))
    for state in ("pending", "verified", "blocked", "stale", "revoked", "expired"):
        assert state in authority
    assert "A separately accepted external verifier must supply `verified`" in authority
    assert "or Coordinator decision is not executable authorization" in authority
    assert "latch_ref: direct_local_first_productive_acceptance" in latch
    assert "initial state: available" in latch
    assert "initial version: 0" in latch
    assert "final state: consumed" in latch
    assert "final version: 1" in latch
    assert "reset: forbidden" in latch
    assert "delete: forbidden" in latch
    assert "blocks a second productive acceptance" in latch
    _assert_global_latch_scope(_owner())


def test_migration_tables_totals_triggers_indexes_and_bootstrap_are_exact() -> None:
    _assert_schema_contract(_owner())
    _assert_application_generation_contract(_owner())
    _assert_cumulative_migration_contract(_owner())
    _assert_migration_failure_and_history_contract(_owner())
    _assert_decision_tranche_ownership(_owner())


def test_transaction_replay_cas_uncertainty_and_tranches_are_exact() -> None:
    transaction = _compact(_section(_owner(), SECTION_HEADINGS[24]))
    for phrase in (
        "1. exact command-local preflight",
        "7. durable writer fencing",
        "8. mutation-receipt lookup",
        "9. exact replay or same-key conflict",
        "14. capability invalidation",
        "15. exactly one commit attempt",
        "same mutation_ref + same canonical digest: exact replay",
        "mutation_ref_reuse_conflict",
        "program_head_conflict",
        "target_effect_state_conflict",
        "coding_global_stop_active",
        "commit_outcome_unknown",
        "committed_exact",
        "definitely_not_committed",
        "unresolved",
        "No mutation automatically retries",
    ):
        assert phrase in transaction
    _assert_tranche_contract(_owner())


def test_c2b0_current_and_target_status_are_consistent() -> None:
    _assert_current_target_status(_owner())


def test_c2b0_stale_no_migration_reserved_wording_is_rejected() -> None:
    text = _owner()
    mutations = (
        _replace_once(
            text,
            "The accepted C2B target reserves migrations",
            "No migration number is reserved here; a future C2B requires a separately accepted durable schema and forward migration.",
        ),
        text + "\nExact future state shape, schema, migrations remain wholly open.\n",
        text + "\nC2B is currently implemented.\n",
        text + "\nMigrations 0002 and 0003 are currently installed.\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(mutation)
        assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
            rejected.value
        )


def test_c2b0_current_target_status_rejects_all_additive_stale_claims() -> None:
    text = _owner()
    stale_claims = (
        "Exact C2B schema remains wholly open.",
        "0002 is installed.",
        "0003 is installed.",
        "Application generation is currently 2.",
        "No migration number is reserved.",
        "C2B is currently implemented.",
    )
    for stale in stale_claims:
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(text + f"\n{stale}\n")
        assert str(rejected.value) == (
            "c2b0.status|heading=1. Status, Classification, And Layering|failure=stale_or_current_claim"
        )

    fenced = text + "\n~~~example`info\n" + "\n".join(stale_claims) + "\n~~~\n"
    _assert_current_target_status(fenced)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_authority_bypass() -> None:
    text = _owner()
    mutation = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_current_target_status(mutation)
    assert str(rejected.value) == (
        "c2b0.status|heading=1. Status, Classification, And Layering|failure=stale_or_current_claim"
    )

    valid_tilde = text + "\n~~~bad`info\nC2B is currently implemented.\n~~~\n"
    _assert_current_target_status(valid_tilde)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_duplicate_heading_bypass() -> None:
    text = _owner()
    mutation = (
        text
        + "\n```bad`info\n## 1. Status, Classification, And Layering\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_owner_structure(mutation)
    assert str(rejected.value) == (
        "c2b0.owner|heading=<inventory>|failure=missing_duplicate_reordered_or_relocated"
    )


def test_c2b0_application_generation_transition_is_exact() -> None:
    text = _owner()
    _assert_application_generation_contract(text)
    sqlite_text = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_sqlite_migration_summary(sqlite_text)
    for mutation in (
        _replace_once(
            text,
            "C2B2 advances the implemented application generation from 1 to 2",
            "C2B2 leaves the implemented application generation at 1",
        ),
        _replace_once(
            text,
            "C2B4 adds migration 0003\nwhile retaining application generation 2",
            "C2B4 adds migration 0003 and advances application generation to 3",
        ),
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_application_generation_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation" in str(
            rejected.value
        )
    sqlite_mutation = _replace_once(
        sqlite_text,
        "C2B2 advances implemented application generation from 1 to 2",
        "C2B2 leaves implemented application generation at 1",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=generation_prefix_or_rollback"
    )


def test_c2b0_cumulative_fresh_install_and_supported_prefix_rules_are_exact() -> None:
    text = _owner()
    _assert_cumulative_migration_contract(text)
    _assert_sqlite_migration_summary(_text(".docs/sqlite-bootstrap-and-migrations.md"))
    for mutation in (
        _replace_once(
            text,
            "C2B4-or-later fresh installation: 0001 -> 0002 -> 0003",
            "C2B4-or-later fresh installation: apply only 0003",
        ),
        _replace_once(
            text,
            "Ordinary open never silently migrates and never accepts an older prefix.",
            "Ordinary open accepts exact 0001 or 0002 as an older prefix.",
        ),
        _replace_once(
            text,
            "one exact non-empty supported older\ncatalog prefix",
            "any non-exact or unsupported older catalog prefix",
        ),
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_cumulative_migration_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=" in str(
            rejected.value
        )


def test_c2b0_migration_failure_and_history_immutability_are_exact() -> None:
    text = _owner()
    _assert_migration_failure_and_history_contract(text)
    _assert_sqlite_migration_summary(_text(".docs/sqlite-bootstrap-and-migrations.md"))
    for mutation in (
        _replace_once(text, "Historical `0001_initial` therefore remains `[1,1]`", "Historical `0001_initial` is rewritten to `[1,2]`"),
        _replace_once(text, "Historical `0001_initial` therefore remains `[1,1]`", "Historical `0001_initial` is rewritten to `[2,2]`"),
        _replace_once(
            text,
            "Failure before commit restores the complete exact prior supported\nprefix with no partial DDL, invariant change, or history row",
            "Failure before commit may retain partial DDL or a partial history row",
        ),
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_migration_failure_and_history_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=history_or_rollback" in str(
            rejected.value
        )


def test_c2b0_complete_migration_suffix_uses_one_administrative_transaction() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_cumulative_migration_contract(owner)
    _assert_sqlite_migration_summary(sqlite)

    split_claim = "C2B4 upgrade from exact 0001 commits 0002 before starting 0003."
    owner_mutation = _replace_once(
        owner,
        "Ordinary product or writer open never performs migration.",
        "Ordinary product or writer open never performs migration.\n\n" + split_claim,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_cumulative_migration_contract(owner_mutation)
    assert str(rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_prefix_or_suffix_claim"
    )

    sqlite_mutation = _replace_once(
        sqlite,
        "Ordinary product or writer open never performs migration.",
        "Ordinary product or writer open never performs migration.\n\n" + split_claim,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
    )


def test_c2b0_migration_commit_uncertainty_mapping_is_exact() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)

    contradictions = (
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
    )
    for contradiction in contradictions:
        owner_mutation = _replace_once(
            owner,
            "The evidence classifications are exact:",
            "The evidence classifications are exact:\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_migration_failure_and_history_contract(owner_mutation)
        assert str(rejected.value) == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
        )

        sqlite_mutation = _replace_once(
            sqlite,
            "The evidence classifications are exact:",
            "The evidence classifications are exact:\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_sqlite_migration_summary(sqlite_mutation)
        assert str(rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
        )


def test_c2b0_unresolved_migration_forbids_automatic_rerun() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    contradiction = "After an unresolved migration commit, the suffix is automatically rerun."
    owner_mutation = _replace_once(
        owner,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_migration_failure_and_history_contract(owner_mutation)
    assert str(rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
    )

    sqlite_mutation = _replace_once(
        sqlite,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
    )


def test_c2b0_owner_sections_are_fence_aware_unique_and_ordered() -> None:
    text = _owner()
    _assert_owner_structure(text)

    fenced_shadows = (
        text
        + "\n```markdown\n## 1. Status, Classification, And Layering\n````\n"
        + "~~~~markdown\n  ## 2. One Database, One Writer, And Fact Ownership ###\n~~~~~\n"
    )
    _assert_owner_structure(fenced_shadows)

    lower_level = _replace_once(
        text,
        "Classification: `ACCEPTED TARGET CONTRACT`.\n\nC2B0 changes",
        "Classification: `ACCEPTED TARGET CONTRACT`.\n\n### Local Detail\n\nC2B0 changes",
    )
    _assert_current_target_status(lower_level)

    mutations = (
        "```markdown\n" + text + "```\n",
        text + "\n## 1. Status, Classification, And Layering\n",
        text + "\n  ## 1. Status, Classification, And Layering ###\n",
        text + "\n##\t1. Status, Classification, And Layering\n",
        _replace_once(
            text,
            "## 1. Status, Classification, And Layering\n",
            "",
        ),
        _replace_once(
            _replace_once(
                text,
                "## 1. Status, Classification, And Layering",
                "## TEMPORARY OWNER HEADING",
            ),
            "## 2. One Database, One Writer, And Fact Ownership",
            "## 1. Status, Classification, And Layering",
        ).replace(
            "## TEMPORARY OWNER HEADING",
            "## 2. One Database, One Writer, And Fact Ownership",
            1,
        ),
        text + "\n~~~markdown\n## 1. Status, Classification, And Layering\n```\n",
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_owner_structure(mutation)
        assert str(rejected.value).startswith("c2b0.owner|heading=")

    for boundary in ("## Relocated Status", "# Relocated Status"):
        mutation = _replace_once(
            text,
            "Classification: `ACCEPTED TARGET CONTRACT`.\n\nC2B0 changes",
            f"Classification: `ACCEPTED TARGET CONTRACT`.\n\n{boundary}\n\nC2B0 changes",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(mutation)
        assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=current_target_distinction" in str(
            rejected.value
        )


def test_c2b0_summary_sections_ignore_fenced_target_claims() -> None:
    summaries = (
        (
            _text(".docs/durable-state-model.md"),
            "c2b0.summary.durable_state",
            "C2B0 Accepted Durable-Development Target",
            "The accepted target comprises migrations",
        ),
        (
            _text(".docs/architecture.md"),
            "c2b0.summary.architecture",
            "C2B0 Accepted Durable-State Target Topology",
            "Status: `ACCEPTED TARGET CONTRACT`; implementation absent.",
        ),
        (
            _text(".docs/autonomous-software-development-operating-model.md"),
            "c2b0.summary.operating_model",
            "C2B0 Accepted Durable-State Composition Overlay",
            "C2B0 closes only the target durable-state seams",
        ),
        (
            _text(".docs/software-development-progression-boundary.md"),
            "c2b0.summary.progression",
            "C2B0 Accepted Durable Progression Closure",
            "C2B remains unimplemented.",
        ),
    )
    for text, role, heading, required in summaries:
        _assert_summary_target(text, role=role, heading=heading, required=required)

    durable, role, heading, required = summaries[0]
    fenced_only = _replace_once(durable, required, f"```text\n{required}\n```")
    with pytest.raises(AssertionError) as rejected:
        _assert_summary_target(fenced_only, role=role, heading=heading, required=required)
    assert str(rejected.value) == (
        "c2b0.summary.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=target_claim_missing"
    )

    contradictory = durable + "\n# Contradictory Current Status\n\nC2B is currently implemented.\n"
    with pytest.raises(AssertionError) as rejected:
        _assert_summary_target(contradictory, role=role, heading=heading, required=required)
    assert str(rejected.value) == (
        "c2b0.summary.durable_state|heading=C2B0 Accepted Durable-Development Target|failure=contradictory_current_status"
    )


def test_c2b0_observation_ingest_and_decision_authorship_are_distinct() -> None:
    text = _owner()
    _assert_observation_ingest_authority(text)
    mutations = (
        _replace_once(
            text,
            "A source observation is a source-authored\nrecord and digest. An ingest disposition is a Coordinator-authored\nclassification.",
            "A source observation and Coordinator ingest disposition use one identity and author row.",
        ),
        _replace_once(
            text,
            "No observation or disposition directly authorizes acceptance, repair,\nreplan, redelivery, publication, or program completion.",
            "An ingest disposition directly creates semantic acceptance.",
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=authorship_or_acceptance_collapse" in str(
            rejected.value
        )


def test_c2b0_first_slice_latch_scope_is_global_bootstrap() -> None:
    text = _owner()
    _assert_global_latch_scope(text)
    mutation = _replace_once(
        text,
        "scope: global Coordinator bootstrap",
        "scope: per program",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_global_latch_scope(mutation)
    assert "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope" in str(
        rejected.value
    )


def test_c2b0_decision_representation_tranche_ownership_is_exact() -> None:
    text = _owner()
    _assert_decision_tranche_ownership(text)
    mutations = (
        _replace_once(
            text,
            "C2B2 owns and lands both the base\ndecision envelope and initialize-decision row treatment",
            "C2B2 omits the base decision envelope and initialize-decision row treatment",
        ),
        _replace_once(
            text,
            "C2B4 adds only non-initialize, evidence-bearing decision contracts; it neither\nowns initialize representation nor is the first point at which a durable\ndecision row is representable.",
            "C2B4 is the first tranche where a durable decision row is representable and owns initialize representation.",
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_tranche_ownership(mutation)
        assert "c2b0.tranches|heading=21. Migration 0002|failure=decision_representation_ownership" in str(
            rejected.value
        )


def test_c2b0_trigger_inventory_has_no_extra_trigger() -> None:
    text = _owner()
    _assert_schema_contract(text)
    for extra in (
        "0003: extra immutable table * no-update/no-delete = 2",
        "0003: one extra trigger without a table-count change = 1",
    ):
        mutation = _replace_once(
            text,
            "0003: latch one-way update guard = 1\n```",
            f"0003: latch one-way update guard = 1\n{extra}\n```",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_schema_contract(mutation)
        assert "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic" in str(
            rejected.value
        )


def test_c2b0_rejects_generic_event_ledger_and_metadata_bags() -> None:
    text = _owner()
    _assert_closed_ledger_metadata_and_trigger_contract(text)
    mutations = (
        _replace_once(
            text,
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
            "C2B introduces one generic event ledger as durable program truth and uses one mutable aggregate JSON row",
        ),
        _replace_once(
            text,
            "closed role-specific relation,\nnot a metadata bag",
            "generic evidence metadata bag",
        ),
        _replace_once(
            text,
            "closed\nkind-specific contract, not a generic decision metadata bag",
            "generic decision metadata bag",
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_closed_ledger_metadata_and_trigger_contract(mutation)
        assert "c2b0.semantic|heading=" in str(rejected.value)


def test_c2b0_observation_ingest_and_decision_contract_is_additively_closed() -> None:
    text = _owner()
    marker = (
        "No observation or disposition directly authorizes acceptance, repair,\n"
        "replan, redelivery, publication, or program completion."
    )
    contradictions = (
        "A source observation and ingest disposition share one authorship identity.",
        "Coordinator authors source observations.",
        "The source authors Coordinator ingest dispositions.",
        "An ingest disposition directly creates accept.",
        "An ingest disposition directly creates repair.",
        "An ingest disposition directly creates replan.",
        "An ingest disposition directly creates publication eligibility.",
    )
    for contradiction in contradictions:
        mutation = _replace_once(text, marker, marker + "\n\n" + contradiction)
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=additive_authorship_or_acceptance"
        )

    added_disposition = _replace_once(
        text,
        "late_retained\nrecorded\n```",
        "late_retained\nrecorded\naccepted\n```",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_observation_ingest_authority(added_disposition)
    assert str(rejected.value) == (
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
    )


def test_c2b0_first_slice_latch_contract_is_additively_closed() -> None:
    text = _owner()
    marker = "The latch is not a scheduler, queue, backlog, lease, or general program truth."
    contradictions = (
        "The latch is per-program durable truth.",
        "The latch is per-program-version durable truth.",
        "The latch is per-work-item durable truth.",
        "The consumed latch may be reset to available.",
        "The latch is reusable for every productive acceptance.",
        "The latch row may be deleted and recreated.",
        "The latch row may be recreated.",
        "The latch is scheduler-authoritative.",
        "The latch is queue-authoritative.",
        "The latch is general program truth.",
    )
    for contradiction in contradictions:
        mutation = _replace_once(text, marker, marker + "\n\n" + contradiction)
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=additive_scope_or_lifecycle"
        )


def test_c2b0_generic_structures_and_schema_inventory_are_additively_closed() -> None:
    text = _owner()
    generic_mutations = (
        _replace_once(
            text,
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger\n\nC2B also uses one generic event ledger as durable program truth.",
        ),
        _replace_once(
            text,
            "closed role-specific relation,\nnot a metadata bag",
            "closed role-specific relation,\nnot a metadata bag. C2B also uses one generic evidence metadata bag.",
        ),
        _replace_once(
            text,
            "closed\nkind-specific contract, not a generic decision metadata bag",
            "closed\nkind-specific contract, not a generic decision metadata bag. C2B also uses one generic decision JSON bag.",
        ),
        _replace_once(
            text,
            "cancel_source_evidence\n```",
            "cancel_source_evidence\narbitrary_role\n```",
        ),
        _replace_once(
            text,
            "not a generic decision metadata bag.",
            "not a generic decision metadata bag. Decision payloads are open-ended.",
        ),
    )
    for mutation in generic_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_closed_ledger_metadata_and_trigger_contract(mutation)
        assert str(rejected.value).startswith("c2b0.semantic|")
        assert str(rejected.value)

    schema_mutations = (
        (
            _replace_once(
                text,
                "development_mutation_receipts\n```",
                "development_mutation_receipts\ndevelopment_extra_0002_table\n```",
            ),
            "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
        ),
        (
            _replace_once(
                text,
                "development_publication_eligibility\ndevelopment_first_slice_latch\n```",
                "development_publication_eligibility\ndevelopment_first_slice_latch\ndevelopment_extra_0003_table\n```",
            ),
            "c2b0.schema|heading=22. Migration 0003|failure=table_inventory",
        ),
        (
            _replace_once(
                text,
                "development_program_versions\n",
                "",
            ),
            "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
        ),
        (
            _replace_once(
                text,
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.",
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.\n\nhidden_extra_trigger is also created.",
            ),
            "c2b0.schema|heading=23. Exact Schema Totals|failure=additive_trigger",
        ),
        (
            _replace_once(
                text,
                "0003: latch no-delete = 1\n",
                "",
            ),
            "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
        ),
        (
            _replace_once(
                text,
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.",
                "Migration 0003 seeds exactly the one available latch row described above; all\nother new C2B tables begin empty.\n\ndevelopment_program_heads is immutable.",
            ),
            "c2b0.schema|heading=<inventory>|failure=mutable_immutable_swap",
        ),
        (
            _replace_once(
                text,
                "idx_development_source_observation_claims_digest\n```",
                "idx_development_source_observation_claims_digest\nidx_additional_reporting\n```",
            ),
            "c2b0.schema|heading=24. Exact Explicit Indexes|failure=index_inventory",
        ),
        (
            _replace_once(
                text,
                "SQLite-managed primary-key and unique\nautoindexes are excluded from explicit-index totals.",
                "A reporting index is added. SQLite-managed primary-key and unique\nautoindexes are excluded from explicit-index totals.",
            ),
            "c2b0.schema|heading=<inventory>|failure=additive_schema_claim",
        ),
    )
    for mutation, diagnostic in schema_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_schema_contract(mutation)
        assert str(rejected.value) == diagnostic


def test_c2b0_decision_mutation_recovery_inventories_are_additively_closed() -> None:
    text = _owner()
    for added_kind in ("retry", "Accept"):
        mutation = _replace_once(
            text,
            "redeliver\ncancel\n```",
            f"redeliver\ncancel\n{added_kind}\n```",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_and_cancel_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory"
        )

    family_mutations = (
        _replace_once(
            text,
            "_record_development_progression_decision\n```",
            "_record_development_progression_decision\n_sixth_development_mutation\n```",
        ),
        _replace_once(
            text,
            "_resolve_development_progression_decision_commit_outcome\n```",
            "_resolve_development_progression_decision_commit_outcome\n_resolve_sixth_development_commit_outcome\n```",
        ),
    )
    for mutation in family_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_mutation_and_recovery_family_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.families|heading=12. Complete Target Mutation Families|failure=closed_blocks"
        )


def test_c2b0_tranche_ownership_is_unique_and_complete() -> None:
    text = _owner()
    decision_marker = "not a generic decision metadata bag."
    decision_contradictions = (
        "C2B4 owns initialize decision representation.",
        "C2B4 is the first tranche where durable decision rows are representable.",
        "C2B3 introduces a separate development_initialization_decisions table.",
    )
    for contradiction in decision_contradictions:
        mutation = _replace_once(
            text,
            decision_marker,
            decision_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_tranche_ownership(mutation)
        assert str(rejected.value) == (
            "c2b0.tranches|heading=21. Migration 0002|failure=additive_decision_ownership"
        )

    tranche_marker = "cancellation redelivery remains\nrisk-reducing and permitted."
    tranche_contradictions = (
        "C2B4 and C2B5 both own source-observation ingest.",
        "No tranche owns bound validation or review effect establishment.",
        "C2B4 and C2B5 both own the same mechanic.",
    )
    for contradiction in tranche_contradictions:
        mutation = _replace_once(
            text,
            tranche_marker,
            tranche_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_tranche_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.tranches|heading=26. Exact Target Tranche Sequence|failure=additive_ownership"
        )


def test_c2b0_repair2_full_audit_counterfactual_matrix() -> None:
    text = _owner()
    migration_marker = "Ordinary product or writer open never performs migration."

    for stale in (
        "Exact C2B schema remains wholly open.",
        "0002 is installed.",
        "0003 is installed.",
        "Application generation is currently 2.",
        "No migration number is reserved.",
        "C2B is currently implemented.",
    ):
        with pytest.raises(AssertionError):
            _assert_current_target_status(text + f"\n{stale}\n")

    for contradiction in MIGRATION_FORBIDDEN_CLAIMS[:6]:
        mutation = _replace_once(
            text,
            migration_marker,
            migration_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_application_generation_contract(mutation)

    for contradiction in MIGRATION_FORBIDDEN_CLAIMS[6:17]:
        mutation = _replace_once(
            text,
            migration_marker,
            migration_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_cumulative_migration_contract(mutation)

    for contradiction in MIGRATION_FORBIDDEN_CLAIMS[17:]:
        mutation = _replace_once(
            text,
            "The evidence classifications are exact:",
            "The evidence classifications are exact:\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_migration_failure_and_history_contract(mutation)

    invalid_info_authority = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError):
        _assert_current_target_status(invalid_info_authority)
    invalid_info_duplicate = (
        text
        + "\n```bad`info\n## 1. Status, Classification, And Layering\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError):
        _assert_owner_structure(invalid_info_duplicate)

    observation_marker = (
        "No observation or disposition directly authorizes acceptance, repair,\n"
        "replan, redelivery, publication, or program completion."
    )
    for contradiction in (
        "A source observation and ingest disposition share one authorship identity.",
        "Coordinator authors source observations.",
        "The source authors Coordinator ingest dispositions.",
        "An ingest disposition directly creates accept.",
        "An ingest disposition directly creates repair.",
        "An ingest disposition directly creates replan.",
        "An ingest disposition directly creates publication eligibility.",
    ):
        mutation = _replace_once(
            text,
            observation_marker,
            observation_marker + "\n\n" + contradiction,
        )
        with pytest.raises(AssertionError):
            _assert_observation_ingest_authority(mutation)
    with pytest.raises(AssertionError):
        _assert_observation_ingest_authority(
            _replace_once(
                text,
                "late_retained\nrecorded\n```",
                "late_retained\nrecorded\naccepted\n```",
            )
        )

    latch_marker = "The latch is not a scheduler, queue, backlog, lease, or general program truth."
    for contradiction in (
        "The latch is per-program durable truth.",
        "The latch is per-program-version durable truth.",
        "The latch is per-work-item durable truth.",
        "The consumed latch may be reset to available.",
        "The latch is reusable for every productive acceptance.",
        "The latch row may be deleted and recreated.",
        "The latch row may be recreated.",
        "The latch is scheduler-authoritative.",
        "The latch is queue-authoritative.",
    ):
        mutation = _replace_once(text, latch_marker, latch_marker + "\n\n" + contradiction)
        with pytest.raises(AssertionError):
            _assert_global_latch_scope(mutation)

    with pytest.raises(AssertionError):
        _assert_closed_ledger_metadata_and_trigger_contract(
            _replace_once(
                text,
                "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
                "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger\n\nC2B also uses one generic event ledger as durable program truth.",
            )
        )
    with pytest.raises(AssertionError):
        _assert_schema_contract(
            _replace_once(
                text,
                "idx_development_source_observation_claims_digest\n```",
                "idx_development_source_observation_claims_digest\nidx_third_explicit_index\n```",
            )
        )
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(
            _replace_once(text, "redeliver\ncancel\n```", "redeliver\ncancel\nretry\n```")
        )
    with pytest.raises(AssertionError):
        _assert_mutation_and_recovery_family_contract(
            _replace_once(
                text,
                "_record_development_progression_decision\n```",
                "_record_development_progression_decision\n_sixth_development_mutation\n```",
            )
        )
    with pytest.raises(AssertionError):
        _assert_mutation_and_recovery_family_contract(
            _replace_once(
                text,
                "_resolve_development_progression_decision_commit_outcome\n```",
                "_resolve_development_progression_decision_commit_outcome\n_resolve_sixth_development_commit_outcome\n```",
            )
        )
    with pytest.raises(AssertionError):
        _assert_decision_tranche_ownership(
            _replace_once(
                text,
                "not a generic decision metadata bag.",
                "not a generic decision metadata bag.\n\nC2B4 owns initialize decision representation.",
            )
        )
    with pytest.raises(AssertionError):
        _assert_tranche_contract(
            _replace_once(
                text,
                "cancellation redelivery remains\nrisk-reducing and permitted.",
                "cancellation redelivery remains\nrisk-reducing and permitted.\n\nC2B4 and C2B5 both own source-observation ingest.",
            )
        )


def test_c2b0_full_audit_counterfactual_matrix() -> None:
    text = _owner()

    markdown_mutations = (
        "```markdown\n" + text + "```\n",
        text + "\n  ## 1. Status, Classification, And Layering ###\n",
        text + "\n##\t1. Status, Classification, And Layering\n",
        text + "\n~~~markdown\n## 1. Status, Classification, And Layering\n```\n",
    )
    for mutation in markdown_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_owner_structure(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic.startswith("c2b0.owner|heading=")

    fenced_target = _replace_once(
        text,
        "The accepted C2B target reserves migrations",
        "```text\nThe accepted C2B target reserves migrations\n```",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_current_target_status(fenced_target)
    assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
        rejected.value
    )

    same_or_higher = _replace_once(
        text,
        "Classification: `ACCEPTED TARGET CONTRACT`.\n\nC2B0 changes",
        "Classification: `ACCEPTED TARGET CONTRACT`.\n\n# Relocated Status\n\nC2B0 changes",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_current_target_status(same_or_higher)
    assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
        rejected.value
    )

    semantic_observation_mutations = (
        _replace_once(
            text,
            "A source observation is a source-authored\nrecord and digest. An ingest disposition is a Coordinator-authored\nclassification.",
            "A source observation and ingest disposition share one authorship identity.",
        ),
        _replace_once(
            text,
            "No observation or disposition directly authorizes acceptance, repair,\nreplan, redelivery, publication, or program completion.",
            "An ingest disposition directly creates acceptance.",
        ),
    )
    for mutation in semantic_observation_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=" in str(
            rejected.value
        )

    per_program_latch = _replace_once(
        text,
        "scope: global Coordinator bootstrap",
        "scope: per program",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_global_latch_scope(per_program_latch)
    assert "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=" in str(
        rejected.value
    )

    semantic_shape_mutations = (
        _replace_once(
            text,
            "C2B rejects one mutable aggregate JSON row, fully mutable normalized history,\none generic event ledger",
            "C2B introduces one generic event ledger as durable program truth",
        ),
        _replace_once(
            text,
            "closed role-specific relation,\nnot a metadata bag",
            "generic evidence metadata bag",
        ),
        _replace_once(
            text,
            "closed\nkind-specific contract, not a generic decision metadata bag",
            "generic decision metadata bag",
        ),
    )
    for mutation in semantic_shape_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_closed_ledger_metadata_and_trigger_contract(mutation)
        assert "c2b0.semantic|heading=" in str(rejected.value)

    extra_trigger = _replace_once(
        text,
        "0003: latch one-way update guard = 1\n```",
        "0003: latch one-way update guard = 1\n0003: extra trigger = 1\n```",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_schema_contract(extra_trigger)
    assert "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic" in str(
        rejected.value
    )

    decision_ownership_mutations = (
        _replace_once(
            text,
            "C2B2 owns and lands both the base\ndecision envelope and initialize-decision row treatment",
            "C2B2 omits the base decision envelope and initialize-decision row treatment",
        ),
        _replace_once(
            text,
            "C2B4 adds only non-initialize, evidence-bearing decision contracts; it neither\nowns initialize representation nor is the first point at which a durable\ndecision row is representable.",
            "C2B4 first represents durable decisions and owns initialize representation.",
        ),
    )
    for mutation in decision_ownership_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_tranche_ownership(mutation)
        assert "c2b0.tranches|heading=21. Migration 0002|failure=" in str(rejected.value)

    generation_mutations = (
        _replace_once(
            text,
            "C2B2 advances the implemented application generation from 1 to 2",
            "C2B2 leaves the implemented application generation at 1",
        ),
        _replace_once(
            text,
            "C2B4 adds migration 0003\nwhile retaining application generation 2",
            "C2B4 advances application generation to 3 when it adds migration 0003",
        ),
    )
    for mutation in generation_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_application_generation_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=application_generation" in str(
            rejected.value
        )

    prefix_mutations = (
        _replace_once(
            text,
            "C2B4-or-later fresh installation: 0001 -> 0002 -> 0003",
            "C2B4-or-later fresh installation: apply only 0003",
        ),
        _replace_once(
            text,
            "Ordinary open never silently migrates and never accepts an older prefix.",
            "Ordinary open accepts an exact older prefix without explicit migration.",
        ),
        _replace_once(
            text,
            "one exact non-empty supported older\ncatalog prefix",
            "a non-exact or unsupported older catalog prefix",
        ),
    )
    for mutation in prefix_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_cumulative_migration_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=" in str(
            rejected.value
        )

    rollback_mutations = (
        _replace_once(
            text,
            "Historical `0001_initial` therefore remains `[1,1]`",
            "Historical `0001_initial` is rewritten to `[2,2]`",
        ),
        _replace_once(
            text,
            "Failure before commit restores the complete exact prior supported\nprefix with no partial DDL, invariant change, or history row",
            "Failure before commit leaves partial DDL or history",
        ),
    )
    for mutation in rollback_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_migration_failure_and_history_contract(mutation)
        assert "c2b0.migration|heading=20. Migration-Framework Strategy|failure=history_or_rollback" in str(
            rejected.value
        )

    status_mutations = (
        _replace_once(
            text,
            "The accepted C2B target reserves migrations",
            "No migration number is reserved here",
        ),
        text + "\nExact future state shape, schema, migrations remain wholly open.\n",
        text + "\nC2B is currently implemented.\n",
    )
    for mutation in status_mutations:
        with pytest.raises(AssertionError) as rejected:
            _assert_current_target_status(mutation)
        assert "c2b0.status|heading=1. Status, Classification, And Layering|failure=" in str(
            rejected.value
        )


def test_c2b0_adds_no_source_schema_runtime_dependency_or_public_export() -> None:
    nonimplementation = _compact(_section(_owner(), SECTION_HEADINGS[26]))
    for phrase in (
        "creates no source module, SQL, schema object, migration, database row",
        "writer method, transaction, reader, observation ingest, decision runtime",
        "authority verifier, worker, process, capsule store, Git effect",
        "direct-local adapter, ES client, service, API, IPC, scheduler, queue",
        "adds no dependency, package-root export, public DTO, public `StateStore` method, or public `WriterSession` method",
        "performs no Bridge or ES change",
        "makes no effect dispatch-eligible",
    ):
        assert phrase in nonimplementation

    assert not (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql").exists()
    assert not (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0003_development_observation_and_progression_state.sql").exists()
    assert not any("c2b" in path.name.lower() for path in (ROOT / "src").rglob("*.py"))
    assert not any("development" in path.name.lower() for path in (ROOT / "src/ge_nwp_coordinator").glob("*.py"))

    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    schema = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "schemas", ROOT / "src/ge_nwp_coordinator/sqlite_migrations")
        for path in root.rglob("*")
        if path.is_file()
    )
    for token in TABLES_0002 + TABLES_0003:
        assert token not in source
        assert token not in schema
    assert "CURRENT_APPLICATION_SCHEMA = 1" in source

    pyproject = tomllib.loads(_text("pyproject.toml"))
    assert pyproject["project"]["dependencies"] == []
    assert "scripts" not in pyproject["project"]
    package_root = _text("src/ge_nwp_coordinator/__init__.py")
    for token in ("DevelopmentProgram", "DevelopmentDecision", "DevelopmentEffectIntent"):
        assert token not in package_root
    assert not re.search(
        r"^\s*(?:from|import)\s+(?:execution_substrate|openai_bridge)(?:\.|\s|$)",
        source,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    assert "ExecutionSubstrateClient" not in source
    assert "OpenAIBridgeClient" not in source


def test_direct_negative_decision_basis_effect_and_stop_mutations_fail() -> None:
    text = _owner()

    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "redeliver\ncancel\n", "redeliver\n"))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "redeliver\ncancel\n", "redeliver\ncancel\ncancel_request\n"))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "cancel: no program-version advance", "cancel: appends a program version"))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "`cancel` is a real immutable Coordinator decision.", "`block` substitutes for cancel."))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "It creates no\nversion, attempt, candidate, command, effect, delivery, observation,", "It creates no\nversion or observation; cancel creates a semantic attempt, candidate, and WorkerCommandV1,"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "basis_decision_ref TEXT NOT NULL", "basis_decision_ref TEXT NULL"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "exact cancel decision that preassigned the cancellation effect", "exact block decision that preassigned the cancellation effect"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "exact initialize, repair, or attempt-selecting replan decision", "exact initialize, accept, redeliver, repair, or attempt-selecting replan decision"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "development_effect_intents.command_ref: non-unique foreign key", "development_effect_intents.command_ref: unique foreign key"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(_replace_once(text, "one author_candidate effect per command", "two author effects per command are permitted"))
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(text + "\nValidation creates a second semantic attempt.\n")
    with pytest.raises(AssertionError):
        _assert_basis_and_effect_contract(text + "\nReview creates a second WorkerCommandV1.\n")
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "An author\ntarget forbids the paired capsule fields.", "An author target requires capsule fields."))
    with pytest.raises(AssertionError):
        _assert_decision_and_cancel_contract(_replace_once(text, "requires the exact paired capsule-manifest ref and portable digest", "permits absent capsule bindings"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "establish author effect: block", "establish author effect: permit"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "ingest source observation: permit", "ingest source observation: block"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "record cancel decision: permit", "record cancel decision: block"))
    with pytest.raises(AssertionError):
        _assert_stop_contract(_replace_once(text, "creates no\nreceipt. Stop-version disagreement", "creates a receipt. Stop-version disagreement"))


def test_direct_negative_privacy_schema_scope_and_tranche_mutations_fail() -> None:
    text = _owner()

    with pytest.raises(AssertionError):
        _assert_privacy_contract(_replace_once(text, "objective text\nrequirements\nexclusions", "C2B may retain objective text\nrequirements\nexclusions"))
    with pytest.raises(AssertionError):
        _assert_privacy_contract(_replace_once(text, "A safe ref is not retrieval authority.", "A safe ref is retrieval authority."))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "retains immutable bytes, checksum, history, and\nmeanings", "permits a migration 0001 rewrite"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "idx_development_source_observation_claims_digest\n```", "idx_development_source_observation_claims_digest\nthird_explicit_index\n```"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "development_mutation_receipts\n```", "development_mutation_receipts\ndevelopment_extra_table\n```"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(_replace_once(text, "forty-six triggers", "forty-seven triggers"))
    with pytest.raises(AssertionError):
        _assert_schema_contract(text + "\nC2B uses one broad migration.\n")
    with pytest.raises(AssertionError):
        _assert_tranche_contract(_replace_once(text, "bound validation/review/cancellation effects", "no bound-effect owner"))

    hybrid = _compact(_section(text, SECTION_HEADINGS[3]))
    assert "one generic event ledger" in hybrid
    assert "one mutable aggregate JSON row" in hybrid
    assert "no second database, writer" in _compact(_section(text, SECTION_HEADINGS[1]))
    assert "public `StateStore` method" in _compact(_section(text, SECTION_HEADINGS[26]))
    assert "performs no Bridge or ES change" in _compact(_section(text, SECTION_HEADINGS[26]))


def test_c2b0_migration_recovery_contradictions_reject_through_both_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)

    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
    )
    for contradiction in contradictions:
        owner_mutation = _replace_once(
            owner,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(owner_mutation)
        assert str(owner_rejected.value) == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
        )

        sqlite_mutation = _replace_once(
            sqlite,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(sqlite_mutation)
        assert str(sqlite_rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
        )


def test_c2b0_unresolved_remainder_append_is_forbidden_through_both_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    contradiction = (
        "After an unresolved migration commit, the missing migration-suffix "
        "remainder is automatically appended."
    )

    owner_mutation = _replace_once(
        owner,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as owner_rejected:
        _assert_migration_failure_and_history_contract(owner_mutation)
    assert str(owner_rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=forbidden_recovery_claim"
    )

    sqlite_mutation = _replace_once(
        sqlite,
        "This migration-specific rule is distinct",
        contradiction + "\n\nThis migration-specific rule is distinct",
    )
    with pytest.raises(AssertionError) as sqlite_rejected:
        _assert_sqlite_migration_summary(sqlite_mutation)
    assert str(sqlite_rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=forbidden_migration_claim"
    )


def test_c2b0_markdown_closer_suffix_is_ascii_space_tab_only() -> None:
    for valid_suffix in ("", " ", "\t", " \t"):
        sample = f"~~~text\n## Hidden\n~~~{valid_suffix}\n## Visible\n"
        headings, visible = _markdown_scan(sample, role="c2b0.repair3")
        assert tuple(item[1] for item in headings) == ("Visible",)
        assert visible == "## Visible\n"

    for invalid_suffix in ("\u00a0", "\u2003", "not-a-closer"):
        closed_later = (
            "~~~text\n"
            f"~~~{invalid_suffix}\n"
            "C2B is currently implemented.\n"
            "## 1. Status, Classification, And Layering\n"
            "~~~\n"
        )
        assert _markdown_scan(closed_later, role="c2b0.repair3") == ((), "")

        with pytest.raises(AssertionError) as scan_rejected:
            _markdown_scan(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="c2b0.repair3",
            )
        assert str(scan_rejected.value) == (
            "c2b0.repair3|heading=<none>|failure=unbalanced_fence"
        )

        with pytest.raises(AssertionError) as block_rejected:
            _top_level_fenced_blocks(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="c2b0.repair3.blocks",
            )
        assert str(block_rejected.value) == (
            "c2b0.repair3.blocks|block=<none>|failure=unbalanced_fence"
        )


def test_c2b0_top_level_fenced_block_reader_rejects_text_bearing_closer_bypass() -> None:
    sample = "  ```text\nalpha\n```not-a-closer\nbeta\n````\n"
    blocks = _top_level_fenced_blocks(sample, role="c2b0.repair3.blocks")
    assert len(blocks) == 1
    block = blocks[0]
    assert block.marker == "`"
    assert block.opener_length == 3
    assert block.info == "text"
    assert block.opening_line == "  ```text\n"
    assert block.closing_line == "````\n"
    assert block.opening_line_number == 1
    assert block.closing_line_number == 5
    assert block.start_offset == 0
    assert block.end_offset == len(sample)
    assert block.content_start_offset == len(block.opening_line)
    assert block.content_end_offset == sample.index("````\n")
    assert block.content == "alpha\n```not-a-closer\nbeta\n"
    assert _text_blocks(sample) == (("alpha", "```not-a-closer", "beta"),)

    with pytest.raises(AssertionError) as rejected:
        _top_level_fenced_blocks(
            "```text\nalpha\n```not-a-closer\nbeta\n",
            role="c2b0.repair3.blocks",
        )
    assert str(rejected.value) == (
        "c2b0.repair3.blocks|block=<none>|failure=unbalanced_fence"
    )


def test_c2b0_top_level_fenced_block_reader_respects_outer_tilde_fences() -> None:
    sample = (
        "~~~~example\n"
        "```text\nouter-tilde-hidden\n```\n"
        "~~~~\n"
        "````example\n"
        "~~~text\nouter-backtick-hidden\n~~~\n"
        "````\n"
        "```text\nvisible-semantic-block\n```\n"
    )
    blocks = _top_level_fenced_blocks(sample, role="c2b0.repair3.blocks")
    assert tuple(block.marker for block in blocks) == ("~", "`", "`")
    assert tuple(block.opener_length for block in blocks) == (4, 4, 3)
    assert tuple(block.info for block in blocks) == ("example", "example", "text")
    assert _text_blocks(sample) == (("visible-semantic-block",),)


def test_c2b0_decision_inventory_cannot_be_truncated_by_pseudo_closer() -> None:
    text = _owner()
    for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        mutation = _inventory_pseudo_closer_mutation(
            text,
            final_item="cancel",
            hidden_addition="retry",
            closer_suffix=closer_suffix,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_decision_and_cancel_contract(mutation)
        assert str(rejected.value) == (
            "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory"
        )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[6],
        insertion=_outer_nonsemantic_inventory_examples("retry"),
    )
    _assert_decision_and_cancel_contract(outer_examples)


def test_c2b0_disposition_inventory_cannot_be_truncated_by_pseudo_closer() -> None:
    text = _owner()
    for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        mutation = _inventory_pseudo_closer_mutation(
            text,
            final_item="recorded",
            hidden_addition="accepted",
            closer_suffix=closer_suffix,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_observation_ingest_authority(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
        )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[13],
        insertion=_outer_nonsemantic_inventory_examples("accepted"),
    )
    _assert_observation_ingest_authority(outer_examples)


def test_c2b0_latch_inventory_cannot_be_truncated_by_pseudo_closer() -> None:
    text = _owner()
    for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        mutation = _inventory_pseudo_closer_mutation(
            text,
            final_item="reuse: forbidden",
            hidden_addition="reuse: allowed",
            closer_suffix=closer_suffix,
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
        )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[19],
        insertion=_outer_nonsemantic_inventory_examples("reuse: allowed"),
    )
    _assert_global_latch_scope(outer_examples)


def test_c2b0_migration_and_trigger_inventories_cannot_be_truncated() -> None:
    text = _owner()
    cases = (
        (
            "development_mutation_receipts",
            "development_extra_0002_table",
            "c2b0.schema|heading=21. Migration 0002|failure=table_inventory",
        ),
        (
            "development_publication_eligibility\ndevelopment_first_slice_latch",
            "development_extra_0003_table",
            "c2b0.schema|heading=22. Migration 0003|failure=table_inventory",
        ),
        (
            "0003: latch one-way update guard = 1",
            "0003: extra trigger = 1",
            "c2b0.schema|heading=23. Exact Schema Totals|failure=trigger_arithmetic",
        ),
        (
            "idx_development_source_observation_claims_digest",
            "idx_third_explicit_index",
            "c2b0.schema|heading=24. Exact Explicit Indexes|failure=index_inventory",
        ),
    )
    for final_item, hidden_addition, diagnostic in cases:
        for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
            mutation = _inventory_pseudo_closer_mutation(
                text,
                final_item=final_item,
                hidden_addition=hidden_addition,
                closer_suffix=closer_suffix,
            )
            with pytest.raises(AssertionError) as rejected:
                _assert_schema_contract(mutation)
            assert str(rejected.value) == diagnostic

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[21],
        insertion=_outer_nonsemantic_inventory_examples(
            "development_extra_0002_table"
        ),
    )
    outer_examples = _insert_before_owner_heading(
        outer_examples,
        next_heading=SECTION_HEADINGS[22],
        insertion=_outer_nonsemantic_inventory_examples(
            "development_extra_0003_table"
        ),
    )
    outer_examples = _insert_before_owner_heading(
        outer_examples,
        next_heading=SECTION_HEADINGS[23],
        insertion=_outer_nonsemantic_inventory_examples("0003: extra trigger = 1"),
    )
    outer_examples = _insert_before_owner_heading(
        outer_examples,
        next_heading=SECTION_HEADINGS[24],
        insertion=_outer_nonsemantic_inventory_examples("idx_third_explicit_index"),
    )
    _assert_schema_contract(outer_examples)


def test_c2b0_mutation_and_recovery_families_cannot_be_truncated() -> None:
    text = _owner()
    cases = (
        (
            "_record_development_progression_decision",
            "_sixth_development_mutation",
        ),
        (
            "_resolve_development_progression_decision_commit_outcome",
            "_resolve_sixth_development_commit_outcome",
        ),
    )
    for final_item, hidden_addition in cases:
        for closer_suffix in ("not-a-closer", "\u00a0", "\u2003"):
            mutation = _inventory_pseudo_closer_mutation(
                text,
                final_item=final_item,
                hidden_addition=hidden_addition,
                closer_suffix=closer_suffix,
            )
            with pytest.raises(AssertionError) as rejected:
                _assert_mutation_and_recovery_family_contract(mutation)
            assert str(rejected.value) == (
                "c2b0.families|heading=12. Complete Target Mutation Families|failure=closed_blocks"
            )

    outer_examples = _insert_before_owner_heading(
        text,
        next_heading=SECTION_HEADINGS[12],
        insertion=_outer_nonsemantic_inventory_examples(
            "_sixth_development_mutation\n_resolve_sixth_development_commit_outcome"
        ),
    )
    _assert_mutation_and_recovery_family_contract(outer_examples)


def test_c2b0_first_slice_latch_requires_reuse_forbidden() -> None:
    text = _owner()
    _assert_global_latch_scope(text)

    missing = _replace_once(text, "reuse: forbidden\n", "")
    with pytest.raises(AssertionError) as missing_rejected:
        _assert_global_latch_scope(missing)
    assert str(missing_rejected.value) == (
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
    )

    for widened in ("reuse: allowed", "reuse: permitted", "reuse: true", "reuse: once_more"):
        mutation = _replace_once(text, "reuse: forbidden", widened)
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value) == (
            "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
        )


def test_c2b0_repair3_full_audit_counterfactual_matrix() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)
    _assert_global_latch_scope(owner)

    recovery_contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    for contradiction in recovery_contradictions:
        owner_mutation = _replace_once(
            owner,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(owner_mutation)
        assert str(owner_rejected.value).endswith("failure=forbidden_recovery_claim")

        sqlite_mutation = _replace_once(
            sqlite,
            "This migration-specific rule is distinct",
            contradiction + "\n\nThis migration-specific rule is distinct",
        )
        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(sqlite_mutation)
        assert str(sqlite_rejected.value).endswith("failure=forbidden_migration_claim")

    for invalid_suffix in ("\u00a0", "\u2003"):
        with pytest.raises(AssertionError) as rejected:
            _markdown_scan(
                f"```text\n```{invalid_suffix}\n",
                role="c2b0.repair3.matrix",
            )
        assert str(rejected.value) == (
            "c2b0.repair3.matrix|heading=<none>|failure=unbalanced_fence"
        )

    decision_mutation = _inventory_pseudo_closer_mutation(
        owner,
        final_item="cancel",
        hidden_addition="retry",
        closer_suffix="not-a-closer",
    )
    with pytest.raises(AssertionError) as decision_rejected:
        _assert_decision_and_cancel_contract(decision_mutation)
    assert str(decision_rejected.value) == (
        "c2b0.decisions|heading=6. Exact Decision-Kind Inventory|failure=closed_inventory"
    )

    disposition_mutation = _inventory_pseudo_closer_mutation(
        owner,
        final_item="recorded",
        hidden_addition="accepted",
        closer_suffix="not-a-closer",
    )
    with pytest.raises(AssertionError) as disposition_rejected:
        _assert_observation_ingest_authority(disposition_mutation)
    assert str(disposition_rejected.value) == (
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
    )

    latch_mutation = _inventory_pseudo_closer_mutation(
        owner,
        final_item="reuse: forbidden",
        hidden_addition="reuse: allowed",
        closer_suffix="not-a-closer",
    )
    with pytest.raises(AssertionError) as latch_rejected:
        _assert_global_latch_scope(latch_mutation)
    assert str(latch_rejected.value) == (
        "c2b0.semantic|heading=19. First-Slice One-Shot Latch|failure=scope"
    )


def test_c2b0_migration_recovery_all_semantic_blocks_are_closed() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    owner_section = _section(owner, SECTION_HEADINGS[19])
    sqlite_section = _summary_section(
        sqlite,
        "C2B0 Target Migration Sequence",
        role="c2b0.repair4.sqlite",
    )
    assert _text_blocks(owner_section) == (
        ORDINARY_OPEN_RULES,
        MIGRATION_PATHS,
        MIGRATION_TRANSACTION_PATHS,
        MIGRATION_TRANSACTION_COMPONENTS,
        MIGRATION_RECOVERY_STEPS,
        MIGRATION_COMMITTED_EXACT,
        MIGRATION_DEFINITELY_NOT_COMMITTED,
        MIGRATION_UNRESOLVED,
    )
    assert _text_blocks(sqlite_section) == (
        MIGRATION_PATHS,
        MIGRATION_TRANSACTION_PATHS,
        MIGRATION_TRANSACTION_COMPONENTS,
        MIGRATION_RECOVERY_STEPS,
        MIGRATION_COMMITTED_EXACT,
        MIGRATION_DEFINITELY_NOT_COMMITTED,
        MIGRATION_UNRESOLVED,
        SQLITE_MIGRATION_DEFINITIONS,
        SQLITE_MIGRATION_SCHEMA_TOTALS,
    )

    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    addition = "```text\nanother recovery classification\n```\n\n"
    with pytest.raises(AssertionError) as owner_rejected:
        _assert_migration_failure_and_history_contract(
            _replace_once(owner, marker, addition + marker)
        )
    assert str(owner_rejected.value) == (
        "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
    )

    with pytest.raises(AssertionError) as sqlite_rejected:
        _assert_sqlite_migration_summary(
            _replace_once(sqlite, marker, addition + marker)
        )
    assert str(sqlite_rejected.value) == (
        "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
    )

    outer = _outer_nonsemantic_inventory_examples("another recovery classification")
    _assert_migration_failure_and_history_contract(
        _replace_once(owner, marker, outer + "\n" + marker)
    )
    _assert_sqlite_migration_summary(
        _replace_once(sqlite, marker, outer + "\n" + marker)
    )


def test_c2b0_migration_recovery_nine_prohibitions_reject_through_both_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    for contradiction in contradictions:
        block = f"```text\n{contradiction}\n```\n\n"
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(
                _replace_once(owner, marker, block + marker)
            )
        owner_diagnostic = str(owner_rejected.value)
        assert owner_diagnostic == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
        )
        assert contradiction not in owner_diagnostic

        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(
                _replace_once(sqlite, marker, block + marker)
            )
        sqlite_diagnostic = str(sqlite_rejected.value)
        assert sqlite_diagnostic == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
        )
        assert contradiction not in sqlite_diagnostic


def test_c2b0_disposition_inventory_is_closed_across_all_semantic_blocks() -> None:
    owner = _owner()
    section = _section(owner, SECTION_HEADINGS[12])
    assert _text_blocks(section) == (OBSERVATION_INGEST_STEPS, DISPOSITIONS)

    appended = _replace_once(owner, "recorded\n```", "recorded\naccepted\n```")
    with pytest.raises(AssertionError) as appended_rejected:
        _assert_observation_ingest_authority(appended)
    assert str(appended_rejected.value).endswith("failure=disposition_inventory")

    duplicate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\n" + "\n".join(DISPOSITIONS) + "\n```\n",
    )
    with pytest.raises(AssertionError) as duplicate_rejected:
        _assert_observation_ingest_authority(duplicate)
    assert str(duplicate_rejected.value).endswith("failure=disposition_inventory")

    alias = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\nrecorded_alias\n```\n",
    )
    with pytest.raises(AssertionError) as alias_rejected:
        _assert_observation_ingest_authority(alias)
    assert str(alias_rejected.value).endswith("failure=disposition_inventory")


def test_c2b0_separate_block_accepted_disposition_is_rejected() -> None:
    mutation = _insert_before_owner_heading(
        _owner(),
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\naccepted\n```\n",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_observation_ingest_authority(mutation)
    assert str(rejected.value) == (
        "c2b0.semantic|heading=13. Source Invocation, Observation, And Ingest|failure=disposition_inventory"
    )


def test_c2b0_latch_contract_is_unique_and_complete() -> None:
    owner = _owner()
    _assert_global_latch_scope(owner)
    latch = _section(owner, SECTION_HEADINGS[18])
    assert _text_blocks(latch) == (LATCH_CONTRACT,)

    missing = _replace_once(owner, "reuse: forbidden\n", "")
    with pytest.raises(AssertionError) as missing_rejected:
        _assert_global_latch_scope(missing)
    assert str(missing_rejected.value).endswith("failure=scope")

    duplicate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="```text\n" + "\n".join(LATCH_CONTRACT) + "\n```\n",
    )
    with pytest.raises(AssertionError) as duplicate_rejected:
        _assert_global_latch_scope(duplicate)
    assert str(duplicate_rejected.value).endswith("failure=contract_inventory")

    second_latch = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="latch_ref: second_productive_acceptance\n",
    )
    with pytest.raises(AssertionError) as second_latch_rejected:
        _assert_global_latch_scope(second_latch)
    assert str(second_latch_rejected.value).endswith(
        "failure=additive_scope_or_lifecycle"
    )


def test_c2b0_additional_latch_reuse_declarations_are_rejected() -> None:
    owner = _owner()
    for declaration in (
        "reuse: allowed",
        "reuse: permitted",
        "reuse: true",
        "reuse: once_more",
    ):
        mutation = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[19],
            insertion=declaration + "\n",
        )
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        assert str(rejected.value).endswith("failure=additive_scope_or_lifecycle")

    separate_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="```text\nreuse: allowed\n```\n",
    )
    with pytest.raises(AssertionError) as block_rejected:
        _assert_global_latch_scope(separate_block)
    assert str(block_rejected.value).endswith("failure=contract_inventory")


def test_c2b0_visible_additional_trigger_arithmetic_is_rejected() -> None:
    owner = _owner()
    _assert_schema_contract(owner)

    visible = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="0003: extra trigger = 1\n",
    )
    with pytest.raises(AssertionError) as visible_rejected:
        _assert_schema_contract(visible)
    assert str(visible_rejected.value).endswith("failure=additive_trigger_arithmetic")

    totals_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="```text\n0003: extra trigger = 1\n```\n",
    )
    with pytest.raises(AssertionError) as totals_block_rejected:
        _assert_schema_contract(totals_block)
    assert str(totals_block_rejected.value).endswith("failure=closed_totals_blocks")

    migration_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\n0003: extra trigger = 1\n```\n",
    )
    with pytest.raises(AssertionError) as migration_block_rejected:
        _assert_schema_contract(migration_block)
    assert str(migration_block_rejected.value).endswith(
        "failure=additive_trigger_arithmetic"
    )


def test_c2b0_repair4_full_audit_counterfactual_matrix() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)
    _assert_observation_ingest_authority(owner)
    _assert_global_latch_scope(owner)
    _assert_schema_contract(owner)

    marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    for contradiction in contradictions:
        block = f"```text\n{contradiction}\n```\n\n"
        with pytest.raises(AssertionError) as owner_rejected:
            _assert_migration_failure_and_history_contract(
                _replace_once(owner, marker, block + marker)
            )
        assert str(owner_rejected.value) == (
            "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
        )

        with pytest.raises(AssertionError) as sqlite_rejected:
            _assert_sqlite_migration_summary(
                _replace_once(sqlite, marker, block + marker)
            )
        assert str(sqlite_rejected.value) == (
            "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
        )

    disposition = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="```text\naccepted\n```\n",
    )
    with pytest.raises(AssertionError) as disposition_rejected:
        _assert_observation_ingest_authority(disposition)
    assert str(disposition_rejected.value).endswith("failure=disposition_inventory")

    for declaration in (
        "reuse: allowed",
        "reuse: permitted",
        "reuse: true",
        "reuse: once_more",
    ):
        latch = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[19],
            insertion=declaration + "\n",
        )
        with pytest.raises(AssertionError) as latch_rejected:
            _assert_global_latch_scope(latch)
        assert str(latch_rejected.value).endswith("failure=additive_scope_or_lifecycle")

    latch_block = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="```text\nreuse: allowed\n```\n",
    )
    with pytest.raises(AssertionError) as latch_block_rejected:
        _assert_global_latch_scope(latch_block)
    assert str(latch_block_rejected.value).endswith("failure=contract_inventory")

    trigger = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="0003: extra trigger = 1\n",
    )
    with pytest.raises(AssertionError) as trigger_rejected:
        _assert_schema_contract(trigger)
    assert str(trigger_rejected.value).endswith("failure=additive_trigger_arithmetic")

    outer_owner = _replace_once(
        owner,
        marker,
        _outer_nonsemantic_inventory_examples(
            "History and live-schema disagreement is committed_exact."
        )
        + "\n"
        + marker,
    )
    outer_sqlite = _replace_once(
        sqlite,
        marker,
        _outer_nonsemantic_inventory_examples(
            "History and live-schema disagreement is committed_exact."
        )
        + "\n"
        + marker,
    )
    _assert_migration_failure_and_history_contract(outer_owner)
    _assert_sqlite_migration_summary(outer_sqlite)

    for invalid_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        with pytest.raises(AssertionError) as closer_rejected:
            _markdown_scan(
                f"```text\n```{invalid_suffix}\n",
                role="c2b0.repair4.matrix",
            )
        assert str(closer_rejected.value) == (
            "c2b0.repair4.matrix|heading=<none>|failure=unbalanced_fence"
        )


def test_c2b0_semantic_text_blocks_are_marker_neutral() -> None:
    expected = (("alpha", "beta"),)
    assert _text_blocks("```text\nalpha\nbeta\n```\n") == expected
    assert _text_blocks("~~~text\nalpha\nbeta\n~~~\n") == expected
    assert _text_blocks("~~~ text \t\nalpha\nbeta\n~~~\n") == expected
    assert _text_blocks(
        _outer_nonsemantic_inventory_examples("alpha\nbeta")
    ) == ()

    for unclosed in (
        "```text\nalpha\n",
        "~~~text\nalpha\n",
    ):
        with pytest.raises(AssertionError) as rejected:
            _text_blocks(unclosed)
        assert str(rejected.value) == (
            "c2b0.text_blocks|block=<none>|failure=unbalanced_fence"
        )


def test_c2b0_migration_recovery_nine_prohibitions_reject_under_both_delimiters_and_validators() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    insertion_marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )

    rejection_count = 0
    for delimiter in ("```", "~~~"):
        for contradiction in contradictions:
            semantic_block = f"{delimiter}text\n{contradiction}\n{delimiter}\n\n"
            owner_mutation = _replace_once(
                owner,
                insertion_marker,
                semantic_block + insertion_marker,
            )
            with pytest.raises(AssertionError) as owner_rejected:
                _assert_migration_failure_and_history_contract(owner_mutation)
            owner_diagnostic = str(owner_rejected.value)
            assert owner_diagnostic == (
                "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
            )
            assert contradiction not in owner_diagnostic
            rejection_count += 1

            sqlite_mutation = _replace_once(
                sqlite,
                insertion_marker,
                semantic_block + insertion_marker,
            )
            with pytest.raises(AssertionError) as sqlite_rejected:
                _assert_sqlite_migration_summary(sqlite_mutation)
            sqlite_diagnostic = str(sqlite_rejected.value)
            assert sqlite_diagnostic == (
                "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
            )
            assert contradiction not in sqlite_diagnostic
            rejection_count += 1

    assert rejection_count == 36


def test_c2b0_tilde_disposition_inventory_is_closed() -> None:
    owner = _owner()
    _assert_observation_ingest_authority(owner)

    primary = _replace_once(owner, "recorded\n```", "recorded\naccepted\n```")
    with pytest.raises(AssertionError) as primary_rejected:
        _assert_observation_ingest_authority(primary)
    assert str(primary_rejected.value).endswith("failure=disposition_inventory")

    for delimiter in ("```", "~~~"):
        separate = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=f"{delimiter}text\naccepted\n{delimiter}\n",
        )
        with pytest.raises(AssertionError) as separate_rejected:
            _assert_observation_ingest_authority(separate)
        assert str(separate_rejected.value).endswith("failure=disposition_inventory")

        duplicate = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=delimiter + "text\n" + "\n".join(DISPOSITIONS) + "\n" + delimiter + "\n",
        )
        with pytest.raises(AssertionError) as duplicate_rejected:
            _assert_observation_ingest_authority(duplicate)
        assert str(duplicate_rejected.value).endswith("failure=disposition_inventory")

    case_variant = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion="~~~text\nRecorded\n~~~\n",
    )
    with pytest.raises(AssertionError) as case_rejected:
        _assert_observation_ingest_authority(case_variant)
    assert str(case_rejected.value).endswith("failure=disposition_inventory")

    outer = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[13],
        insertion=_outer_nonsemantic_inventory_examples("accepted"),
    )
    _assert_observation_ingest_authority(outer)


def test_c2b0_latch_governing_and_seed_roles_are_unique_and_bound() -> None:
    owner = _owner()
    _assert_global_latch_scope(owner)

    wrong_seed_identity = _replace_once(
        owner,
        "latch_ref: direct_local_first_productive_acceptance\nstate: available",
        "latch_ref: wrong_first_productive_acceptance\nstate: available",
    )
    wrong_seed_state = _replace_once(
        owner,
        "state: available\nversion: 0\nconsumed bindings: null",
        "state: consumed\nversion: 0\nconsumed bindings: null",
    )
    wrong_seed_version = _replace_once(
        owner,
        "state: available\nversion: 0\nconsumed bindings: null",
        "state: available\nversion: 1\nconsumed bindings: null",
    )
    non_null_seed_binding = _replace_once(
        owner,
        "state: available\nversion: 0\nconsumed bindings: null",
        "state: available\nversion: 0\nconsumed bindings: decision_ref",
    )
    second_seed = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\n" + "\n".join(LATCH_SEED_CONTRACT) + "\n```\n",
    )
    second_governing = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="~~~text\n" + "\n".join(LATCH_CONTRACT) + "\n~~~\n",
    )
    missing_reuse = _replace_once(owner, "reuse: forbidden\n", "")

    for mutation in (
        wrong_seed_identity,
        wrong_seed_state,
        wrong_seed_version,
        non_null_seed_binding,
        second_seed,
        second_governing,
        missing_reuse,
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic
        assert diagnostic.startswith("c2b0.semantic|heading=")
        assert "failure=" in diagnostic


def test_c2b0_out_of_section_latch_reuse_is_rejected() -> None:
    owner = _owner()
    section_19_tilde = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[19],
        insertion="~~~text\nreuse: allowed\n~~~\n",
    )
    section_22_visible = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="reuse: allowed\n",
    )
    section_22_tilde = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="~~~text\nreuse: allowed\n~~~\n",
    )
    section_22_backtick = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\nreuse: allowed\n```\n",
    )

    for mutation in (
        section_19_tilde,
        section_22_visible,
        section_22_tilde,
        section_22_backtick,
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_global_latch_scope(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic
        assert diagnostic.startswith("c2b0.semantic|heading=")
        assert "failure=" in diagnostic

    outer = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion=_outer_nonsemantic_inventory_examples("reuse: allowed"),
    )
    _assert_global_latch_scope(outer)


def test_c2b0_trigger_totals_are_role_unique() -> None:
    owner = _owner()
    _assert_schema_contract(owner)

    conflicting_schema_tip = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="schema tip 0003: 39 user tables, 2 explicit application indexes, 63 triggers\n",
    )
    conflicting_aggregate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion="C2B adds exactly twenty-eight tables, forty-seven triggers, and two explicit indexes.\n",
    )
    duplicate_schema_tip = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion=TRIGGER_SCHEMA_ROLE_CLAIMS[2] + "\n",
    )
    duplicate_aggregate = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion=TRIGGER_AGGREGATE_ROLE_CLAIMS[0] + "\n",
    )
    extra_backtick = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="```text\n0003: extra trigger = 1\n```\n",
    )
    extra_tilde = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="~~~text\n0003: extra trigger = 1\n~~~\n",
    )

    for mutation in (
        conflicting_schema_tip,
        conflicting_aggregate,
        duplicate_schema_tip,
        duplicate_aggregate,
        extra_backtick,
        extra_tilde,
    ):
        with pytest.raises(AssertionError) as rejected:
            _assert_schema_contract(mutation)
        diagnostic = str(rejected.value)
        assert diagnostic
        assert diagnostic.startswith("c2b0.schema|heading=")
        assert "failure=" in diagnostic


def test_c2b0_tilde_trigger_arithmetic_is_closed() -> None:
    owner = _owner()
    mutation = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[22],
        insertion="~~~text\n0003: extra trigger = 1\n~~~\n",
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_schema_contract(mutation)
    assert str(rejected.value).endswith("failure=additive_trigger_arithmetic")

    outer = _insert_before_owner_heading(
        owner,
        next_heading=SECTION_HEADINGS[23],
        insertion=_outer_nonsemantic_inventory_examples("0003: extra trigger = 1"),
    )
    _assert_schema_contract(outer)


def test_c2b0_repair5_full_audit_counterfactual_matrix() -> None:
    owner = _owner()
    sqlite = _text(".docs/sqlite-bootstrap-and-migrations.md")
    _assert_migration_failure_and_history_contract(owner)
    _assert_sqlite_migration_summary(sqlite)
    _assert_observation_ingest_authority(owner)
    _assert_global_latch_scope(owner)
    _assert_schema_contract(owner)

    insertion_marker = "An `unresolved` result forbids automatic rerun and automatic append of a"
    contradictions = (
        "History and live-schema disagreement is committed_exact.",
        "A partial intended suffix is committed_exact.",
        "An unknown or divergent migration-history row is committed_exact.",
        "An unexpected live-schema object is committed_exact.",
        "Incomplete exact history or live-schema verification is committed_exact.",
        "Matching migration history alone is committed_exact even when the live schema differs.",
        "Matching live schema alone is committed_exact even when migration history differs.",
        "After an unresolved migration commit, the suffix is automatically rerun.",
        "After an unresolved migration commit, the missing migration-suffix remainder is automatically appended.",
    )
    migration_rejections = 0
    for delimiter in ("```", "~~~"):
        for contradiction in contradictions:
            block = f"{delimiter}text\n{contradiction}\n{delimiter}\n\n"
            owner_mutation = _replace_once(owner, insertion_marker, block + insertion_marker)
            with pytest.raises(AssertionError) as owner_rejected:
                _assert_migration_failure_and_history_contract(owner_mutation)
            assert str(owner_rejected.value) == (
                "c2b0.migration|heading=20. Migration-Framework Strategy|failure=commit_uncertainty_mapping"
            )
            assert contradiction not in str(owner_rejected.value)
            migration_rejections += 1

            sqlite_mutation = _replace_once(sqlite, insertion_marker, block + insertion_marker)
            with pytest.raises(AssertionError) as sqlite_rejected:
                _assert_sqlite_migration_summary(sqlite_mutation)
            assert str(sqlite_rejected.value) == (
                "c2b0.sqlite_migration|heading=C2B0 Target Migration Sequence|failure=transaction_or_recovery_mapping"
            )
            assert contradiction not in str(sqlite_rejected.value)
            migration_rejections += 1
    assert migration_rejections == 36

    for delimiter in ("```", "~~~"):
        disposition = _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=f"{delimiter}text\naccepted\n{delimiter}\n",
        )
        with pytest.raises(AssertionError) as disposition_rejected:
            _assert_observation_ingest_authority(disposition)
        assert str(disposition_rejected.value).endswith("failure=disposition_inventory")

    latch_mutations = (
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[19],
            insertion="~~~text\nreuse: allowed\n~~~\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion="reuse: allowed\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion="~~~text\nreuse: allowed\n~~~\n",
        ),
        _replace_once(
            owner,
            "latch_ref: direct_local_first_productive_acceptance\nstate: available",
            "latch_ref: wrong_first_productive_acceptance\nstate: available",
        ),
        _replace_once(
            owner,
            "state: available\nversion: 0\nconsumed bindings: null",
            "state: consumed\nversion: 0\nconsumed bindings: null",
        ),
        _replace_once(
            owner,
            "state: available\nversion: 0\nconsumed bindings: null",
            "state: available\nversion: 1\nconsumed bindings: null",
        ),
        _replace_once(
            owner,
            "state: available\nversion: 0\nconsumed bindings: null",
            "state: available\nversion: 0\nconsumed bindings: decision_ref",
        ),
    )
    for latch_mutation in latch_mutations:
        with pytest.raises(AssertionError) as latch_rejected:
            _assert_global_latch_scope(latch_mutation)
        assert str(latch_rejected.value).startswith("c2b0.semantic|heading=")

    trigger_mutations = (
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion="~~~text\n0003: extra trigger = 1\n~~~\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion="schema tip 0003: 39 user tables, 2 explicit application indexes, 63 triggers\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion="C2B adds exactly twenty-eight tables, forty-seven triggers, and two explicit indexes.\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion=TRIGGER_SCHEMA_ROLE_CLAIMS[2] + "\n",
        ),
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion=TRIGGER_AGGREGATE_ROLE_CLAIMS[0] + "\n",
        ),
    )
    for trigger_mutation in trigger_mutations:
        with pytest.raises(AssertionError) as trigger_rejected:
            _assert_schema_contract(trigger_mutation)
        assert str(trigger_rejected.value).startswith("c2b0.schema|heading=")

    outer_owner = _replace_once(
        owner,
        insertion_marker,
        _outer_nonsemantic_inventory_examples(contradictions[0]) + "\n" + insertion_marker,
    )
    outer_sqlite = _replace_once(
        sqlite,
        insertion_marker,
        _outer_nonsemantic_inventory_examples(contradictions[0]) + "\n" + insertion_marker,
    )
    _assert_migration_failure_and_history_contract(outer_owner)
    _assert_sqlite_migration_summary(outer_sqlite)
    _assert_observation_ingest_authority(
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[13],
            insertion=_outer_nonsemantic_inventory_examples("accepted"),
        )
    )
    _assert_global_latch_scope(
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[22],
            insertion=_outer_nonsemantic_inventory_examples("reuse: allowed"),
        )
    )
    _assert_schema_contract(
        _insert_before_owner_heading(
            owner,
            next_heading=SECTION_HEADINGS[23],
            insertion=_outer_nonsemantic_inventory_examples("0003: extra trigger = 1"),
        )
    )

    for invalid_suffix in ("not-a-closer", "\u00a0", "\u2003"):
        with pytest.raises(AssertionError) as closer_rejected:
            _markdown_scan(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="c2b0.repair5.matrix",
            )
        assert str(closer_rejected.value) == (
            "c2b0.repair5.matrix|heading=<none>|failure=unbalanced_fence"
        )

    for unclosed in ("```text\n", "~~~text\n"):
        with pytest.raises(AssertionError) as unclosed_rejected:
            _text_blocks(unclosed)
        assert str(unclosed_rejected.value) == (
            "c2b0.text_blocks|block=<none>|failure=unbalanced_fence"
        )
