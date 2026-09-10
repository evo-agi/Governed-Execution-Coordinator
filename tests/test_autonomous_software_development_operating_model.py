from dataclasses import dataclass
from pathlib import Path
import re
import tomllib

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ".docs/autonomous-software-development-operating-model.md"
CLASSIFICATIONS = (
    "CURRENT IMPLEMENTED CONTRACT",
    "CURRENT COMPATIBILITY EDGE",
    "ACCEPTED STRATEGIC TARGET",
    "FUTURE IMPLEMENTATION DETAIL",
    "DEFERRED OR BLOCKED EFFECT",
    "PROCESS-ONLY GOVERNANCE",
)
CLASSIFICATION_PATTERN = re.compile(
    "|".join(re.escape(label) for label in CLASSIFICATIONS)
)
C1_HEADINGS = (
    ("C1-AOM-001", "Status And Classification Ledger"),
    ("C1-AOM-002", "Accepted Staged Topology"),
    ("C1-AOM-003", "Worker Source, Release, Process, And Credential Boundary"),
    ("C1-AOM-004", "First Autonomous Slice And Effect Ceiling"),
    ("C1-AOM-005", "Candidate Capsule And Custody"),
    ("C1-AOM-006", "Standing Authority, Subordinate Authorization, Model, And User Role"),
    ("C1-AOM-007", "Review, Acceptance, Repair, And Publication Separation"),
    ("C1-AOM-008", "Direct-Local Bootstrap/Proof Contract"),
    ("C1-AOM-009", "First Recorded ES Scenario"),
    ("C1-AOM-010", "Parallel ES Lanes And Migration Gate"),
    ("C1-AOM-011", "Compatibility, Deferred Components, And Cross-Repository Drift"),
    ("C1-AOM-012", "Audit-Isolation Process Governance"),
    ("C1-AOM-013", "Future Details And Non-Implementation Contract"),
)
EXPECTED_CLASSIFICATIONS = {
    "C1-AOM-001": CLASSIFICATIONS,
    "C1-AOM-002": ("ACCEPTED STRATEGIC TARGET",),
    "C1-AOM-003": ("ACCEPTED STRATEGIC TARGET", "FUTURE IMPLEMENTATION DETAIL"),
    "C1-AOM-004": ("ACCEPTED STRATEGIC TARGET", "DEFERRED OR BLOCKED EFFECT"),
    "C1-AOM-005": ("ACCEPTED STRATEGIC TARGET", "FUTURE IMPLEMENTATION DETAIL"),
    "C1-AOM-006": ("CURRENT IMPLEMENTED CONTRACT", "ACCEPTED STRATEGIC TARGET"),
    "C1-AOM-007": ("ACCEPTED STRATEGIC TARGET",),
    "C1-AOM-008": ("ACCEPTED STRATEGIC TARGET", "DEFERRED OR BLOCKED EFFECT"),
    "C1-AOM-009": ("ACCEPTED STRATEGIC TARGET", "DEFERRED OR BLOCKED EFFECT"),
    "C1-AOM-010": ("CURRENT COMPATIBILITY EDGE", "ACCEPTED STRATEGIC TARGET"),
    "C1-AOM-011": ("CURRENT COMPATIBILITY EDGE", "DEFERRED OR BLOCKED EFFECT"),
    "C1-AOM-012": ("PROCESS-ONLY GOVERNANCE",),
    "C1-AOM-013": ("FUTURE IMPLEMENTATION DETAIL", "DEFERRED OR BLOCKED EFFECT"),
}
EXPECTED_CLASSIFICATION_FIELDS = {
    "C1-AOM-001": tuple((label,) for label in CLASSIFICATIONS),
    "C1-AOM-002": (("ACCEPTED STRATEGIC TARGET",),),
    "C1-AOM-003": (
        ("ACCEPTED STRATEGIC TARGET",),
        ("FUTURE IMPLEMENTATION DETAIL",),
    ),
    "C1-AOM-004": (
        ("ACCEPTED STRATEGIC TARGET",),
        ("DEFERRED OR BLOCKED EFFECT",),
    ),
    "C1-AOM-005": (
        ("ACCEPTED STRATEGIC TARGET",),
        ("FUTURE IMPLEMENTATION DETAIL",),
    ),
    "C1-AOM-006": (
        ("CURRENT IMPLEMENTED CONTRACT",),
        ("ACCEPTED STRATEGIC TARGET",),
    ),
    "C1-AOM-007": (("ACCEPTED STRATEGIC TARGET",),),
    "C1-AOM-008": (
        ("ACCEPTED STRATEGIC TARGET", "DEFERRED OR BLOCKED EFFECT"),
    ),
    "C1-AOM-009": (
        ("ACCEPTED STRATEGIC TARGET",),
        ("DEFERRED OR BLOCKED EFFECT",),
    ),
    "C1-AOM-010": (
        ("CURRENT COMPATIBILITY EDGE", "ACCEPTED STRATEGIC TARGET"),
    ),
    "C1-AOM-011": (
        ("CURRENT COMPATIBILITY EDGE",),
        ("DEFERRED OR BLOCKED EFFECT",),
    ),
    "C1-AOM-012": (("PROCESS-ONLY GOVERNANCE",),),
    "C1-AOM-013": (
        ("FUTURE IMPLEMENTATION DETAIL",),
        ("DEFERRED OR BLOCKED EFFECT",),
    ),
}
SCENARIO_PATHS = (
    "Execution Substrate/PLANS.md",
    "Execution Substrate/.docs/system_overview/hybrid_integration_architecture_adr.md",
    "Execution Substrate/docs_contract_test.go",
)
SCENARIO_EFFECT_PARAGRAPH = (
    "Its purpose is to classify direct-local worker execution as a bounded "
    "bootstrap/proof edge, record mandatory migration stop conditions, preserve ES "
    "reliable-submit dependencies, preserve the current ES P0, and create no ES "
    "runtime change. Its maximum effect is one local feature-branch Git commit; push, "
    "remote-ref mutation, PR creation, merge, deployment, and a production-autonomy "
    "claim are excluded."
)
AUDIT_NON_RUNTIME_PARAGRAPH = (
    "This clause is `NOT PRODUCT RUNTIME ARCHITECTURE`, `NOT COORDINATOR DURABLE "
    "STATE`, and `NOT WORKER BEHAVIOR`."
)
AUDIT_CONTROLS = (
    "clear ambient Git variables;",
    "initialize an explicit audit-owned `.git`;",
    "verify the physical Git top-level is beneath the audit root;",
    "never use a copied pathname as isolation proof; and",
    "recheck the real repository HEAD, index, local configuration, and status after each mutation-capable probe group.",
)
DIRECT_LOCAL_CONDITIONS = (
    "The direct-local route implements the same versioned worker command, observation, fence, and capsule contracts intended for ES routing.",
    "It is named explicitly as bootstrap/proof.",
    "It initially permits one repository and one active invocation.",
    "It has no connector or Bridge trigger.",
    "It cannot push, create a PR, merge, or deploy.",
    "It cannot write Coordinator SQLite directly.",
    "It cannot create semantic attempts, accept candidates, or decide repairs.",
    "Expansion stops after one accepted vertical slice pending an ES-migration review.",
    "The later ES adapter must pass the same conformance contract.",
    "After ES routing is accepted, direct-local becomes disabled by default and survives only under a distinct proof/recovery policy.",
)
SCENARIO_PATHS_FIELD = (
    "The first recorded worker scenario is eventually allowed to change exactly"
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


def _markdown_atx_headings(
    text: str,
    *,
    role: str = "operating_model.markdown",
) -> tuple[tuple[int, str, int, int], ...]:
    """Parse bounded ATX headings outside backtick and tilde fenced blocks."""
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
    role: str,
    allow_eof: bool = False,
) -> str:
    headings = _markdown_atx_headings(text, role=role)
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


@dataclass(frozen=True)
class _MarkdownBlock:
    kind: str
    text: str = ""
    name: str | None = None
    value: str | None = None
    items: tuple[str, ...] = ()
    ordinals: tuple[int, ...] = ()
    marker: str | None = None
    info: str | None = None
    level: int | None = None


@dataclass(frozen=True)
class _ScenarioEffectSurface:
    maximum_effect: str
    excluded_effects: tuple[str, ...]


def _structured_markdown_blocks(text: str) -> tuple[_MarkdownBlock, ...]:
    """Parse only the finite block surfaces used by the C1 contract tests."""
    blocks: list[_MarkdownBlock] = []
    pending_kind: str | None = None
    pending_name: str | None = None
    pending_lines: list[str] = []
    pending_items: list[list[str]] = []
    pending_ordinals: list[int] = []
    fence: tuple[str, int, str, list[str]] | None = None

    def flush() -> None:
        nonlocal pending_kind, pending_name
        if pending_kind == "paragraph":
            blocks.append(_MarkdownBlock(kind="paragraph", text=_compact("\n".join(pending_lines))))
        elif pending_kind == "field":
            assert pending_name is not None
            blocks.append(
                _MarkdownBlock(
                    kind="field",
                    name=pending_name,
                    value=_compact("\n".join(pending_lines)),
                )
            )
        elif pending_kind in {"ordered_list", "unordered_list"}:
            assert pending_items
            blocks.append(
                _MarkdownBlock(
                    kind=pending_kind,
                    items=tuple(_compact("\n".join(item)) for item in pending_items),
                    ordinals=tuple(pending_ordinals),
                )
            )
        pending_kind = None
        pending_name = None
        pending_lines.clear()
        pending_items.clear()
        pending_ordinals.clear()

    for content in text.splitlines():
        stripped = content.lstrip(" ")
        indent = len(content) - len(stripped)
        fence_marker = _markdown_fence_candidate(content)

        if fence is not None:
            marker, run_length, info, lines = fence
            if (
                fence_marker is not None
                and fence_marker[0] == marker
                and fence_marker[1] >= run_length
                and _markdown_closer_suffix_is_ascii_space_tab(fence_marker[2])
            ):
                blocks.append(
                    _MarkdownBlock(
                        kind="fenced_code",
                        text="\n".join(lines),
                        marker=marker,
                        info=info,
                    )
                )
                fence = None
            else:
                lines.append(content)
            continue

        if fence_marker is not None:
            flush()
            marker, run_length, remainder = fence_marker
            fence = (marker, run_length, remainder.strip(), [])
            continue

        if not stripped:
            flush()
            continue

        heading = None
        if indent <= 3:
            heading = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
        if heading is not None:
            flush()
            title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2)).strip()
            assert title
            blocks.append(
                _MarkdownBlock(
                    kind="heading",
                    text=title,
                    level=len(heading.group(1)),
                )
            )
            continue

        field = None
        ordered = None
        unordered = None
        if indent <= 3:
            field = re.fullmatch(
                r"[ ]{0,3}([A-Za-z][A-Za-z0-9 /_-]*):[ \t]*(.*)",
                content,
            )
            ordered = re.fullmatch(r"[ ]{0,3}(\d+)\.[ \t]+(.*)", content)
            unordered = re.fullmatch(r"[ ]{0,3}[-+*][ \t]+(.*)", content)

        if field is not None:
            flush()
            pending_kind = "field"
            pending_name = field.group(1)
            pending_lines.append(field.group(2))
            continue

        if ordered is not None:
            if pending_kind != "ordered_list":
                flush()
                pending_kind = "ordered_list"
            pending_items.append([ordered.group(2)])
            pending_ordinals.append(int(ordered.group(1)))
            continue

        if unordered is not None:
            if pending_kind != "unordered_list":
                flush()
                pending_kind = "unordered_list"
            pending_items.append([unordered.group(1)])
            continue

        if pending_kind in {"ordered_list", "unordered_list"}:
            pending_items[-1].append(content)
        else:
            if pending_kind is None:
                pending_kind = "paragraph"
            pending_lines.append(content)

    _require(
        fence is None,
        "operating_model.markdown_blocks|block=<none>|failure=unbalanced_fence",
    )
    flush()
    return tuple(blocks)


def _c1_clause_sections(text: str) -> dict[str, str]:
    headings = _markdown_atx_headings(text)
    expected_titles = {
        identifier: f"{identifier} — {title}" for identifier, title in C1_HEADINGS
    }
    identified: list[tuple[str, tuple[int, str, int, int]]] = []
    for heading in headings:
        identifiers = re.findall(r"C1-AOM-\d{3}", heading[1])
        for identifier in identifiers:
            assert identifier in expected_titles
            assert heading[0] == 2
            assert heading[1] == expected_titles[identifier]
            identified.append((identifier, heading))
    assert [identifier for identifier, _ in identified] == [
        identifier for identifier, _ in C1_HEADINGS
    ]

    sections: dict[str, str] = {}
    for identifier, heading in identified:
        heading_index = headings.index(heading)
        end = len(text)
        for following in headings[heading_index + 1 :]:
            if following[0] <= heading[0]:
                end = following[2]
                break
        sections[identifier] = text[heading[3] : end]
    return sections


def _clause(
    identifier: str,
    next_identifier: str | None = None,
    *,
    text: str | None = None,
) -> str:
    del next_identifier
    return _c1_clause_sections(_doc() if text is None else text)[identifier]


def _code_blocks(text: str) -> list[str]:
    return [
        block.text
        for block in _structured_markdown_blocks(text)
        if block.kind == "fenced_code" and block.info == "text"
    ]


def _numbered_items(text: str) -> list[str]:
    return [
        item
        for block in _structured_markdown_blocks(text)
        if block.kind == "ordered_list"
        for item in block.items
    ]


def _classification_fields(
    identifier: str,
    next_identifier: str | None = None,
    *,
    text: str | None = None,
) -> tuple[tuple[str, ...], ...]:
    clause = _clause(identifier, next_identifier, text=text)
    blocks = _structured_markdown_blocks(clause)
    classification_blocks = tuple(
        block
        for block in blocks
        if block.kind == "field" and block.name == "Classification"
    )

    nonfenced_occurrences = 0
    for block in blocks:
        if block.kind == "fenced_code":
            continue
        if block.kind == "field":
            surface = f"{block.name}: {block.value}"
        elif block.kind in {"ordered_list", "unordered_list"}:
            surface = " ".join(block.items)
        else:
            surface = block.text
        nonfenced_occurrences += surface.count("Classification:")
    assert nonfenced_occurrences == len(classification_blocks)

    fields: list[tuple[str, ...]] = []
    for block in classification_blocks:
        assert block.value is not None
        observed = tuple(
            match.group(0) for match in CLASSIFICATION_PATTERN.finditer(block.value)
        )
        assert observed
        assert len(observed) == len(set(observed))
        fields.append(observed)
    labels = tuple(label for field in fields for label in field)
    assert len(labels) == len(set(labels))
    return tuple(fields)


def _classification_labels(
    identifier: str,
    next_identifier: str | None = None,
    *,
    text: str | None = None,
) -> tuple[str, ...]:
    return tuple(
        label
        for field in _classification_fields(identifier, next_identifier, text=text)
        for label in field
    )


def _markdown_table(
    path: str,
    heading: str,
    next_heading: str,
    *,
    text: str | None = None,
) -> tuple[tuple[str, ...], ...]:
    text = _text(path) if text is None else text
    assert heading.startswith("## ") and next_heading.startswith("## ")
    heading_title = heading.removeprefix("## ")
    next_title = next_heading.removeprefix("## ")
    headings = _markdown_atx_headings(text)
    matches = [item for item in headings if item[1] == heading_title]
    assert len(matches) == 1
    selected_heading = matches[0]
    assert selected_heading[0] == 2
    selected_index = headings.index(selected_heading)
    next_boundary = next(
        item for item in headings[selected_index + 1 :] if item[0] <= 2
    )
    assert next_boundary[0] == 2 and next_boundary[1] == next_title
    section = text[selected_heading[3] : next_boundary[2]]
    tables = _markdown_tables(section)
    assert len(tables) == 1
    selected_table = tables[0]
    assert sum(
        table[0] == selected_table[0]
        for table in _markdown_tables(text)
        if table
    ) == 1
    return selected_table


def _markdown_tables(text: str) -> tuple[tuple[tuple[str, ...], ...], ...]:
    tables: list[tuple[tuple[str, ...], ...]] = []
    current: list[tuple[str, ...]] = []
    fence: tuple[str, int] | None = None

    def finish_table() -> None:
        if current:
            table = tuple(current)
            assert all(len(row) == len(table[0]) for row in table)
            tables.append(table)
            current.clear()

    for line in text.splitlines():
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        candidate = _markdown_fence_candidate(line)
        if candidate is not None:
            marker, run_length, remainder = candidate
            if fence is None:
                finish_table()
                fence = (marker, run_length)
                continue
            if (
                marker == fence[0]
                and run_length >= fence[1]
                and _markdown_closer_suffix_is_ascii_space_tab(remainder)
            ):
                fence = None
                continue
        if fence is not None:
            continue
        if line.lstrip().startswith("|"):
            normalized = line.strip().removeprefix("|").removesuffix("|")
            current.append(tuple(cell.strip() for cell in normalized.split("|")))
        else:
            finish_table()
    finish_table()
    _require(
        fence is None,
        "operating_model.markdown_tables|block=<none>|failure=unbalanced_fence",
    )
    return tuple(tables)


def _expected_authority_rows() -> tuple[tuple[str, ...], ...]:
    return (
        ("External standing grant", "External standing-policy authority", "External authority system; Coordinator records only a verified safe binding", "External authority system; Coordinator holds a safe reference", "Reports may project bounded status only"),
        ("External revocation, expiry, or applicable global-stop directive", "External standing-policy authority", "External authority system; Coordinator records its verified binding and resulting progression facts", "External authority system; Coordinator holds a safe reference", "Reports do not author or clear the directive"),
        ("Program identity, revisions, work items, semantic attempts, progression decisions, effect intents, subordinate attempt/effect records, fences, cancellation intents, semantic acceptance, repair/replan decisions, and publication eligibility", "Coordinator under the admitted domain and parent grant", "Coordinator", "Coordinator durable state, using only safe material", "Reports are non-authoritative projections"),
        ("Current transition and `global_stop` mutation", "Current guarded Coordinator `WriterSession` contract", "Guarded Coordinator `WriterSession`", "Coordinator SQLite under current custody rules", "Reports remain projections"),
        ("Bootstrap worker invocation fact", "Direct-local supervisor as source", "Future Coordinator observation binding only", "Supervisor owns process-local fact; Coordinator may hold a safe reference", "Supervisor output is evidence, not acceptance"),
        ("Later runtime admission, profile handoff, identity, lifecycle, cancellation request, and result fact", "Execution Substrate", "ES", "ES; Coordinator may hold safe references", "ES observations remain source-attributed"),
        ("Candidate bytes and implementation activity", "Worker invocation", "Not Coordinator program truth", "Mutable worker workspace until sealed", "Worker completion is not acceptance"),
        ("Canonical capsule manifest, blobs, and portable digest", "Capsule builder acting at the worker boundary", "Immutable capsule store for the sealed artifact; Coordinator records only a safe digest/reference", "First-slice private immutable worker-side content-addressed store", "A digest is not authority or acceptance"),
        ("Validation result", "Executing validator or CI source", "Validator/CI source; Coordinator may bind an observation", "Validator/CI evidence system", "Success is not semantic acceptance"),
        ("Model planning or review proposal", "Model invocation as non-authoritative source evidence", "Coordinator may bind only the safe proposal/decision relationship required by a future contract", "Model/provider under its own custody contract", "Model output is a proposal only"),
        ("Git object and local ref", "Git", "Git object database and refs", "Git", "A commit is neither acceptance nor publication permission"),
        ("PR or remote publication state", "Git forge, when a future tranche permits it", "Git forge", "Git forge", "Blocked in the first slice"),
        ("Workspace teardown", "Worker supervisor", "Supervisor operational record, if a future contract requires one", "Worker supervisor", "Teardown does not decide acceptance"),
        ("Public report", "No semantic authority", "No authoritative fact writer", "Projection output only", "Projection only"),
    )


def _assert_classification_mapping(text: str) -> dict[str, tuple[str, ...]]:
    fields = {
        identifier: _classification_fields(identifier, text=text)
        for identifier, _ in C1_HEADINGS
    }
    assert fields == EXPECTED_CLASSIFICATION_FIELDS
    observed = {
        identifier: tuple(label for field in clause_fields for label in field)
        for identifier, clause_fields in fields.items()
    }
    assert observed == EXPECTED_CLASSIFICATIONS
    return observed


def _assert_authority_matrix_contract(text: str) -> None:
    table = _markdown_table(
        ".docs/authority-boundaries.md",
        "## Target Writer, Source, Custodian, And Projection Matrix",
        "## Evidence And References Versus Authority",
        text=text,
    )
    assert table[0] == (
        "Fact or material",
        "Semantic source or authority",
        "Durable recorder",
        "Physical custodian or safe-reference holder",
        "Projection treatment",
    )
    assert table[1] == ("---", "---", "---", "---", "---")
    assert table[2:] == _expected_authority_rows()
    assert len(table[2:]) == len(set(table[2:]))


def _assert_first_scenario_structured_contract(text: str) -> None:
    scenario = _clause("C1-AOM-009", text=text)
    blocks = _structured_markdown_blocks(scenario)
    assert _classification_fields("C1-AOM-009", text=text) == (
        ("ACCEPTED STRATEGIC TARGET",),
        ("DEFERRED OR BLOCKED EFFECT",),
    )
    fields = tuple(block for block in blocks if block.kind == "field")
    assert tuple(field.name for field in fields) == (
        "Classification",
        SCENARIO_PATHS_FIELD,
        "Classification",
    )
    assert fields[1].value == ""

    authorized_index = blocks.index(fields[1])
    assert authorized_index + 1 < len(blocks)
    path_block = blocks[authorized_index + 1]
    assert path_block.kind == "fenced_code"
    assert path_block.info == "text"
    assert tuple(
        block for block in blocks if block.kind == "fenced_code"
    ) == (path_block,)
    assert path_block.text == "\n".join(SCENARIO_PATHS)

    assert not any(
        block.kind in {"ordered_list", "unordered_list"} for block in blocks
    )
    structured = tuple(
        block.text
        for block in blocks
        if block.kind == "paragraph" and block.text.startswith("Its purpose is ")
    )
    assert structured == (SCENARIO_EFFECT_PARAGRAPH,)
    effect = re.fullmatch(
        r".* Its maximum effect is (?P<maximum>[^;]+); "
        r"(?P<excluded>.+?) are excluded\.",
        structured[0],
    )
    assert effect is not None
    surface = _ScenarioEffectSurface(
        maximum_effect=effect.group("maximum"),
        excluded_effects=tuple(
            item.removeprefix("a ")
            for item in re.split(r", (?:and )?", effect.group("excluded"))
        ),
    )
    assert surface == _ScenarioEffectSurface(
        maximum_effect="one local feature-branch Git commit",
        excluded_effects=(
            "push",
            "remote-ref mutation",
            "PR creation",
            "merge",
            "deployment",
            "production-autonomy claim",
        ),
    )


def _assert_direct_local_structured_contract(text: str) -> None:
    clause = _clause("C1-AOM-008", text=text)
    blocks = _structured_markdown_blocks(clause)
    assert _classification_fields("C1-AOM-008", text=text) == (
        ("ACCEPTED STRATEGIC TARGET", "DEFERRED OR BLOCKED EFFECT"),
    )
    fields = tuple(block for block in blocks if block.kind == "field")
    assert tuple(field.name for field in fields) == ("Classification",)
    lists = tuple(
        block
        for block in blocks
        if block.kind in {"ordered_list", "unordered_list"}
    )
    assert len(lists) == 1
    assert lists[0].kind == "ordered_list"
    assert lists[0].ordinals == tuple(range(1, 11))
    assert lists[0].items == DIRECT_LOCAL_CONDITIONS


def _assert_audit_isolation_structured_contract(text: str) -> None:
    clause = _clause("C1-AOM-012", text=text)
    blocks = _structured_markdown_blocks(clause)
    assert _classification_labels("C1-AOM-012", text=text) == (
        "PROCESS-ONLY GOVERNANCE",
    )
    fields = tuple(block for block in blocks if block.kind == "field")
    assert tuple(field.name for field in fields) == (
        "Classification",
        "Any future mutation-capable synthetic Git fixture must",
    )
    exclusions = tuple(
        block.text
        for block in blocks
        if block.kind == "paragraph" and block.text.startswith("This clause is ")
    )
    assert exclusions == (AUDIT_NON_RUNTIME_PARAGRAPH,)
    lists = tuple(
        block
        for block in blocks
        if block.kind in {"ordered_list", "unordered_list"}
    )
    assert len(lists) == 1
    assert lists[0].kind == "ordered_list"
    assert lists[0].ordinals == tuple(range(1, 6))
    assert lists[0].items == AUDIT_CONTROLS


def _assert_nonimplementation_contract(text: str) -> None:
    clause = _compact(_clause("C1-AOM-013", text=text))
    for phrase in (
        "C2A1 adds only one internal pure no-I/O production source module for immutable semantic values and six named coherence validators",
        "adds no schema, migration, dependency, package export, entry point, script, worker, subprocess call, network client",
        "filesystem capsule implementation",
        "model/provider implementation",
        "ES client",
        "Bridge integration",
        "Git mutation implementation",
        "runtime subordinate-authority implementation",
        "runtime enablement flag",
        "software-development runtime",
        "semantic-attempt runtime",
        "observation ingest",
        "validation/review/repair executor",
        "publisher",
        "service/API/IPC",
        "autonomous loop",
        "require a separately accepted implementation or owner-repository tranche",
    ):
        assert phrase in clause


def test_c1_clause_inventory_is_exact_and_ordered() -> None:
    assert tuple(_c1_clause_sections(_doc())) == tuple(
        identifier for identifier, _ in C1_HEADINGS
    )


def test_c2a_cross_reference_is_bounded_outside_unchanged_c1_inventory() -> None:
    preamble = _compact(_doc().split("## C1-AOM-001", 1)[0])
    assert ".docs/c2a-first-slice-semantic-protocol-contract.md" in preamble
    assert "`program_ref` and `program_version_ref` mandatory distinct identities" in preamble
    assert "C2A1 implements only the internal no-I/O values and six named pure coherence validators" in preamble
    assert "does not change C1 topology, add durable state, or authorize any effect" in preamble
    assert "preserves the one-local-commit maximum" in preamble
    assert "C2A-PROTO-" not in "\n".join(
        heading for _, heading, _, _ in _markdown_atx_headings(_doc())
    )


def test_classification_ledger_and_authoritative_composition_are_pinned() -> None:
    ledger = _compact(_clause("C1-AOM-001", "C1-AOM-002"))
    for classification in CLASSIFICATIONS:
        assert classification in ledger

    for phrase in (
        "authoritative composition record",
        "selected staged model",
        "first exact scenario",
        "first effect ceiling",
        "ten direct-local stop conditions",
        "parallel ES lanes",
        "ES-migration gate",
        "first-slice dependency exclusions",
        "process-only audit-isolation governance",
        ".docs/authority-boundaries.md",
        ".docs/software-development-progression-boundary.md",
        ".docs/worker-execution-boundary.md",
        ".docs/durable-state-model.md",
    ):
        assert phrase in ledger

    observed = _assert_classification_mapping(_doc())
    assert [
        identifier
        for identifier, labels in observed.items()
        if "CURRENT IMPLEMENTED CONTRACT" in labels
    ] == ["C1-AOM-001", "C1-AOM-006"]
    assert [
        identifier
        for identifier, labels in observed.items()
        if "PROCESS-ONLY GOVERNANCE" in labels and identifier != "C1-AOM-001"
    ] == ["C1-AOM-012"]

    current = _compact(_clause("C1-AOM-001", "C1-AOM-002"))
    authority = _compact(_clause("C1-AOM-006", "C1-AOM-007"))
    target_topology = _compact(_clause("C1-AOM-002", "C1-AOM-003"))
    nonimplementation = _compact(_clause("C1-AOM-013"))
    assert "It also has twelve private C2B2 reader roles with no public API" in current
    assert "only the mutation-receipt role has the bounded private C2B3 route-neutral program-initialization caller" in current
    assert "receipt-first nine-row/eight-entry genesis family" in current
    assert "It has no software-development program runtime, semantic-attempt runtime" in current
    assert "Current executable authorization remains unsupported and fail-closed." in authority
    assert "This subordinate-authorization behavior is not currently implemented." in authority
    assert "Neither route is implemented by this tranche." in target_topology
    assert "C2A1 adds only one internal pure no-I/O production source module" in nonimplementation


def test_staged_topology_is_ordered_and_transport_contracts_survive_es_migration() -> None:
    topology = _clause("C1-AOM-002", "C1-AOM-003")
    blocks = _code_blocks(topology)
    assert blocks == [
        "\n".join(
            (
                "reasoning model",
                "    -> Coordinator durable software-development progression",
                "    -> transport-neutral Worker Execution Boundary",
                "    -> bounded direct-local bootstrap/proof adapter",
                "    -> process-separated coding worker",
                "    -> exact immutable candidate capsule",
                "    -> validation and independent review observations",
                "    -> model review proposal",
                "    -> Coordinator acceptance, repair, replan, rejection, or block",
                "    -> at most one local feature-branch Git commit",
            )
        ),
        "\n".join(
            (
                "same Coordinator progression semantics",
                "same worker command/observation/fence/capsule contracts",
                "same worker artifact",
                "    -> ES reliable-submit adapter",
                "    -> ES admission and runtime lifecycle",
                "    -> process-separated coding worker",
                "    -> opaque capsule result transport or retention",
            )
        ),
    ]
    compact = _compact(topology)
    assert "Direct-local is a bounded bootstrap/proof route, not the target production execution path." in compact
    assert "Neither route is implemented by this tranche." in compact


def test_worker_source_process_release_extraction_and_credentials_are_bounded() -> None:
    worker = _compact(_clause("C1-AOM-003", "C1-AOM-004"))
    for phrase in (
        "Initial worker source and release machinery live in the Coordinator repository",
        "the worker executes as a separate OS process",
        "must not execute implementation work in-process",
        "The worker has no direct Coordinator SQLite mutation authority.",
        "must not receive a `WriterSession`, writer proof, Coordinator database path, or unrestricted Coordinator credentials",
        "No seventh repository is created now.",
        "demonstrated independent release cadence, independent ownership, multiple consumers, or materially separate dependency or security governance",
        "Exact package names, executable names, IPC, supervisor mechanics, build system, credential delivery, and deployment remain open.",
        "Bridge and Bridge Core are not worker implementation owners.",
    ):
        assert phrase in worker


def test_first_slice_effect_ceiling_and_excluded_effects_are_exact() -> None:
    effect = _compact(_clause("C1-AOM-004", "C1-AOM-005"))
    assert "one local feature-branch Git commit after Coordinator semantic acceptance and a separate effect decision" in effect
    assert "Worker authoring must not silently create that commit." in effect
    assert "Push, remote-ref mutation, PR creation, merge, deployment, and any production-autonomy claim are excluded." in effect
    assert "The effect ceiling is not permission" in effect


def test_capsule_authorship_sealing_custody_retrieval_and_exclusions_are_pinned() -> None:
    capsule = _compact(_clause("C1-AOM-005", "C1-AOM-006"))
    for phrase in (
        "private, immutable, content-addressed, worker-side, outside the mutable worktree, and outside Coordinator SQLite",
        "worker invocation is the source of candidate bytes and implementation activity",
        "capsule builder acting at the worker boundary seals the canonical manifest, blobs, and portable digest",
        "private immutable worker-side content-addressed store has first-slice physical custody",
        "Coordinator holds only a safe digest/reference and progression decisions",
        "reviewer receives read-only, attempt-bound, capsule-bound retrieval authority",
        "ES may later transport or retain the exported capsule opaquely",
        "Git becomes object and ref truth only after a separately selected commit effect",
        "A capsule digest is not a local path, endpoint, bearer retrieval credential, authorization proof, acceptance decision, or Git identity.",
        "new semantic attempt, new candidate identity, new portable capsule digest, and new candidate-bound validation and review",
        "raw prompts, model transcripts, Codex JSONL, unrestricted logs, unrestricted command output, credentials, private endpoints, trust material, and unrelated workspace content",
        "Exact path, storage implementation, encryption, garbage collection, retention duration, serialization, and wire encoding remain open.",
    ):
        assert phrase in capsule


def test_standing_authority_subordinate_records_model_and_user_roles_are_pinned() -> None:
    authority = _compact(_clause("C1-AOM-006", "C1-AOM-007"))
    for phrase in (
        "Current executable authorization remains unsupported and fail-closed.",
        "Current coding `global_stop`",
        "Coordinator cannot self-authorize",
        "a digest proves identity only, not permission",
        "External standing-policy authority authors immutable standing grants, grant revocation or expiry, applicable global-stop directives",
        "effect, risk, cost, time, repository, path, and publication ceilings",
        "It does not write Coordinator SQLite directly.",
        "derive narrower subordinate attempt/effect authorization records and issue attempt/effect fences",
        "binds the parent standing-grant identity",
        "binds the exact program version, work item, semantic attempt, and effect",
        "fails closed when the parent grant is absent, stale, expired, revoked, ambiguous, or insufficient",
        "is not a new grant issuer",
        "is not transferable to another effect or attempt unless the external grant expressly permits bounded reuse",
        "may never exceed, extend, renew, reinterpret, or outlive the external grant",
        "may never convert its own durable record into independent external authority",
        "This subordinate-authorization behavior is not currently implemented.",
        "Model reasoning creates cognitive planning, implementation, and review proposals.",
        "not a durable decision or effect authority",
        "The user steers major direction, priorities, and risk posture and is not a routine synchronous per-attempt approver.",
    ):
        assert phrase in authority


def test_review_acceptance_repair_and_publication_are_distinct() -> None:
    review = _clause("C1-AOM-007", "C1-AOM-008")
    assert _numbered_items(review)[:12] == [
        "worker completion;",
        "candidate capture;",
        "validation observation;",
        "independent review observation or proposal;",
        "model review proposal;",
        "Coordinator semantic acceptance;",
        "Coordinator repair decision;",
        "Coordinator replan decision;",
        "local Git commit;",
        "PR creation;",
        "merge; and",
        "deployment.",
    ]


def test_authoritative_writer_source_custodian_matrix_is_complete() -> None:
    _assert_authority_matrix_contract(_text(".docs/authority-boundaries.md"))


def test_direct_local_conditions_are_exact_and_ordered() -> None:
    _assert_direct_local_structured_contract(_doc())


def test_direct_local_structured_list_rejects_finite_mutations() -> None:
    text = _doc()
    list_start = text.index("1. The direct-local route implements")
    list_end = text.index("distinct proof/recovery policy.", list_start) + len(
        "distinct proof/recovery policy."
    )
    list_surface = text[list_start:list_end]
    second = "2. It is named explicitly as bootstrap/proof."
    third = "3. It initially permits one repository and one active invocation."
    mutations = (
        text.replace(second + "\n", "", 1),
        text.replace(second, second + "\n" + second, 1),
        text.replace(second + "\n" + third, third + "\n" + second, 1),
        text.replace(
            list_surface,
            list_surface + "\n   11. An unauthorized extra condition.",
            1,
        ),
        text.replace(
            list_surface,
            list_surface + "\n\n1. An unauthorized second normative list.",
            1,
        ),
        text.replace(list_surface, f"~~~text\n{list_surface}\n~~~", 1),
    )
    assert all(mutation != text for mutation in mutations)
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _assert_direct_local_structured_contract(mutation)


def test_first_recorded_es_scenario_paths_preconditions_and_effects_are_exact() -> None:
    _assert_first_scenario_structured_contract(_doc())
    scenario = _clause("C1-AOM-009", "C1-AOM-010")
    compact = _compact(scenario)
    for phrase in (
        "classify direct-local worker execution as a bounded bootstrap/proof edge",
        "record mandatory migration stop conditions",
        "preserve ES reliable-submit dependencies",
        "preserve the current ES P0",
        "create no ES runtime change",
        "maximum effect is one local feature-branch Git commit",
        "The scenario may occur only after the Coordinator C1 contract reset is accepted, the Bridge documentation/test reset is accepted, a separately authorized direct-local bootstrap implementation is accepted, and first-slice standing-policy and validation contracts exist.",
        "This tranche does not execute it and does not modify ES.",
    ):
        assert phrase in compact


def test_parallel_es_lanes_migration_gate_and_p0_non_displacement_are_pinned() -> None:
    migration = _clause("C1-AOM-010", "C1-AOM-011")
    assert _code_blocks(migration) == [
        "\n".join(
            (
                "Lane 1:",
                "  current ES P0 Remote Alpha operator-helper consolidation",
                "",
                "Lane 2:",
                "  Coordinator C1 contract reset and bounded autonomy bootstrap",
                "",
                "Lane 3:",
                "  ES reliable-submit, correlation, and reconciliation under ES planning authority",
            )
        )
    ]
    compact = _compact(migration)
    assert "The owner-governed lanes may progress in parallel" in compact
    assert "Coordinator documentation does not reprioritize ES." in compact
    for requirement in (
        "resolved execution-plan extraction",
        "reliable keyed submit",
        "caller correlation and response-loss recovery",
        "ES-owned ambiguous-submit reconciliation",
        "runtime admission and lifecycle observation",
        "cancellation correlation",
        "opaque capsule result transport or retention",
        "Coordinator-to-ES adapter conformance",
    ):
        assert requirement in compact
    assert "`resolved-execution-plan-extraction-foundation` remains the next source-bearing reliable-submit seam under ES planning authority." in compact
    assert "does not import, revive, or adopt the rejected archived implementation" in compact


def test_compatibility_component_exclusions_and_cross_repository_drift_are_pinned() -> None:
    compatibility = _compact(_clause("C1-AOM-011", "C1-AOM-012"))
    for phrase in (
        "`FiniteBacklog`",
        "current standing-lease behavior",
        "current zero-only budget behavior",
        "current READY-only dependency behavior",
        "current disabled-stage behavior",
        "current coding `global_stop`",
        "current `WriterSession` authority",
        "schema-0001 compatibility meanings and unchanged `0001_initial.sql` identity",
        "current generation-2 migration-0002 physical tip",
        "`control-plane-normal-shell/v1` as an ES/CP compatibility edge",
        "Coding and operational progression remain separately versioned domains",
        "operational progression is excluded from the first software-development slice",
        "Governed Execution OpenAI Bridge",
        "Governed Execution Bridge Core",
        "Control Plane",
        "Infrastructure Manager",
        "Governed Execution Maintenance Agent",
        "Host Lens",
        "Symphony",
        "Bridge remains a guarded adapter/evidence surface, not the worker owner or a direct-local trigger.",
        "later Bridge-only documentation and contract-test tranche",
        "Bridge Core adoption is deferred.",
        "not the complete Coordinator target operating model",
    ):
        assert phrase in compatibility


def test_audit_isolation_is_process_only_and_not_product_behavior() -> None:
    _assert_audit_isolation_structured_contract(_doc())
    audit_clause = _clause("C1-AOM-012", "C1-AOM-013")
    audit = _compact(audit_clause)
    assert "This tranche implements no fixture or helper." in audit


def test_c1_adds_no_source_schema_packaging_or_runtime_enablement() -> None:
    _assert_nonimplementation_contract(_doc())

    pyproject = tomllib.loads(_text("pyproject.toml"))
    assert pyproject["project"]["dependencies"] == []
    for table in ("scripts", "gui-scripts", "entry-points"):
        assert table not in pyproject["project"]

    migrations = ROOT / "src" / "ge_nwp_coordinator" / "sqlite_migrations"
    assert sorted(path.name for path in migrations.glob("*.sql")) == [
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
    ]


def test_c1_heading_parser_is_closed_world_fence_aware_and_bounded() -> None:
    text = _doc()
    canonical_second = "## C1-AOM-002 — Accepted Staged Topology"
    canonical_third = (
        "## C1-AOM-003 — Worker Source, Release, Process, And Credential Boundary"
    )
    fenced_identifier = (
        "```text\n## C1-AOM-009 - ignored fenced duplicate\n"
        "## C1-AOM-999 - ignored fenced unknown\n```\n\n"
    )
    assert tuple(_c1_clause_sections(fenced_identifier + text)) == tuple(
        identifier for identifier, _ in C1_HEADINGS
    )

    reordered = (
        text.replace(canonical_second, "## TEMPORARY-HEADING", 1)
        .replace(canonical_third, canonical_second, 1)
        .replace("## TEMPORARY-HEADING", canonical_third, 1)
    )
    malformed = (
        text + "\n## C1-AOM-009 - alternate delimiter duplicate\n",
        text + "\n ## C1-AOM-009 (alternate delimiter duplicate)\n",
        text + "\n## C1-AOM-009 — First Recorded ES Scenario\n",
        text + "\n## C1-AOM-999 — Unknown Clause\n",
        text.replace(canonical_second, "", 1),
        text.replace(canonical_second, "## C1-AOM-002: Accepted Staged Topology", 1),
        reordered,
        text + "\n```text\nunclosed\n",
        text + "\n~~~text\n```\n",
    )
    for mutation in malformed:
        with pytest.raises(AssertionError):
            _c1_clause_sections(mutation)

    level_three = text.replace(
        "Any future mutation-capable synthetic Git fixture must:",
        "### Audit Fixture Detail\n\nAny future mutation-capable synthetic Git fixture must:",
        1,
    )
    _assert_audit_isolation_structured_contract(level_three)

    level_two_shadow = text.replace(
        "Any future mutation-capable synthetic Git fixture must:",
        "## Shadow Audit Controls\n\nAny future mutation-capable synthetic Git fixture must:",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_audit_isolation_structured_contract(level_two_shadow)

    final_clause_shadow = text.replace(
        "C2A1 adds only one internal pure no-I/O production source module",
        "## Shadow Non-Implementation Section\n\n"
        "C2A1 adds only one internal pure no-I/O production source module",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_nonimplementation_contract(final_clause_shadow)


def test_shared_c1_block_representation_is_fence_aware_and_bounded() -> None:
    sample = (
        "   ### Structured Detail\n"
        "  Field name: value\n\n"
        "   1. first ordered item\n"
        "   2. second ordered item\n\n"
        " - first unordered item\n"
        " - second unordered item\n\n"
        "~~~text\n"
        "Classification: `NOT NORMATIVE`\n"
        "```text\n"
        "1. literal nested item\n"
        "```\n"
        "~~~\n"
    )
    blocks = _structured_markdown_blocks(sample)
    assert tuple(block.kind for block in blocks) == (
        "heading",
        "field",
        "ordered_list",
        "unordered_list",
        "fenced_code",
    )
    assert blocks[0].level == 3 and blocks[0].text == "Structured Detail"
    assert blocks[1].name == "Field name" and blocks[1].value == "value"
    assert blocks[2].ordinals == (1, 2)
    assert blocks[2].items == ("first ordered item", "second ordered item")
    assert blocks[3].items == ("first unordered item", "second unordered item")
    assert blocks[4].marker == "~" and blocks[4].info == "text"
    assert blocks[4].text == (
        "Classification: `NOT NORMATIVE`\n"
        "```text\n"
        "1. literal nested item\n"
        "```"
    )

    for malformed in (
        "```text\nunclosed\n",
        "~~~text\nmismatched\n```\n",
        "```text\nmismatched\n~~~\n",
    ):
        with pytest.raises(AssertionError):
            _structured_markdown_blocks(malformed)


def test_structured_classification_mapping_rejects_field_mutations() -> None:
    text = _doc()
    audit_heading = "## C1-AOM-012 — Audit-Isolation Process Governance"
    audit_field = "Classification: `PROCESS-ONLY GOVERNANCE`."
    trailing_classification_value = (
        "`PROCESS-ONLY GOVERNANCE`. Also `ACCEPTED STRATEGIC TARGET`."
    )
    trailing_classification = text.replace(
        f"{audit_heading}\n\n{audit_field}",
        f"{audit_heading}\n\nClassification: {trailing_classification_value}",
        1,
    )
    trailing_blocks = _structured_markdown_blocks(
        _clause("C1-AOM-012", text=trailing_classification)
    )
    assert tuple(
        block.value
        for block in trailing_blocks
        if block.kind == "field" and block.name == "Classification"
    ) == (trailing_classification_value,)
    with pytest.raises(AssertionError):
        _assert_audit_isolation_structured_contract(trailing_classification)

    target_heading = "## C1-AOM-002 — Accepted Staged Topology"
    target_field = "Classification: `ACCEPTED STRATEGIC TARGET`."
    mutations = (
        trailing_classification,
        text.replace(
            f"{audit_heading}\n\n{audit_field}",
            f"{audit_heading}\n\nClassification: `ACCEPTED STRATEGIC TARGET`.",
            1,
        ),
        text.replace(audit_field, f"{audit_field}\n\n{audit_field}", 1),
        text.replace(
            f"{audit_heading}\n\n{audit_field}",
            f"{audit_heading}\n\n"
            "Classification: `PROCESS-ONLY GOVERNANCE` and "
            "`ACCEPTED STRATEGIC TARGET`.",
            1,
        ),
        text.replace(
            f"{target_heading}\n\n{target_field}",
            f"{target_heading}\n\nClassification: `CURRENT IMPLEMENTED CONTRACT`.",
            1,
        ),
        text.replace(
            "Classification: `ACCEPTED STRATEGIC TARGET` with "
            "`DEFERRED OR BLOCKED EFFECT`\nlimits.",
            "Classification: `ACCEPTED STRATEGIC TARGET`.\n\n"
            "Classification: `DEFERRED OR BLOCKED EFFECT`.",
            1,
        ),
        text.replace(
            audit_field,
            f"{audit_field} Classification: `ACCEPTED STRATEGIC TARGET`.",
            1,
        ),
        text.replace(
            audit_field,
            f"~~~text\n{audit_field}\n~~~",
            1,
        ),
    )
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _assert_classification_mapping(mutation)


def test_authority_matrix_rejects_boundary_and_cell_mutations() -> None:
    text = _text(".docs/authority-boundaries.md")
    header = (
        "| Fact or material | Semantic source or authority | Durable recorder | "
        "Physical custodian or safe-reference holder | Projection treatment |"
    )
    rows = _expected_authority_rows()

    def line(row: tuple[str, ...]) -> str:
        return "| " + " | ".join(row) + " |"

    table_start = text.index(header)
    table_end = text.index("\n", text.index(line(rows[-1]))) + 1
    table_block = text[table_start:table_end]

    source_recorder = list(rows[0])
    source_recorder[1], source_recorder[2] = source_recorder[2], source_recorder[1]
    recorder_custodian = list(rows[0])
    recorder_custodian[2], recorder_custodian[3] = (
        recorder_custodian[3],
        recorder_custodian[2],
    )
    reordered = table_block.replace(
        line(rows[0]) + "\n" + line(rows[1]),
        line(rows[1]) + "\n" + line(rows[0]),
        1,
    )
    mutations = (
        text.replace(table_block, "## Shadow Matrix\n\n" + table_block, 1),
        text + "\n## Shadow Authority Matrix\n\n" + table_block,
        text.replace(line(rows[0]), line(tuple(source_recorder)), 1),
        text.replace(line(rows[0]), line(tuple(recorder_custodian)), 1),
        text.replace(line(rows[0]), line(rows[0]) + "\n" + line(rows[0]), 1),
        text.replace(
            line(rows[-1]),
            line(rows[-1])
            + "\n| Conflicting fact | Alternate writer | Alternate recorder | Alternate "
            "custodian | Alternate projection |",
            1,
        ),
        text.replace(line(rows[0]) + "\n", "", 1),
        text.replace(table_block, reordered, 1),
    )
    for mutation in mutations:
        with pytest.raises((AssertionError, StopIteration)):
            _assert_authority_matrix_contract(mutation)


def test_scenario_structured_effect_contract_rejects_finite_mutations() -> None:
    text = _doc()
    path_block = "\n".join(SCENARIO_PATHS)
    path_fence = f"```text\n{path_block}\n```"
    authorized_surface = f"{SCENARIO_PATHS_FIELD}:\n\n{path_fence}"
    effect_start = text.index("Its purpose is to classify direct-local worker execution")
    effect_end = text.index("claim are excluded.", effect_start) + len(
        "claim are excluded."
    )
    effect_source = text[effect_start:effect_end]
    mutations = (
        text.replace(path_block, path_block + "\nExecution Substrate/extra.go", 1),
        text.replace(SCENARIO_PATHS[0] + "\n", "", 1),
        text.replace(
            authorized_surface,
            authorized_surface + "\n\n" + authorized_surface,
            1,
        ),
        text.replace(
            path_fence,
            path_fence + "\n\n~~~text\nExecution Substrate/extra.go\n~~~",
            1,
        ),
        text.replace(
            path_fence,
            f"~~~text\n{path_fence}\n~~~",
            1,
        ),
        text.replace(
            "one local feature-branch Git commit;",
            "two local feature-branch Git commits;",
            1,
        ),
        text.replace(
            "one local feature-branch Git commit;",
            "one local feature-branch Git commit and one push;",
            1,
        ),
        text.replace(
            effect_source,
            effect_source
            + "\n\nMaximum effect: one local feature-branch Git commit",
            1,
        ),
        text.replace(
            effect_source,
            effect_source + "\n\nPermitted effects:\n\n- push",
            1,
        ),
        text.replace(effect_source, f"~~~text\n{effect_source}\n~~~", 1),
        text.replace(
            "Git commit; push,\nremote-ref mutation",
            "Git commit;\nremote-ref mutation",
            1,
        ),
        text.replace(
            "Git commit; push,\nremote-ref mutation",
            "Git commit;\nremote-ref mutation",
            1,
        )
        + "\nPush is excluded outside the scenario clause.\n",
        text.replace(
            "a production-autonomy\nclaim are excluded.",
            "a production-autonomy\nclaim are excluded. Push is also permitted.",
            1,
        ),
        text.replace(
            "deployment, and a production-autonomy\nclaim are excluded.",
            "deployment, production-autonomy claim, and package publication\n"
            "are excluded.",
            1,
        ),
    )
    assert all(mutation != text for mutation in mutations)
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _assert_first_scenario_structured_contract(mutation)


def test_audit_isolation_structured_contract_rejects_finite_mutations() -> None:
    text = _doc()
    first = "1. clear ambient Git variables;"
    second = "2. initialize an explicit audit-owned `.git`;"
    fifth = (
        "5. recheck the real repository HEAD, index, local configuration, and status\n"
        "   after each mutation-capable probe group."
    )
    exclusion_start = text.index("This clause is `NOT PRODUCT RUNTIME ARCHITECTURE`")
    exclusion_end = text.index("`NOT WORKER BEHAVIOR`.", exclusion_start) + len(
        "`NOT WORKER BEHAVIOR`."
    )
    exclusion_source = text[exclusion_start:exclusion_end]
    mutations = (
        text.replace(first + "\n", "", 1),
        text.replace(fifth, fifth + "\n6. add an unauthorized extra control.", 1),
        text.replace(
            fifth,
            fifth + "\n   6. add an indented unauthorized extra control.",
            1,
        ),
        text.replace(first, first + "\n" + first, 1),
        text.replace(first + "\n" + second, second + "\n" + first, 1),
        text.replace(first, f"~~~text\n{first}\n~~~", 1),
        text.replace(
            exclusion_source,
            f"~~~text\n{exclusion_source}\n~~~",
            1,
        ),
        text.replace(
            fifth,
            fifth + "\n\n1. add an unauthorized second control list.",
            1,
        ),
        text.replace(
            "## C1-AOM-012 — Audit-Isolation Process Governance\n\n"
            "Classification: `PROCESS-ONLY GOVERNANCE`.",
            "## C1-AOM-012 — Audit-Isolation Process Governance\n\n"
            "Classification: `ACCEPTED STRATEGIC TARGET`.",
            1,
        ),
        text.replace("`NOT WORKER BEHAVIOR`", "`WORKER BEHAVIOR`", 1),
        text.replace(
            "Any future mutation-capable synthetic Git fixture must:",
            "## Moved Audit Controls\n\n"
            "Any future mutation-capable synthetic Git fixture must:",
            1,
        ),
    )
    assert all(mutation != text for mutation in mutations)
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _assert_audit_isolation_structured_contract(mutation)


def _assert_c2b0_composition_overlay(text: str) -> None:
    heading = "C2B0 Accepted Durable-State Composition Overlay"
    role = "operating_model.c2b0_summary"
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
    for phrase in (
        "Classification: `ACCEPTED TARGET CONTRACT`.",
        "C2B0 closes only the target durable-state seams",
        "immutable `initialize` decision",
        "distinct risk-reducing `cancel` decision",
        "Author-effect establishment is separate from bound validation, review, and cancellation-effect establishment",
        "active coding global stop blocks initialization, author/validation/review effects, productive delivery or redelivery, acceptance, repair, productive replan, publication eligibility, latch consumption, and Git eligibility",
        "permits source evidence retention, terminal reject/block decisions, a cancel decision, cancellation-effect planning and cancellation delivery, and cancellation evidence ingest",
        "C2B5 owns source-observation ingest, cancel/redeliver decisions, and bound validation/review/cancellation effects",
        "C2B6 owns remaining program progression, publication eligibility, and the first-slice latch",
        "adds no schema, migration, runtime, worker, Bridge change, or ES change",
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


def test_c2b0_overlay_pins_split_stop_and_continuation_progression_ownership() -> None:
    _assert_c2b0_composition_overlay(_doc())


def test_c2b0_overlay_is_fence_aware_and_bounded() -> None:
    text = _doc()
    required = "C2B0 closes only the target durable-state seams"
    fenced_only = text.replace(required, f"~~~text\n{required}\n~~~~\n", 1)
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_composition_overlay(fenced_only)
    assert str(rejected.value) == (
        "operating_model.c2b0_summary|heading=C2B0 Accepted Durable-State Composition Overlay|failure=target_claim_missing"
    )

    boundary = text.replace(
        "Classification: `ACCEPTED TARGET CONTRACT`.\n\nC2B0 closes",
        "Classification: `ACCEPTED TARGET CONTRACT`.\n\n# Relocated Overlay\n\nC2B0 closes",
        1,
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_composition_overlay(boundary)
    assert str(rejected.value) == (
        "operating_model.c2b0_summary|heading=C2B0 Accepted Durable-State Composition Overlay|failure=target_claim_missing"
    )

    contradictory = text + "\n# Contradictory Current Status\n\nC2B is currently implemented.\n"
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_composition_overlay(contradictory)
    assert str(rejected.value) == (
        "operating_model.c2b0_summary|heading=C2B0 Accepted Durable-State Composition Overlay|failure=contradictory_current_status"
    )


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_authority_bypass() -> None:
    text = _doc()
    mutation = (
        text
        + "\n```bad`info\nC2B is currently implemented.\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_composition_overlay(mutation)
    assert str(rejected.value) == (
        "operating_model.c2b0_summary|heading=C2B0 Accepted Durable-State Composition Overlay|failure=contradictory_current_status"
    )

    valid_tilde = text + "\n~~~bad`info\nC2B is currently implemented.\n~~~\n"
    _assert_c2b0_composition_overlay(valid_tilde)

    blocks = _structured_markdown_blocks(
        "```bad`info\n## Visible Heading\n```\n```\n"
    )
    assert any(block.kind == "heading" and block.text == "Visible Heading" for block in blocks)
    tables = _markdown_tables(
        "```bad`info\n| visible |\n| --- |\n```\n```\n"
    )
    assert tables == ((('visible',), ('---',)),)


def test_c2b0_markdown_parsers_reject_invalid_backtick_info_duplicate_heading_bypass() -> None:
    text = _doc()
    mutation = (
        text
        + "\n```bad`info\n## C2B0 Accepted Durable-State Composition Overlay\n"
        + "```\n```\n"
    )
    with pytest.raises(AssertionError) as rejected:
        _assert_c2b0_composition_overlay(mutation)
    assert str(rejected.value) == (
        "operating_model.c2b0_summary|heading=C2B0 Accepted Durable-State Composition Overlay|failure=duplicate"
    )


def test_c2b2_current_administrative_pure_value_and_reader_composition_does_not_promote_progression() -> None:
    section = _compact(
        _unfenced_markdown(
            _bounded_markdown_section(
                _doc(),
                "C2B1/C2B2 Current Administrative, Pure-Value, And Private-Reader Composition",
                2,
                role="operating_model.c2b1_current",
                allow_eof=True,
            ),
            role="operating_model.c2b1_current.section",
        )
    )
    for phrase in (
        "`CURRENT IMPLEMENTED CONTRACT` for migration administration, private pure no-I/O row/value validation, private reader behavior, and the bounded private C2B3 route-neutral genesis and author-effect families",
        "C2B0 remains the historical contract-freeze tranche",
        "exact-current ordinary SQLite open",
        "explicit supported-prefix migration",
        "terminal-only application-generation compatibility",
        "cumulative packaged-SQL schema authority",
        "complete-suffix single-transaction migration",
        "three-way migration commit readback",
        "application generation 2",
        "catalog tip `0002_development_program_and_effect_state`",
        "physical schema representability only",
        "administrative evidence is not program, progression, decision, effect, acceptance, publication, or runtime truth",
        "four private pure row/value modules",
        "eighteen row self-digest checks",
        "five receipt result projections",
        "no SQL, reader capability, database reader, or independent product writer",
        "C2B2 Slice 3 separately implements exactly twelve private reader roles and twenty-four literal SELECT specifications",
        "All twelve roles have the bounded private C2B3D author-effect caller",
        "mutation-receipt role also retains the VS1B caller",
        "C2B3 now implements route-neutral program genesis and private author-effect establishment",
        "Bound effect, observation ingest, progression decisions, and C2B4-C2B6 remain target-only",
    ):
        assert phrase in section


def test_operating_model_markdown_closer_suffix_is_ascii_space_tab_only() -> None:
    for valid_suffix in ("", " ", "\t", " \t"):
        sample = f"~~~text\n## Hidden\n~~~{valid_suffix}\n## Visible\n"
        headings = _markdown_atx_headings(sample, role="operating_model.repair3")
        assert tuple(item[1] for item in headings) == ("Visible",)
        blocks = _structured_markdown_blocks(
            f"~~~text\nblock content\n~~~{valid_suffix}\n"
        )
        assert tuple(block.kind for block in blocks) == ("fenced_code",)
        assert _markdown_tables(
            f"~~~text\n| hidden |\n~~~{valid_suffix}\n"
        ) == ()

    for invalid_suffix in ("\u00a0", "\u2003", "not-a-closer"):
        closed_later = (
            "~~~text\n"
            f"~~~{invalid_suffix}\n"
            "C2B is currently implemented.\n"
            "## C2B0 Accepted Durable-State Composition Overlay\n"
            "~~~\n"
        )
        assert _markdown_atx_headings(
            closed_later,
            role="operating_model.repair3",
        ) == ()
        assert _unfenced_markdown(
            closed_later,
            role="operating_model.repair3",
        ) == ""

        with pytest.raises(AssertionError) as headings_rejected:
            _markdown_atx_headings(
                f"~~~text\n~~~{invalid_suffix}\n",
                role="operating_model.repair3",
            )
        assert str(headings_rejected.value) == (
            "operating_model.repair3|heading=<none>|failure=unbalanced_fence"
        )
        with pytest.raises(AssertionError) as blocks_rejected:
            _structured_markdown_blocks(f"~~~text\n~~~{invalid_suffix}\n")
        assert str(blocks_rejected.value) == (
            "operating_model.markdown_blocks|block=<none>|failure=unbalanced_fence"
        )
        with pytest.raises(AssertionError) as tables_rejected:
            _markdown_tables(f"~~~text\n~~~{invalid_suffix}\n")
        assert str(tables_rejected.value) == (
            "operating_model.markdown_tables|block=<none>|failure=unbalanced_fence"
        )


def test_narrowed_vertical_slice_order_and_jit_ledger_are_exact() -> None:
    document = (ROOT / DOC_PATH).read_text(encoding="utf-8")
    document_compact = " ".join(document.split())
    assert document.count("<!-- C2B3_NARROWED_OPERATING_MODEL_BEGIN -->") == 1
    assert document.count("<!-- C2B3_NARROWED_OPERATING_MODEL_END -->") == 1
    ordered = (
        "1. pre-I/O Coordinator progression;",
        "2. remote worker contact through semantic decision;",
        "3. a separate local-Git effect and stop;",
        "4. migration to ES before another productive bootstrap slice.",
    )
    positions = tuple(document.index(item) for item in ordered)
    assert positions == tuple(sorted(positions))
    for expected in (
        "This is not a mandatory program or tranche count.",
        "VS1B resolved the pre-I/O route-neutral initialization, minimum durable graph, migration-0002 sufficiency",
        "C2B3D now resolves only the private author-effect command, ten-row/nine-entry durable family",
        "minimum custody/retrieval, fresh verifier, invocation, capsule, evidence",
        "command/delivery/observation",
        "reliable keyed submit, response-loss and Nomad ambiguity",
        "These are required questions, not selected future schemas.",
        "Current capability remains generation 2, migration 0002, C2A1, C2B2",
        "private VS1B genesis family",
        "All worker, dispatch, Git, Bridge, ES, and other external execution remains absent.",
    ):
        assert expected in document_compact
    for forbidden in (
        "WorkSpecCustodyReceiptV1",
        "VerifiedAuthorityResultV1",
        "LocalGitCommandV1",
        "LocalGitDeliveryV1",
        "LocalGitObservationV1",
        "CREATE TABLE",
    ):
        assert forbidden not in document
