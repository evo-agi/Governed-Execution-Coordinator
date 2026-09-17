from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ".docs/rw0-remote-worker-contact-phase-entry.md"
C2B_PATH = ".docs/c2b-durable-development-state.md"
SELECTION_SOURCE_PATH = (
    "src/ge_nwp_coordinator/"
    "_development_pre_execution_plan_disposition_contracts.py"
)
SUPPORTING_PATHS = (
    ".docs/autonomous-software-development-operating-model.md",
    ".docs/worker-execution-boundary.md",
    ".docs/authority-boundaries.md",
    ".docs/durable-state-model.md",
)
CROSS_REFERENCE_OWNERS = (
    (SUPPORTING_PATHS[0], "C1 Autonomous Software-Development Operating Model"),
    (SUPPORTING_PATHS[1], "Worker Execution Boundary"),
    (SUPPORTING_PATHS[2], "Authority Boundaries"),
    (SUPPORTING_PATHS[3], "Durable State Model"),
)
CROSS_REFERENCE_PARENT = "Cognitive proposal and selection runtime"
CROSS_REFERENCE_HEADING = "RW0 remote-contact phase-entry target cross-reference"

CONTRACT_BEGIN = "<!-- COORDINATOR_RW0_PHASE_ENTRY_CONTRACT_BEGIN -->"
CONTRACT_END = "<!-- COORDINATOR_RW0_PHASE_ENTRY_CONTRACT_END -->"
CROSS_REFERENCE_BEGIN = (
    "<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_BEGIN -->"
)
CROSS_REFERENCE_END = "<!-- COORDINATOR_RW0_PHASE_ENTRY_CROSS_REFERENCE_END -->"
C2B_CROSS_REFERENCE_BEGIN = (
    "<!-- COORDINATOR_RW0_PHASE_ENTRY_TARGET_CROSS_REFERENCE_BEGIN -->"
)
C2B_CROSS_REFERENCE_END = (
    "<!-- COORDINATOR_RW0_PHASE_ENTRY_TARGET_CROSS_REFERENCE_END -->"
)
COMMITTED_STATUS_END = "<!-- COORDINATOR_SECTION41_COMMITTED_CURRENT_STATUS_END -->"

C2B_OPENING_SIZE = 1_883_380
C2B_OPENING_SHA256 = (
    "9401d62a0eb36e0cca1af5b8a6a80b540ddc4c781fee3faaf7318546cb532ccc"
)
K8_FIELDS = (
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
)
REQUIRED_HEADINGS = (
    "Status, scope, and nonimplementation",
    "Current entry lineage",
    "Bounded RW0 scenario class",
    "Authority model",
    "WorkSpec and selected-plan custody",
    "Host, transport, and process boundary",
    "Identity and fact ownership",
    "Target fact timeline",
    "Failure, ambiguity, cancellation, and recovery",
    "Capsule, validation, review, model, and decision",
    "ES and IM ownership",
    "Tranche map and open decisions",
)
TERMINAL_OUTCOMES = (
    "accept",
    "repair",
    "replan",
    "terminal_reject",
    "block",
    "cancel",
)


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _compact(value: str) -> str:
    return " ".join(value.split())


def _extract_unique(text: str, begin: str, end: str, *, role: str) -> str:
    begin_line, end_line, _headings, visible = _visible_marker_span(
        text, begin, end, role=role
    )
    return "\n".join(
        line for position, line in visible if begin_line[0] < position < end_line[0]
    ).strip()


def _broken_raw_marker_extractor(text: str, begin: str, end: str) -> str:
    """Predecessor control: raw bytes can put the begin marker in a fence."""
    assert text.count(begin) == text.count(end) == 1
    return text.split(begin, 1)[1].split(end, 1)[0]


def _broken_raw_first_body(text: str, begin: str, end: str) -> str:
    """Deliberately ignore visibility and duplicate hidden markers."""
    return text.split(begin, 1)[1].split(end, 1)[0]


def _owner_text() -> str:
    path = ROOT / OWNER_PATH
    assert path.is_file(), "RW0 owner document is absent"
    return path.read_text(encoding="utf-8")


def _require_phrases(text: str, phrases: tuple[str, ...], *, role: str) -> None:
    compact = _compact(text)
    for phrase in phrases:
        assert _compact(phrase) in compact, f"{role}: missing phrase: {phrase}"


def _parse_literal_tuple(source: str, name: str) -> tuple[str, ...]:
    module = ast.parse(source)
    for statement in module.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if isinstance(target, ast.Name) and target.id == name:
            value = ast.literal_eval(statement.value)
            assert type(value) is tuple
            assert all(type(item) is str for item in value)
            return value
    raise AssertionError(f"static tuple not found: {name}")


def _visible_markdown_lines_and_headings(
    text: str,
) -> tuple[tuple[tuple[int, str, int, int], ...], tuple[tuple[int, str], ...]]:
    """Return only unfenced ATX headings and ordinary lines with character offsets."""
    headings: list[tuple[int, str, int, int]] = []
    visible: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.lstrip(" ")
        indent = len(content) - len(stripped)
        candidate = None
        if indent <= 3 and stripped and stripped[0] in "`~":
            marker = stripped[0]
            run_length = len(stripped) - len(stripped.lstrip(marker))
            if run_length >= 3:
                candidate = (marker, run_length, stripped[run_length:])
        if fence is not None:
            if (
                candidate is not None
                and candidate[0] == fence[0]
                and candidate[1] >= fence[1]
                and all(character in " \t" for character in candidate[2])
            ):
                fence = None
        elif candidate is not None and (
            candidate[0] != "`" or "`" not in candidate[2]
        ):
            fence = candidate[:2]
        else:
            visible.append((offset, content))
            if indent <= 3:
                heading = re.fullmatch(r"(#{1,6})[ \t]+(.+?)[ \t]*", stripped)
                if heading is not None:
                    title = re.sub(r"[ \t]+#+[ \t]*$", "", heading[2]).strip()
                    assert title, "rw0.outcomes: empty visible heading"
                    headings.append(
                        (len(heading[1]), title, offset, offset + len(line))
                    )
        offset += len(line)
    assert fence is None, "rw0.outcomes: unclosed Markdown fence"
    ordinary: list[tuple[int, str]] = []
    hidden_comment = False
    for position, line in visible:
        stripped = line.strip()
        if hidden_comment:
            if "-->" in line:
                hidden_comment = False
                trailing = line.split("-->", 1)[1]
                if trailing.strip():
                    ordinary.append((position, trailing))
            continue
        if stripped.startswith("<!--") and "-->" not in stripped:
            hidden_comment = True
            continue
        ordinary.append((position, line))
    assert not hidden_comment, "rw0.structure: unclosed HTML comment"
    kept = {position for position, _line in ordinary}
    return tuple(h for h in headings if h[2] in kept), tuple(ordinary)


def _rw0_gap_is_hidden(
    visible: tuple[tuple[int, str], ...], start: int, end: int
) -> bool:
    return all(
        not line.strip() or re.fullmatch(r"<!--.*?-->", line.strip()) is not None
        for position, line in visible
        if start <= position < end
    )


def _visible_marker_span(
    text: str, begin: str, end: str, *, role: str
) -> tuple[
    tuple[int, str],
    tuple[int, str],
    tuple[tuple[int, str, int, int], ...],
    tuple[tuple[int, str], ...],
]:
    headings, visible = _visible_markdown_lines_and_headings(text)

    def marker_lines(marker: str) -> tuple[tuple[int, str], ...]:
        return tuple(
            (position, line)
            for position, line in visible
            if len(line) - len(line.lstrip(" ")) <= 3
            and line.lstrip(" ") == marker
        )

    begins = marker_lines(begin)
    ends = marker_lines(end)
    assert len(begins) == len(ends) == 1, f"{role}: one visible marker pair"
    assert begins[0][0] < ends[0][0], f"{role}: marker order"
    return begins[0], ends[0], headings, visible


def _heading_chain(
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
    return tuple((level, title) for level, title, _start, _end in stack)


def _owner_visible_body(text: str) -> str:
    begin, end, headings, visible = _visible_marker_span(
        text, CONTRACT_BEGIN, CONTRACT_END, role="rw0.owner"
    )
    roots = tuple(item for item in headings if item[0] == 1)
    assert len(roots) == 1 and roots[0][1] == (
        "RW0 Remote-Contact Phase-Entry Operating Model"
    ), "rw0.owner: unique live root"
    assert roots[0][3] <= begin[0], "rw0.owner: marker before root"
    assert _rw0_gap_is_hidden(visible, roots[0][3], begin[0]), (
        "rw0.owner: visible prose before BEGIN"
    )
    inside = tuple(item for item in headings if begin[0] < item[2] < end[0])
    assert inside and all(item[0] == 2 for item in inside), (
        "rw0.owner: complete live H2 body"
    )
    assert tuple(item[1] for item in inside) == (
        *REQUIRED_HEADINGS,
        "Non-authoritative initial proof fixture candidate",
    ), "rw0.owner: ordered live headings"
    assert all(
        _heading_chain(headings, item) == ((1, roots[0][1]), (2, item[1]))
        for item in inside
    ), "rw0.owner: heading ancestry"
    assert not any(item[2] > end[0] for item in headings), (
        "rw0.owner: heading outside owner"
    )
    assert _rw0_gap_is_hidden(visible, end[0] + len(end[1]), len(text)), (
        "rw0.owner: visible prose after END"
    )
    return "\n".join(
        line for position, line in visible if begin[0] < position < end[0]
    ).strip()


def _cross_reference_visible_body(path: str, text: str, root_title: str) -> str:
    role = f"rw0.cross_reference.{path}"
    begin, end, headings, visible = _visible_marker_span(
        text, CROSS_REFERENCE_BEGIN, CROSS_REFERENCE_END, role=role
    )
    roots = tuple(item for item in headings if item[0] == 1)
    parents = tuple(
        item for item in headings if item[0] == 2 and item[1] == CROSS_REFERENCE_PARENT
    )
    owners = tuple(
        item for item in headings if item[0] == 3 and item[1] == CROSS_REFERENCE_HEADING
    )
    assert len(roots) == len(parents) == len(owners) == 1, (
        f"{role}: unique root, parent, and owner"
    )
    root, parent, owner = roots[0], parents[0], owners[0]
    assert root[1] == root_title, f"{role}: intended document root"
    assert _heading_chain(headings, owner) == (
        (1, root_title), (2, CROSS_REFERENCE_PARENT), (3, CROSS_REFERENCE_HEADING)
    ), f"{role}: intended current owner chain"
    assert parent == tuple(item for item in headings if item[0] == 2)[-1], (
        f"{role}: final current parent"
    )
    assert owner == headings[-1], f"{role}: live final owner"
    preceding = tuple(item for item in headings if item[2] < begin[0])
    marker_before_heading = begin[0] < owner[2]
    if marker_before_heading:
        assert preceding and preceding[-1] == parent, f"{role}: adjacent parent"
        assert parent[3] <= begin[0] < owner[2] < end[0], (
            f"{role}: marker and heading order"
        )
        assert _rw0_gap_is_hidden(
            visible, begin[0] + len(begin[1]), owner[2]
        ), f"{role}: empty marker-to-owner gap"
    else:
        assert preceding and preceding[-1] == owner, f"{role}: adjacent owner"
        assert parent[3] <= owner[2] < begin[0] < end[0], (
            f"{role}: heading and marker order"
        )
        assert _rw0_gap_is_hidden(visible, owner[3], begin[0]), (
            f"{role}: empty owner-to-marker gap"
        )
    assert not any(item[2] > owner[2] and item[2] < end[0] for item in headings), (
        f"{role}: no nested replacement owner"
    )
    predecessor_end_marker = "<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->"
    predecessor_ends = tuple(
        item for item in visible
        if item[1].lstrip(" ") == predecessor_end_marker
        and len(item[1]) - len(item[1].lstrip(" ")) <= 3
    )
    owner_start = min(begin[0], owner[2])
    assert len(predecessor_ends) == 1 and parent[2] < predecessor_ends[0][0] < owner_start, (
        f"{role}: unique adjacent predecessor terminator"
    )
    assert _rw0_gap_is_hidden(
        visible, predecessor_ends[0][0] + len(predecessor_end_marker), owner_start
    ), f"{role}: visible prose before BEGIN"
    assert _rw0_gap_is_hidden(visible, end[0] + len(end[1]), len(text)), (
        f"{role}: visible prose after END"
    )
    assert any(
        line.strip() and not re.fullmatch(r"<!--.*?-->", line.strip())
        for position, line in visible
        if max(owner[3], begin[0] + len(begin[1])) <= position < end[0]
    ), f"{role}: empty visible owner body"
    return "\n".join(
        line for position, line in visible if begin[0] < position < end[0]
    ).strip()


RW0_CROSS_REFERENCE_MAP_SPECS = tuple(
    (
        path,
        root_title,
        ((1, root_title), (2, CROSS_REFERENCE_PARENT), (3, CROSS_REFERENCE_HEADING)),
        "<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->",
        CROSS_REFERENCE_BEGIN,
        CROSS_REFERENCE_END,
    )
    for path, root_title in CROSS_REFERENCE_OWNERS
)


def _assert_complete_rw0_cross_reference_map(documents: dict[str, str]) -> str:
    """The four live owners are one closed semantic and structural input."""
    assert len(RW0_CROSS_REFERENCE_MAP_SPECS) == 4
    assert tuple(documents) == tuple(spec[0] for spec in RW0_CROSS_REFERENCE_MAP_SPECS)
    bodies: list[str] = []
    for path, root_title, chain, predecessor, begin, end in RW0_CROSS_REFERENCE_MAP_SPECS:
        assert chain == (
            (1, root_title), (2, CROSS_REFERENCE_PARENT), (3, CROSS_REFERENCE_HEADING)
        )
        assert predecessor == "<!-- COGNITIVE_PROPOSAL_SELECTION_CROSS_REFERENCE_END -->"
        assert (begin, end) == (CROSS_REFERENCE_BEGIN, CROSS_REFERENCE_END)
        bodies.append(_compact(_cross_reference_visible_body(path, documents[path], root_title)))
    assert len(set(bodies)) == 1, "rw0.cross_reference.map: body mismatch"
    _require_phrases(
        bodies[0],
        (
            f"{OWNER_PATH} is the sole detailed owner.",
            "Current implementation stops at private C2B3D planned author delivery plus Section 41 pre-execution selection; executable contact and terminal-outcome runtime remain unsupported and fail-closed.",
            "RW0 target begins with a receipt-backed no-contact phase-entry fact and fresh authority, host, and custody gates.",
            "External standing-policy authority owns the parent grant; Coordinator target derives a separate narrower subordinate authorization record only inside that freshly verified grant.",
            "No current custody, adapter, supervisor, worker, capsule, validation, review, model, post-execution decision, terminal-outcome, latch, Git, or publication runtime exists.",
            "Direct-local permits one qualified remote Linux host, exactly the existing author attempt, effect, command, candidate, and initial delivery, with at most one author invocation and actual author delivery; reached validation, review, and cancellation use distinct current effects and deliveries.",
            "Existing author attempt/effect fences retain exact externally authored per-fence authorization-basis refs/digests",
            "The existing C2B `cancel` decision commits before the cancellation effect",
            "A separate future Coordinator-owned durable RW0 terminal-outcome fact closes each run",
            "The accepted direct-local C2B decision alone atomically consumes the one-way latch in its guarded writer transaction; the later terminal-outcome `accept` binds that exact decision ref/digest and committed latch postimage without another latch mutation.",
            "an unusable pre-effect cancel basis establishes no effect, fence, delivery, request, or signal and commits terminal-outcome `block` bound to the exact unusable decision and mismatch evidence, without another C2B decision.",
            "terminal-outcome `cancel` only when complete and unambiguous or terminal-outcome `block` otherwise without another C2B decision",
            "Direct-local route-local process and cancellation ownership does not absorb ES-route authority",
            "Exact custodian, transport, framing, Codex seam, schema, terminal-outcome representation, latch, and physical backends remain deferred.",
        ),
        role="rw0.cross_reference.map",
    )
    return bodies[0]


def _terminal_outcome_owner_range(
    text: str, *, heading: str, role: str
) -> tuple[int, int, tuple[str, ...]]:
    begin, marker_end, headings, visible = _visible_marker_span(
        text, CONTRACT_BEGIN, CONTRACT_END, role=f"rw0.outcomes.{role}"
    )
    matches = tuple(item for item in headings if item[1] == heading)
    assert len(matches) == 1, f"rw0.outcomes.{role}: unique visible owner"
    level, _title, start, heading_end = matches[0]
    assert level == 2, f"rw0.outcomes.{role}: owner level"
    assert begin[0] < start < marker_end[0], (
        f"rw0.outcomes.{role}: owner outside contract"
    )
    following = tuple(
        item for item in headings if item[2] > start and item[0] <= level
    )
    assert following, f"rw0.outcomes.{role}: missing owner boundary"
    end = following[0][2]
    assert end <= marker_end[0], (
        f"rw0.outcomes.{role}: owner boundary outside contract"
    )
    lines = tuple(line for position, line in visible if heading_end <= position < end)
    return heading_end, end, lines


def _validate_terminal_outcome_regions(text: str) -> None:
    owners = (
        ("Bounded RW0 scenario class", "scenario"),
        ("Capsule, validation, review, model, and decision", "decision"),
    )
    ranges: list[tuple[int, int]] = []
    for heading, role in owners:
        start, end, lines = _terminal_outcome_owner_range(
            text, heading=heading, role=role
        )
        ranges.append((start, end))
        inventories = tuple(
            line.lstrip(" ")
            for line in lines
            if len(line) - len(line.lstrip(" ")) <= 3
            and line.lstrip(" ").startswith("Terminal outcomes:")
        )
        assert len(inventories) == 1, (
            f"rw0.outcomes.{role}: exactly one visible owned inventory"
        )
        match = re.fullmatch(r"Terminal outcomes: ([a-z_, ]+)\.", inventories[0])
        assert match is not None, f"rw0.outcomes.{role}: inventory grammar"
        observed = tuple(part.strip() for part in match[1].split(","))
        assert observed == TERMINAL_OUTCOMES, (
            f"rw0.outcomes.{role}: exact ordered terminal domain"
        )
        owned_prose = _compact("\n".join(lines))
        assert (
            "Every listed terminal outcome ends RW0, launches no successor in "
            "RW0, and permits no Git or publication effect."
        ) in owned_prose, f"rw0.outcomes.{role}: independent terminal stop"
        if role == "scenario":
            assert (
                "Every terminal outcome ends RW0, and repair or replan never "
                "launches a successor in RW0."
            ) in owned_prose, "rw0.outcomes.scenario: terminal stop and no successor"
        else:
            assert (
                "Coordinator alone commits the applicable C2B decision and "
                "the distinct future RW0 terminal-outcome fact through guarded "
                "writer authority."
            ) in owned_prose, "rw0.outcomes.decision: Coordinator ownership"
            assert "No Git effect follows the RW0 terminal outcome." in owned_prose, (
                "rw0.outcomes.decision: terminal effect ceiling"
            )
    _headings, visible = _visible_markdown_lines_and_headings(text)
    all_inventories = tuple(
        position
        for position, line in visible
        if len(line) - len(line.lstrip(" ")) <= 3
        and line.lstrip(" ").startswith("Terminal outcomes:")
    )
    assert len(all_inventories) == 2 and all(
        any(start <= position < end for start, end in ranges)
        for position in all_inventories
    ), "rw0.outcomes: no sibling or relocated inventory"


def _broken_whole_document_outcome_checker(text: str) -> bool:
    """Deliberately reproduces the predecessor's non-causal global check."""
    line = "Terminal outcomes: " + ", ".join(TERMINAL_OUTCOMES) + "."
    return _compact(line) in _compact(text)


def _replace_owned_inventory(
    text: str, *, heading: str, role: str, replacement: str
) -> str:
    start, end, lines = _terminal_outcome_owner_range(
        text, heading=heading, role=role
    )
    inventory = "Terminal outcomes: " + ", ".join(TERMINAL_OUTCOMES) + "."
    assert lines.count(inventory) == 1
    owned = text[start:end]
    assert owned.count(inventory) == 1
    return text[:start] + owned.replace(inventory, replacement, 1) + text[end:]


REPAIR_SEMANTIC_REQUIREMENTS = (
    (
        "exact_author_lineage",
        "RW0 retains exactly the existing C2B3D semantic attempt, author effect intent, author command, author candidate, and initial author delivery identity.",
    ),
    (
        "no_second_attempt",
        "No replacement or second semantic attempt occurs in RW0.",
    ),
    (
        "no_second_effect",
        "No replacement or second author effect occurs in RW0.",
    ),
    (
        "no_second_command",
        "No replacement or second author command occurs in RW0.",
    ),
    (
        "no_second_candidate",
        "No replacement or second author candidate occurs in RW0.",
    ),
    (
        "no_second_invocation",
        "No second candidate-authoring worker or source invocation occurs in RW0.",
    ),
    (
        "no_author_relaunch_or_redelivery",
        "No author relaunch or author redelivery occurs in RW0.",
    ),
    (
        "author_delivery_ceiling",
        "The existing author-candidate delivery identity permits exactly one actual author-candidate delivery in RW0.",
    ),
    (
        "later_current_effect_deliveries",
        "Validation, independent review, and cancellation each require a distinct current effect intent, current effect fence, and initial delivery under the same originating semantic attempt and author-command lineage.",
    ),
    (
        "later_effect_ceiling",
        "At most one actual validation-effect delivery, one actual review-effect delivery, and one actual cancellation-effect delivery for the exact currently targeted effect may occur if those effects are reached.",
    ),
    (
        "no_redelivery",
        "Every reached effect has zero redelivery or retry in RW0; an ambiguous delivery stops and reconciles.",
    ),
    (
        "model_not_delivery_effect",
        "The model-review proposal is a separate source invocation and not a DeliveryEnvelopeV1 effect class.",
    ),
    (
        "existing_fences_inert",
        "The existing author attempt fence and author effect fence are inert persisted bounds and are reused exactly; they are not executable permission.",
    ),
    (
        "subordinate_existing_binding",
        "Coordinator derives narrower subordinate authorization bound to the exact existing author attempt and effect fences only after fresh parent verification; it does not issue replacement author fences.",
    ),
    (
        "immutable_external_basis",
        "Each persisted author fence retains its exact externally authored authorization-basis reference and digest; those immutable basis bindings are inert lineage and ceiling bounds, not permission.",
    ),
    (
        "separate_subordinate_record",
        "The future Coordinator-derived subordinate authorization is a separate record with its own identity and digest; it neither replaces nor rewrites either existing author fence.",
    ),
    (
        "per_fence_basis_equality",
        "For each existing author fence, the subordinate record binds that fence's persisted authorization-basis reference and digest byte-for-byte and binds the exact existing fence reference and digest.",
    ),
    (
        "verified_basis_family",
        "The current external verifier proves that the parent grant authorizes the immutable fence-bound basis family and that the attempt-fence and author-effect-fence basis bindings are jointly compatible with the same parent-grant family and exact K8/L34 lineage.",
    ),
    (
        "basis_pairs_need_not_equal",
        "The two fence-bound authorization-basis pairs need not equal each other; each must equal its corresponding subordinate-record binding under a freshly verified common parent-grant-family relation.",
    ),
    (
        "incompatible_basis_blocks",
        "If any basis equality, ancestry, family, scope, freshness, revocation, expiry, repository, base, path, or global-stop relation is false, missing, stale, or ambiguous, no subordinate record is established, no retrieval, contact, author delivery, or launch occurs, no replacement author lineage is minted, and a C2B block decision precedes matching RW0 terminal-outcome block.",
    ),
    (
        "later_subordinate_bindings",
        "Later validation, review, and active-cancellation effects each bind their own current effect fence and subordinate authorization to the same verified parent-grant family and exact originating attempt-fence lineage; none reuses the author effect fence.",
    ),
    (
        "complete_verifier_relation",
        "Before WorkSpec retrieval, author launch, and every later effect, a current verifier proves the complete grant, subordinate authorization, applicable attempt and current effect fences, expiry, revocation, repository, base, path, and current global stop relation.",
    ),
    (
        "later_effect_fences",
        "Coordinator may establish distinct current effect intents and fences for validation, review, or cancellation within freshly verified parent authority.",
    ),
    (
        "normal_terminal_branch",
        "On the normal branch, Coordinator commits one C2B accept, repair, replan, terminal_reject, or block decision after validation, review, and model proposal complete or become conclusively unavailable.",
    ),
    (
        "early_cancel_not_terminal",
        "The pre-effect decision does not terminate RW0 or consume the latch.",
    ),
    (
        "cancel_effect_before_request",
        "Coordinator establishes the distinct `cancel_effect` intent, current effect fence, subordinate authorization binding, and initial cancellation delivery before an external request.",
    ),
    (
        "terminal_cancel_after_teardown",
        "Only after that source-native reconciliation proves every required terminal relation complete and non-ambiguous may the guarded writer commit the one RW0 terminal-outcome fact with value `cancel`.",
    ),
    (
        "post_teardown_reconciliation",
        "Post-teardown source-native reconciliation covers process-group and descendant state, worker observations, request, acknowledgement, signal, exit, workspace cleanup, capsule custody, and applicable delivery and source receipts.",
    ),
    (
        "ambiguous_reconciliation_blocks",
        "If reconciliation is incomplete, contradictory, stale, or ambiguous, it commits terminal-outcome value `block` bound to the same pre-effect cancel decision and unresolved evidence, without a C2B block decision.",
    ),
    (
        "one_final_decision",
        "The future guarded Coordinator writer commits exactly one durable RW0 terminal-outcome fact per run after outcome-specific evidence and current-head checks; it is not a development_decision, effect basis, executable permission, source observation, report, or projection.",
    ),
    (
        "early_control_not_final",
        "On the active-cancel branch, exactly one pre-effect C2B cancel decision bases the cancel effect; terminal-outcome cancel binds that decision and complete post-teardown reconciliation without a second cancel decision.",
    ),
    (
        "normal_has_no_cancel_control",
        "No additional cancellation-control decision exists on a non-cancel branch, and no other Coordinator progression decision is created on the active-cancel branch.",
    ),
    (
        "reconciliation_not_decision",
        "Source reconciliation alone does not establish terminal outcome; only the guarded Coordinator writer commits the fact after rereading current evidence and heads.",
    ),
    (
        "worker_start_owner",
        "The worker process owns and canonically authors worker_started, worker_completed, and candidate_captured observations.",
    ),
    (
        "process_launch_not_start",
        "Supervisor process launch does not prove worker_started; worker_started does not prove completion or candidate capture.",
    ),
    (
        "direct_local_route_owner",
        "The direct-local supervisor owns only route-local process control, cancellation-request delivery, route receipts, and source-native reconciliation facts.",
    ),
    (
        "es_route_owner",
        "Execution Substrate owns ES-route admission, reliable submit, runtime lifecycle, cancellation, runtime identity and credential handoff, route correlations, and retained results.",
    ),
    (
        "no_parallel_es_truth",
        "Direct-local never claims ES-route facts or creates a parallel ES lifecycle store.",
    ),
)

REPAIR_SEMANTIC_MUTANTS = {
    "exact_author_lineage": "RW0 substitutes a new semantic attempt, author effect, command, candidate, and delivery.",
    "no_second_attempt": "A replacement semantic attempt may be minted in RW0.",
    "no_second_effect": "A second author effect may be minted in RW0.",
    "no_second_command": "A second author command may be minted in RW0.",
    "no_second_candidate": "A replacement author candidate may be minted in RW0.",
    "no_second_invocation": "A second candidate-authoring worker invocation may run in RW0.",
    "no_author_relaunch_or_redelivery": "Author relaunch and redelivery are permitted in RW0.",
    "author_delivery_ceiling": "RW0 permits exactly one total delivery across all effects.",
    "later_current_effect_deliveries": "Validation, review, and cancellation reuse the author delivery.",
    "later_effect_ceiling": "Later effects have an unbounded delivery ceiling.",
    "no_redelivery": "An ambiguous author delivery permits redelivery or relaunch.",
    "model_not_delivery_effect": "The model proposal is a DeliveryEnvelopeV1 effect class.",
    "existing_fences_inert": "Existing author fences alone authorize launch.",
    "subordinate_existing_binding": "Coordinator mints replacement author fences after phase entry.",
    "immutable_external_basis": "The existing author fences are rewritten to name the new subordinate record.",
    "separate_subordinate_record": "The external authority authors the subordinate record inside the existing author fence.",
    "per_fence_basis_equality": "The subordinate record substitutes another attempt authorization ref and another effect authorization digest.",
    "verified_basis_family": "A current parent grant suffices without verified ancestry or a common basis family.",
    "basis_pairs_need_not_equal": "The two basis pairs are assumed to be one family without a current verifier result.",
    "incompatible_basis_blocks": "An incompatible authorization family is absorbed by minting replacement author fences and launching.",
    "later_subordinate_bindings": "Validation, review, and cancel reuse the author effect fence and authorization binding.",
    "complete_verifier_relation": "A persisted fence digest suffices without a current grant or subordinate relation.",
    "later_effect_fences": "Later effects reuse the author effect fence.",
    "normal_terminal_branch": "The normal terminal decision may precede all required evidence.",
    "early_cancel_not_terminal": "The pre-effect C2B cancel decision alone terminates RW0.",
    "cancel_effect_before_request": "The cancellation request precedes its effect fence and delivery.",
    "terminal_cancel_after_teardown": "Coordinator commits terminal cancel before process exit and teardown.",
    "post_teardown_reconciliation": "Coordinator omits reconciliation of workspace cleanup and process descendants.",
    "ambiguous_reconciliation_blocks": "Ambiguous source reconciliation produces terminal-outcome cancel.",
    "one_final_decision": "RW0 may commit two terminal-outcome facts.",
    "early_control_not_final": "A second post-teardown C2B cancel decision closes RW0.",
    "normal_has_no_cancel_control": "The non-cancel branch commits a cancellation-control decision.",
    "reconciliation_not_decision": "Source reconciliation itself commits terminal outcome without Coordinator action.",
    "worker_start_owner": "The supervisor or adapter authors worker_started.",
    "process_launch_not_start": "Supervisor process launch proves worker_started.",
    "direct_local_route_owner": "Direct-local has no route-local process or cancellation responsibility.",
    "es_route_owner": "Direct-local owns ES admission, lifecycle, cancellation, and results.",
    "no_parallel_es_truth": "Direct-local keeps a parallel ES lifecycle store.",
}

EXISTING_REPAIR_DIAGNOSTIC_NAMES = frozenset(
    (
        "author_delivery_ceiling",
        "later_current_effect_deliveries",
        "later_effect_ceiling",
        "no_redelivery",
        "model_not_delivery_effect",
        "existing_fences_inert",
        "subordinate_existing_binding",
        "complete_verifier_relation",
        "later_effect_fences",
        "normal_terminal_branch",
        "early_cancel_not_terminal",
        "cancel_effect_before_request",
        "terminal_cancel_after_teardown",
        "worker_start_owner",
        "process_launch_not_start",
        "direct_local_route_owner",
        "es_route_owner",
        "no_parallel_es_truth",
    )
)


RW0_TERMINAL_OUTCOME_REQUIREMENTS = (
    (
        "closed_c2b_kinds",
        "The exact C2B decision-kind inventory remains initialize, accept, repair, replan, terminal_reject, block, redeliver, cancel; RW0-A does not add or reinterpret a C2B decision kind.",
        "RW0-A adds a terminal_outcome C2B decision kind.",
    ),
    (
        "pre_effect_cancel_basis",
        "The existing immutable C2B cancel decision commits before the cancellation effect, preassigns its effect intent, fence, first delivery, and exact target, and is the cancellation effect's exact basis_decision_ref.",
        "The cancellation effect uses the later terminal-outcome fact as its basis_decision_ref.",
    ),
    (
        "separate_terminal_fact",
        "The future guarded Coordinator writer commits exactly one durable RW0 terminal-outcome fact per run after outcome-specific evidence and current-head checks; it is not a development_decision, effect basis, executable permission, source observation, report, or projection.",
        "The RW0 terminal-outcome fact is omitted; a report projects terminal closure.",
    ),
    (
        "finite_non_authorizing_outcome",
        "The terminal-outcome fact has the finite values accept, repair, replan, terminal_reject, block, cancel; it creates no program version or effect authority by itself.",
        "The terminal-outcome fact advances the program version and authorizes another effect.",
    ),
    (
        "noncancel_same_kind_decision",
        "On a non-cancel branch, exactly one corresponding immutable C2B development_decision of the same kind commits first, and the terminal-outcome fact binds its exact ref and digest without contradicting kind or lineage.",
        "A non-cancel terminal outcome needs no C2B decision and may contradict its kind.",
    ),
    (
        "accept_decision_atomic_latch",
        "The immutable C2B accept decision consumes the productive-direct-local acceptance latch atomically in the same guarded Coordinator writer transaction; no terminal-outcome fact is a prerequisite for that latch mutation.",
        "Latch consumption waits for the terminal-outcome fact after the accept decision commits.",
    ),
    (
        "accept_outcome_binds_postimage",
        "The later terminal-outcome accept binds the exact accepted decision ref and digest and the committed latch postimage from that decision transaction; it never consumes, advances, reopens, repairs, or otherwise mutates the latch.",
        "The terminal-outcome accept consumes the latch and binds a different postimage.",
    ),
    (
        "accept_uncertainty_no_second_mutation",
        "If the accepted decision committed while the terminal-outcome commit is uncertain, the latch remains consumed; exact guarded-writer readback precedes any new effect or successor, and recovery creates neither a second accept decision nor a second latch mutation.",
        "An uncertain terminal outcome permits a second accept decision, latch mutation, and successor.",
    ),
    (
        "nonaccept_no_latch_mutation",
        "Repair, replan, terminal_reject, ordinary block, and cancel decisions do not consume the productive-direct-local acceptance latch.",
        "Repair, replan, terminal_reject, block, and cancel decisions may consume the latch.",
    ),
    (
        "active_cancel_exact_decision",
        "On the active-cancel branch, exactly one pre-effect C2B cancel decision bases the cancel effect; terminal-outcome cancel binds that decision and complete post-teardown reconciliation without a second cancel decision.",
        "A second post-teardown C2B cancel decision establishes terminal cancel before reconciliation.",
    ),
    (
        "active_cancel_block_without_decision",
        "If active-cancel reconciliation is incomplete, contradictory, stale, or ambiguous, terminal-outcome block binds the same pre-effect cancel decision and unresolved evidence without a C2B block decision.",
        "Unresolved active cancellation creates a second C2B block decision.",
    ),
    (
        "cancel_currentness_after_readback",
        "After exact cancel-decision commit readback and before cancel-effect establishment, the guarded Coordinator writer and current verifier recheck the decision ref/digest, current program/version/attempt/target head, stop version/state, parent grant, subordinate authorization, attempt/effect fences and authorization bases, expiry, revocation, repository, base, path, audience, and preassigned effect/fence/first delivery/target.",
        "The cancel effect is established before cancel-decision readback or current-head verification.",
    ),
    (
        "unusable_cancel_no_effect",
        "If that pre-effect cancel basis is stale, superseded, incompatible, missing, or ambiguous, RW0 establishes no cancel effect, fence, delivery, request, or signal and creates no replacement cancel or block decision, semantic attempt, or author lineage.",
        "A stale pre-effect cancel basis creates a replacement cancel decision and sends a request.",
    ),
    (
        "unusable_cancel_terminal_block",
        "The pre_effect_cancel_basis_unusable sub-branch commits one RW0 terminal-outcome block bound to the unusable cancel decision and exact current-head, stop, and verification mismatch evidence, without a C2B block decision, successor, Git effect, or publication.",
        "The stale pre-effect cancel basis produces terminal cancel without mismatch evidence.",
    ),
    (
        "unusable_cancel_before_teardown",
        "This pre-effect terminal block can close RW0 before a cancellation effect or teardown; it is distinct from the post-teardown reconciliation block.",
        "A stale pre-effect cancel decision has no terminal path before teardown.",
    ),
    (
        "valid_cancel_continues",
        "If the pre-effect cancel basis remains current and valid, RW0 follows the existing cancel effect, request, acknowledgement, signal, exit, teardown, reconciliation, and terminal-outcome sequence.",
        "A valid pre-effect cancel basis skips effect establishment and immediately declares terminal cancel.",
    ),
    (
        "cancel_decision_not_terminal",
        "The pre-effect C2B cancel decision does not prove terminal cancellation or block, and the later terminal-outcome fact cannot basis its already-established cancel effect.",
        "The pre-effect cancel decision proves terminal cancellation and the later outcome bases its effect.",
    ),
    (
        "cancel_decision_not_source_or_semantics",
        "The C2B cancel decision is neither a cancellation request, acknowledgement, signal, process exit, workspace teardown, source reconciliation, semantic abandonment, semantic cancellation, nor RW0 terminal closure.",
        "The C2B cancel decision itself is semantic cancellation.",
    ),
    (
        "no_other_active_cancel_decision",
        "No other Coordinator progression decision is created on the active-cancel branch.",
        "Active cancellation creates a second Coordinator progression decision.",
    ),
    (
        "reconciliation_not_outcome",
        "Source reconciliation alone does not establish terminal outcome; only the guarded Coordinator writer commits the fact after rereading current evidence and heads.",
        "Source reconciliation itself establishes terminal outcome without a Coordinator commit.",
    ),
    (
        "terminal_stop",
        "No terminal-outcome value permits a successor, Git effect, or publication inside RW0.",
        "Terminal repair launches a successor and publishes inside RW0.",
    ),
    (
        "outcome_commit_recovery",
        "Terminal-outcome commit uncertainty requires exact guarded-writer readback; unresolved outcome prevents new effect or successor and recovery never fabricates another accept, cancel, or block decision or latch mutation. A committed accept decision retains its consumed latch during unresolved outcome recovery.",
        "Unresolved terminal-outcome commit permits a new effect and another cancel decision.",
    ),
    (
        "exact_outcome_lineage",
        "The terminal-outcome fact binds the exact phase-entry identity, C2B3D and Section 41 lineage, applicable decision refs and digests, effect/delivery/source evidence, reached capsule/validation/review/model evidence, current global-stop and head state, and any acceptance-latch postimage.",
        "The terminal-outcome fact binds only an unversioned report identifier.",
    ),
    (
        "representation_deferred",
        "The terminal-outcome semantic role is frozen here, while its identity, digest, row, receipt, graph, table, migration, application generation, and public API representation remain deferred.",
        "Migration 0004 and a public terminal-outcome class are implemented now.",
    ),
)


# Each sentence below introduces one independently forbidden interpretation. The
# additive mutants retain every required positive sentence, so rejection cannot
# be explained by deletion of a required phrase.
RW0_TERMINAL_OUTCOME_CONTRADICTIONS = (
    ("second_post_teardown_cancel", "A second post-teardown C2B cancel decision closes the active-cancel branch."),
    ("outcome_as_cancel_basis", "The cancellation effect cites the later terminal-outcome fact as its basis_decision_ref."),
    ("cancel_before_reconciliation", "Terminal-outcome cancel commits before source-native reconciliation completes."),
    ("active_cancel_second_block", "Active-cancel terminal block requires a second C2B block decision."),
    ("outcome_as_report", "The RW0 terminal-outcome fact is only a report or projection."),
    ("outcome_as_source_observation", "The RW0 terminal-outcome fact is a source observation."),
    ("outcome_advances_version", "The RW0 terminal-outcome fact advances the program version by itself."),
    ("noncancel_without_decision", "A non-cancel terminal outcome requires no C2B decision."),
    ("noncancel_kind_contradiction", "A non-cancel terminal outcome may contradict its C2B decision kind."),
    ("two_outcome_facts", "One RW0 run may commit two terminal-outcome facts."),
    ("outcome_authorizes_effect", "The RW0 terminal-outcome fact authorizes another effect."),
    ("outcome_representation_current", "The RW0 terminal-outcome row and public API are implemented now."),
    ("latch_delayed_until_outcome", "Latch consumption waits until the terminal-outcome fact commits."),
    ("outcome_consumes_latch", "The terminal-outcome fact consumes or reopens the productive-direct-local acceptance latch."),
    ("outcome_prerequisite_to_accept", "The terminal-outcome fact must commit before the C2B accept decision may consume the latch."),
    ("wrong_latch_postimage", "The terminal-outcome accept binds a different latch postimage from the accepted decision transaction."),
    ("second_accept_latch_mutation", "An uncertain terminal outcome permits a second accept decision and a second latch mutation."),
    ("nonaccept_consumes_latch", "Repair, replan, terminal_reject, block, or cancel consumes the acceptance latch."),
    ("stale_cancel_effect", "A stale pre-effect cancel decision may establish the cancellation effect."),
    ("stale_cancel_replacement", "A stale pre-effect cancel decision permits a replacement cancel or block decision inside RW0."),
    ("stale_cancel_request", "A stale pre-effect cancel decision permits a cancellation request or signal without an effect."),
    ("stale_cancel_wrong_outcome", "A stale pre-effect cancel decision produces terminal-outcome cancel."),
    ("stale_cancel_successor", "The pre_effect_cancel_basis_unusable sub-branch launches a successor inside RW0."),
    ("stale_cancel_report_authority", "A verifier projection or report authors the pre-effect terminal outcome."),
)


def _assert_c2b_cancel_source_contract(source: str) -> None:
    section = source.split("## 6. Exact Decision-Kind Inventory", 1)[1]
    inventory = section.split("```text\n", 1)[1].split("\n```", 1)[0]
    assert inventory.splitlines() == [
        "initialize", "accept", "repair", "replan", "terminal_reject",
        "block", "redeliver", "cancel",
    ], "rw0.c2b: unchanged closed decision kinds"
    assert "The cancel-decision transaction creates only one immutable decision" in source
    assert (
        "cancel_effect:\n  exact cancel decision that preassigned the cancellation effect, fence, and\n  first delivery and named the exact target"
    ) in source, "rw0.c2b: exact pre-effect cancel basis"
    assert "Consumption is atomic with the first accepted productive direct-local\ndecision." in source, (
        "rw0.c2b: accept decision owns atomic latch consumption"
    )
    assert "A recorded but unestablished cancel\ndecision bound to an older version remains immutable history but cannot\nestablish its effect; a new current-version decision is required." in source, (
        "rw0.c2b: stale cancel decision cannot establish effect"
    )


def _assert_rw0_terminal_outcome_contract(body: str) -> None:
    compact = _compact(body)
    missing = [
        name for name, phrase, _mutant in RW0_TERMINAL_OUTCOME_REQUIREMENTS
        if _compact(phrase) not in compact
    ]
    assert not missing, "RW0_TERMINAL_OUTCOME_CONTRACT_MISSING:" + ",".join(missing)
    contradictions = [
        name for name, sentence in RW0_TERMINAL_OUTCOME_CONTRADICTIONS
        if _compact(sentence) in compact
    ]
    assert not contradictions, "RW0_TERMINAL_OUTCOME_CONTRADICTION:" + ",".join(contradictions)


def _assert_repair_semantics(body: str) -> None:
    compact = _compact(body)
    missing = [
        name
        for name, phrase in REPAIR_SEMANTIC_REQUIREMENTS
        if _compact(phrase) not in compact
    ]
    if "RW0 permits exactly one actual delivery and no second delivery or relaunch." in compact:
        missing.append("one_total_delivery_conflict")
    if "The target requires one authenticated bounded contact and one actual delivery." in compact:
        missing.append("one_total_contact_conflict")
    assert not missing, "RW0_REPAIR_CONTRACT_MISSING:" + ",".join(missing)


def _validate_owner(text: str) -> None:
    body = _owner_visible_body(text)

    required = (
        "Classification: ACCEPTED STRATEGIC TARGET; not current implementation.",
        "RW0-A is a docs-and-contract-tests-only freeze.",
        "Current executable authorization remains unsupported and fail-closed.",
        "No phase-entry, verifier, custody, adapter, supervisor, worker, Codex invocation, capsule store, validation or review executor, model invocation, post-execution decision or terminal-outcome runtime, acceptance latch, Git effect, ES route, service, queue, scheduler, or autonomous loop is implemented.",
        "Reports, model output, topology and readiness profiles, transport receipts, and artifacts remain evidence only.",
        "VS1B route-neutral genesis commits nine physical rows and eight graph entries.",
        "C2B3D author-effect establishment commits ten physical rows and nine graph entries, including one pending authority evaluation and one inert planned initial delivery.",
        "Section 41 selection is causally later than C2B3D and does not advance the effect or delivery heads.",
        "K8 plus the exact current L34 and selection-head postimage is necessary, but it is not launch authority.",
        "selected_for_dispatch_gates is planning state, not executable permission.",
        "The first productive proof is a docs/docs-contract-only change with a maximum three-path ceiling.",
        "Base or path drift requires replan and a new WorkSpec; it is never absorbed.",
        "At most one productive direct-local acceptance is permitted.",
        "Every terminal outcome ends RW0, and repair or replan never launches a successor in RW0.",
        "RW0 performs no Git effect and no publication.",
        "The external standing-policy authority authors the immutable parent grant, revocation and expiry directives, applicable global-stop directives, and effect ceilings.",
        "Coordinator never mints, renews, widens, reinterprets, or outlives the parent grant and never becomes an independent grant issuer.",
        "A schema, digest, ref, report, readiness result, or model output is never execution permission.",
        "Raw WorkSpec and selected-plan bytes never enter Coordinator SQLite, reports, argv, environment, logs, capsules, or public errors.",
        "A safe ref or digest is not retrieval permission.",
        "Retrieval is one-use, expiring, revocable, out of band, and bound to the exact attempt, effect, and audience.",
        "Crash or restart discards the bearer and never reuses it.",
        "The exact custodian, broker, backend, capability issuer, bearer transport, and credential mechanism remain deferred.",
        "Standing operator provisioning is only a bounded proof candidate; the user is not a synchronous per-attempt approver and this candidate is not enduring architecture.",
        "The target uses one owner-neutrally qualified remote Linux host.",
        "There is no Mac, Coordinator-host, or alternate-host fallback and no third adapter kind.",
        "direct_local_bootstrap remains only the compatibility route token.",
        "A host-key-pinned SSH forced command is only a preferred future proof candidate; it is not governing architecture in RW0-A.",
        "RW0-A does not freeze length-prefix framing, exact frame encoding, terminal-result grammar, or numeric caps.",
        "No adapter, supervisor, worker, builder, store, validator, reviewer, or model adapter receives Coordinator SQLite or writer authority.",
        "Delivery, source invocation, observation, candidate, capsule, validation, review, model proposal, C2B decision, RW0 terminal outcome, and Git effect remain distinct facts.",
        "Validator and reviewer evidence, model output, reports, IM evidence, and transport receipts are non-authoritative evidence.",
        "The immutable C2B accept decision consumes the productive-direct-local acceptance latch atomically in the same guarded Coordinator writer transaction; no terminal-outcome fact is a prerequisite for that latch mutation.",
        "No Git effect follows the RW0 terminal outcome.",
        "Migration 0004, its tables and receipts, application-generation treatment, terminal-outcome representation, and acceptance-latch representation are not implemented or selected by RW0-A.",
        "No open decision blocks RW0-A.",
    )
    _require_phrases(body, required, role="rw0.owner")
    _assert_repair_semantics(body)
    _assert_rw0_terminal_outcome_contract(body)

    k8_line = "K8 field inventory, in order: " + ", ".join(K8_FIELDS) + "."
    assert _compact(k8_line) in _compact(body)
    _validate_terminal_outcome_regions(text)

    for identity in (
        "program/work",
        "semantic attempt/candidate",
        "author effect intent/command/fences",
        "existing author delivery attempt",
        "later current effects and deliveries",
        "Section 41 proposal/disposition/head",
        "phase-entry/contact claim",
        "authority/host/custody gates",
        "source invocation and observation",
        "capsule manifest/portable digest/custody",
        "validation/review",
        "model proposal",
        "C2B development decision",
        "RW0 terminal outcome and one-way acceptance latch",
    ):
        assert identity in body, f"rw0.owner: missing identity role {identity}"

    for phase in (
        "pre-contact reconstruction",
        "phase-entry claim",
        "fresh authority, host, and custody gates",
        "one-use retrieval",
        "pre-send claim",
        "one actual author-candidate delivery",
        "process launch and worker start observations",
        "candidate capture and capsule seal",
        "validation observation",
        "independent review observation",
        "typed model proposal",
        "Coordinator semantic decision",
        "possible latch consumption",
        "RW0 terminal outcome",
        "teardown and custody terminal facts",
    ):
        assert phase in body, f"rw0.owner: missing timeline phase {phase}"

    for failure in (
        "phase-entry commit uncertainty",
        "stale, missing, or ambiguous authority or host gate",
        "retrieval failure or unknown consumption",
        "delivery rejection or unknown acceptance",
        "process start, exit, or deadline ambiguity",
        "candidate capture or capsule seal ambiguity",
        "validation, review, or model inconclusive outcome",
        "C2B decision commit uncertainty",
        "pre-effect cancel basis unusable after decision readback",
        "accepted decision committed, terminal outcome uncertain",
        "RW0 terminal-outcome commit uncertainty",
        "cleanup or custody ambiguity",
    ):
        assert failure in body, f"rw0.owner: missing failure row {failure}"

    cancellation_order = (
        "pre-effect C2B cancel decision → cancellation effect/fence/"
        "subordinate binding/delivery → request → acknowledgement → signal → "
        "process exit → workspace teardown → source-native reconciliation → "
        "RW0 terminal-outcome cancel or block"
    )
    assert cancellation_order in body

    for tranche in (
        "RW0-A — phase-entry contract freeze",
        "RW0-B — pure protocol and value contracts",
        "RW0-C — durable phase-entry and observation state",
        "RW0-D — offline worker, supervisor, and capsule proof",
        "RW0-E — one live qualified-host proof",
    ):
        assert tranche in body, f"rw0.owner: missing tranche {tranche}"
    offsets = [body.index(f"RW0-{letter} —") for letter in "ABCDE"]
    assert offsets == sorted(offsets), "rw0.owner: tranche order"

    for open_decision in (
        "verifier deployment, trust root, grant encoding, and revocation transport",
        "custodian and capability issuance",
        "Codex CLI versus App Server",
        "host-observation authenticity and sandbox technology",
        "exact framing and terminal-result grammar",
        "migration-0004 table, receipt, and application-generation design",
        "acceptance-latch representation",
        "capsule backend, encryption, retention, and garbage collection",
        "validator, reviewer, and model-adapter implementation",
        "ES reliable-submit and public recovery",
    ):
        assert open_decision in body, f"rw0.owner: open decision {open_decision}"

    forbidden = (
        "The Coordinator currently implements remote worker contact.",
        "The external authority derives the subordinate attempt/effect authorization.",
        "The user approves every attempt synchronously.",
        "A safe ref or digest grants retrieval permission.",
        "The ES fixture is an enduring Coordinator contract.",
        "Base drift is absorbed into the existing WorkSpec.",
        "SSH forced command is the governing target transport.",
        "Length-prefix framing is the governing target frame.",
        "Mac fallback is permitted.",
        "Coordinator-host fallback is permitted.",
        "A third adapter kind is permitted.",
        "A second RW0 delivery is permitted.",
        "A worker relaunch is permitted in RW0.",
        "A second productive direct-local acceptance is permitted.",
        "Validation, review, and model proposal are the Coordinator decision.",
        "Model, report, IM, or transport evidence is authoritative progression truth.",
        "Direct-local owns ES runtime lifecycle.",
        "RW0 includes a Git effect or publication.",
        "Repair or replan launches a successor in RW0.",
        "Cancellation acknowledgement proves process exit and semantic cancellation.",
        "Migration 0004 and the RW0 runtime are currently implemented.",
    )
    for claim in forbidden:
        assert claim not in body, f"rw0.owner: forbidden claim: {claim}"


def test_one_authoritative_owner_and_unique_markers() -> None:
    owner = _owner_text()
    begin, end, _headings, _visible = _visible_marker_span(
        owner, CONTRACT_BEGIN, CONTRACT_END, role="rw0.owner"
    )
    hidden_begin = owner.replace(CONTRACT_BEGIN, f"~~~\n{CONTRACT_BEGIN}\n~~~", 1)
    assert _broken_raw_marker_extractor(hidden_begin, CONTRACT_BEGIN, CONTRACT_END)
    with pytest.raises(AssertionError, match="rw0.owner: one visible marker pair"):
        _owner_visible_body(hidden_begin)
    hidden_end = owner.replace(CONTRACT_END, f"~~~\n{CONTRACT_END}\n~~~", 1)
    with pytest.raises(AssertionError, match="rw0.owner: one visible marker pair"):
        _owner_visible_body(hidden_end)
    hidden_duplicate = owner + f"\n~~~\n{CONTRACT_BEGIN}\n{CONTRACT_END}\n~~~\n"
    assert _owner_visible_body(hidden_duplicate) == _owner_visible_body(owner)
    visible_duplicate = owner + f"\n{CONTRACT_BEGIN}\n{CONTRACT_END}\n"
    with pytest.raises(AssertionError, match="rw0.owner: one visible marker pair"):
        _owner_visible_body(visible_duplicate)
    live_prose = "This region authorizes a second author attempt and immediate worker launch."
    unexpected_acceptances = []
    for label, mutant in (
        ("owner leading prose", owner.replace(CONTRACT_BEGIN, live_prose + "\n" + CONTRACT_BEGIN, 1)),
        ("owner trailing prose", owner + "\n" + live_prose + "\n"),
    ):
        assert _broken_raw_marker_extractor(mutant, CONTRACT_BEGIN, CONTRACT_END)
        try:
            _owner_visible_body(mutant)
        except AssertionError:
            pass
        else:
            unexpected_acceptances.append(label)
    assert not unexpected_acceptances, f"visible owner prose escaped markers: {unexpected_acceptances}"
    real_block = owner[begin[0] : end[0] + len(end[1])]
    empty_visible_owner = (
        owner[:begin[0]] + "~~~\n" + real_block + "\n~~~\n"
        + CONTRACT_BEGIN + "\n\n" + CONTRACT_END
        + owner[end[0] + len(end[1]) :]
    )
    assert _compact(_broken_raw_first_body(empty_visible_owner, CONTRACT_BEGIN, CONTRACT_END)) == _compact(_broken_raw_first_body(owner, CONTRACT_BEGIN, CONTRACT_END))
    with pytest.raises(AssertionError):
        _owner_visible_body(empty_visible_owner)
    assert _owner_visible_body(owner + "\n<!-- irrelevant hidden comment -->\n") == _owner_visible_body(owner)
    multiline_hidden_owner = owner.replace(
        CONTRACT_BEGIN, "<!--\n## Hidden historical owner\n-->\n" + CONTRACT_BEGIN, 1
    )
    assert _owner_visible_body(multiline_hidden_owner) == _owner_visible_body(owner)
    reversed_pair = owner[:begin[0]] + CONTRACT_END + owner[begin[0] + len(begin[1]):end[0]] + CONTRACT_BEGIN + owner[end[0] + len(end[1]):]
    with pytest.raises(AssertionError, match="rw0.owner: marker order"):
        _owner_visible_body(reversed_pair)
    split_pair = owner.replace(CONTRACT_BEGIN, "", 1).replace(
        "## Authority model", CONTRACT_BEGIN + "\n\n## Authority model", 1
    )
    with pytest.raises(AssertionError):
        _owner_visible_body(split_pair)
    outside_owner = owner.replace(CONTRACT_BEGIN, "", 1).replace(
        "# RW0 Remote-Contact Phase-Entry Operating Model",
        CONTRACT_BEGIN + "\n# RW0 Remote-Contact Phase-Entry Operating Model",
        1,
    )
    with pytest.raises(AssertionError, match="rw0.owner: marker before root"):
        _owner_visible_body(outside_owner)
    _validate_owner(owner)
    all_documents = tuple((ROOT / ".docs").glob("*.md"))
    begin_owners = [
        path
        for path in all_documents
        if any(
            line.lstrip(" ") == CONTRACT_BEGIN
            for _position, line in _visible_markdown_lines_and_headings(path.read_text())[1]
        )
    ]
    end_owners = [
        path
        for path in all_documents
        if any(
            line.lstrip(" ") == CONTRACT_END
            for _position, line in _visible_markdown_lines_and_headings(path.read_text())[1]
        )
    ]
    assert begin_owners == [ROOT / OWNER_PATH]
    assert end_owners == [ROOT / OWNER_PATH]


def test_four_supporting_cross_references_are_unique_and_normalized() -> None:
    live_map = {path: _text(path) for path, _root in CROSS_REFERENCE_OWNERS}
    live_body = _assert_complete_rw0_cross_reference_map(live_map)

    def mapped(path: str, candidate: str) -> str:
        mutated = dict(live_map)
        mutated[path] = candidate
        return _assert_complete_rw0_cross_reference_map(mutated)

    def reject_map(path: str, candidate: str, match: str | None = None) -> None:
        with pytest.raises(AssertionError, match=match):
            mapped(path, candidate)

    bodies: list[str] = []
    unexpected_acceptances: list[str] = []
    for path, root_title in CROSS_REFERENCE_OWNERS:
        text = live_map[path]
        body = _cross_reference_visible_body(path, text, root_title)
        bodies.append(_compact(body))
        begin, end, _headings, _visible = _visible_marker_span(
            text, CROSS_REFERENCE_BEGIN, CROSS_REFERENCE_END, role=path
        )
        block = text[begin[0] : end[0] + len(end[1])]
        heading_inside = CROSS_REFERENCE_BEGIN + "\n### " + CROSS_REFERENCE_HEADING
        assert heading_inside in block
        heading_outside = text[:begin[0]] + block.replace(
            heading_inside,
            "### " + CROSS_REFERENCE_HEADING + "\n" + CROSS_REFERENCE_BEGIN,
            1,
        ) + text[end[0] + len(end[1]) :]
        assert _compact(_cross_reference_visible_body(path, heading_outside, root_title)) == _compact(
            body.replace("### " + CROSS_REFERENCE_HEADING, "", 1)
        )
        reject_map(path, heading_outside, "body mismatch")
        hidden_duplicate = text + "\n~~~\n" + block + "\n~~~\n"
        assert _cross_reference_visible_body(path, hidden_duplicate, root_title) == body
        assert mapped(path, hidden_duplicate) == live_body
        two_visible = text + "\n" + block + "\n"
        with pytest.raises(AssertionError, match="one visible marker pair"):
            _cross_reference_visible_body(path, two_visible, root_title)
        reject_map(path, two_visible, "one visible marker pair")
        live_prose = "This region authorizes a second author attempt and immediate worker launch."
        for fence in ("~~~", "```"):
            empty_visible_block = (
                text[:begin[0]] + "### " + CROSS_REFERENCE_HEADING + "\n"
                + fence + "\n" + block + "\n" + fence + "\n"
                + CROSS_REFERENCE_BEGIN + "\n\n" + CROSS_REFERENCE_END
                + text[end[0] + len(end[1]) :]
            )
            assert _compact(
                _broken_raw_first_body(
                    empty_visible_block, CROSS_REFERENCE_BEGIN, CROSS_REFERENCE_END
                )
            ) == _compact(body)
            with pytest.raises(AssertionError, match="empty visible owner body"):
                _cross_reference_visible_body(path, empty_visible_block, root_title)
            reject_map(path, empty_visible_block, "empty visible owner body")
        for label, mutant in (
            ("leading prose", text[:begin[0]] + live_prose + "\n" + text[begin[0]:]),
            ("trailing prose", text + "\n" + live_prose + "\n"),
        ):
            try:
                mapped(path, mutant)
            except AssertionError:
                pass
            else:
                unexpected_acceptances.append(f"{path}: {label}")
        assert mapped(path, text + "\n<!-- irrelevant hidden comment -->\n") == live_body
        multiline_hidden_cross = text + "\n<!--\n### " + CROSS_REFERENCE_HEADING + "\n-->\n"
        assert mapped(path, multiline_hidden_cross) == live_body
        fenced_only = text[:begin[0]] + "~~~\n" + block + "\n~~~" + text[end[0] + len(end[1]) :]
        assert _compact(_broken_raw_marker_extractor(fenced_only, CROSS_REFERENCE_BEGIN, CROSS_REFERENCE_END)) == _compact(body)
        with pytest.raises(AssertionError, match="one visible marker pair"):
            _cross_reference_visible_body(path, fenced_only, root_title)
        reject_map(path, fenced_only, "one visible marker pair")
        empty_h3_hidden_body = text[:begin[0]] + "### " + CROSS_REFERENCE_HEADING + "\n~~~\n" + block + "\n~~~" + text[end[0] + len(end[1]) :]
        assert _compact(_broken_raw_marker_extractor(empty_h3_hidden_body, CROSS_REFERENCE_BEGIN, CROSS_REFERENCE_END)) == _compact(body)
        with pytest.raises(AssertionError, match="one visible marker pair"):
            _cross_reference_visible_body(path, empty_h3_hidden_body, root_title)
        reject_map(path, empty_h3_hidden_body, "one visible marker pair")
        historical = text.replace(block, "", 1).replace(
            "## " + CROSS_REFERENCE_PARENT,
            block + "\n## " + CROSS_REFERENCE_PARENT,
            1,
        )
        with pytest.raises(AssertionError):
            _cross_reference_visible_body(path, historical, root_title)
        reject_map(path, historical)
        same_title_sibling = text.replace(
            "## " + CROSS_REFERENCE_PARENT,
            "## " + CROSS_REFERENCE_PARENT + "\n### " + CROSS_REFERENCE_HEADING
            + "\n\n## " + CROSS_REFERENCE_PARENT,
            1,
        )
        with pytest.raises(AssertionError):
            _cross_reference_visible_body(path, same_title_sibling, root_title)
        reject_map(path, same_title_sibling)
        same_title_ancestor = text.replace(
            "# " + root_title,
            "# " + root_title + "\n### " + CROSS_REFERENCE_HEADING,
            1,
        )
        with pytest.raises(AssertionError):
            _cross_reference_visible_body(path, same_title_ancestor, root_title)
        reject_map(path, same_title_ancestor)
        split_markers = text.replace(
            CROSS_REFERENCE_END, "## Detached owner\n" + CROSS_REFERENCE_END, 1
        )
        with pytest.raises(AssertionError):
            _cross_reference_visible_body(path, split_markers, root_title)
        reject_map(path, split_markers)
        reversed_markers = (
            text.replace(CROSS_REFERENCE_BEGIN, "__RW0_BEGIN__", 1)
            .replace(CROSS_REFERENCE_END, CROSS_REFERENCE_BEGIN, 1)
            .replace("__RW0_BEGIN__", CROSS_REFERENCE_END, 1)
        )
        reject_map(path, reversed_markers)
        body_mismatch = text.replace(
            "A separate future Coordinator-owned durable RW0 terminal-outcome fact closes each run",
            "A different future Coordinator-owned durable RW0 terminal-outcome fact closes each run",
            1,
        )
        assert body_mismatch != text
        _cross_reference_visible_body(path, body_mismatch, root_title)
        reject_map(path, body_mismatch, "body mismatch")
    assert len(set(bodies)) == 1
    assert not unexpected_acceptances, f"visible cross-reference body escaped markers: {unexpected_acceptances}"
    _require_phrases(
        bodies[0],
        (
            f"{OWNER_PATH} is the sole detailed owner.",
            "Current implementation stops at private C2B3D planned author delivery plus Section 41 pre-execution selection; executable contact and terminal-outcome runtime remain unsupported and fail-closed.",
            "RW0 target begins with a receipt-backed no-contact phase-entry fact and fresh authority, host, and custody gates.",
            "External standing-policy authority owns the parent grant; Coordinator target derives a separate narrower subordinate authorization record only inside that freshly verified grant.",
            "No current custody, adapter, supervisor, worker, capsule, validation, review, model, post-execution decision, terminal-outcome, latch, Git, or publication runtime exists.",
            "Direct-local permits one qualified remote Linux host, exactly the existing author attempt, effect, command, candidate, and initial delivery, with at most one author invocation and actual author delivery; reached validation, review, and cancellation use distinct current effects and deliveries.",
            "Existing author attempt/effect fences retain exact externally authored per-fence authorization-basis refs/digests",
            "The existing C2B `cancel` decision commits before the cancellation effect",
            "A separate future Coordinator-owned durable RW0 terminal-outcome fact closes each run",
            "The accepted direct-local C2B decision alone atomically consumes the one-way latch in its guarded writer transaction; the later terminal-outcome `accept` binds that exact decision ref/digest and committed latch postimage without another latch mutation.",
            "an unusable pre-effect cancel basis establishes no effect, fence, delivery, request, or signal and commits terminal-outcome `block` bound to the exact unusable decision and mismatch evidence, without another C2B decision.",
            "terminal-outcome `cancel` only when complete and unambiguous or terminal-outcome `block` otherwise without another C2B decision",
            "Direct-local route-local process and cancellation ownership does not absorb ES-route authority",
            "Exact custodian, transport, framing, Codex seam, schema, terminal-outcome representation, latch, and physical backends remain deferred.",
        ),
        role="rw0.cross_reference",
    )


def test_c2b_is_append_only_and_section_42_remains_final_h2() -> None:
    payload = (ROOT / C2B_PATH).read_bytes()
    opening = payload[:C2B_OPENING_SIZE]
    assert len(opening) == C2B_OPENING_SIZE
    assert hashlib.sha256(opening).hexdigest() == C2B_OPENING_SHA256
    text = payload.decode("utf-8")
    begin, _end, headings, visible = _visible_marker_span(
        text, C2B_CROSS_REFERENCE_BEGIN, C2B_CROSS_REFERENCE_END,
        role="rw0.c2b_cross_reference",
    )
    status_ends = tuple(
        position for position, line in visible if line.lstrip(" ") == COMMITTED_STATUS_END
    )
    assert len(status_ends) == 1 and begin[0] > status_ends[0]
    body = _extract_unique(
        text,
        C2B_CROSS_REFERENCE_BEGIN,
        C2B_CROSS_REFERENCE_END,
        role="rw0.c2b_cross_reference",
    )
    assert body.startswith("### RW0 remote-contact phase-entry target boundary")
    _require_phrases(
        body,
        (
            "accepted strategic target, not current implementation",
            f"{OWNER_PATH} is the sole detailed owner",
            "Section 41 remains the sole detailed pre-execution selection semantic owner",
            "K8 plus the exact current L34 and head postimage is necessary but is not launch authority",
            "No phase-entry, verifier, custody, worker, capsule, validation, review, model proposal, decision runtime, latch, Git, or publication capability is implemented",
            "No table, row, receipt, graph, migration, application-generation, or public API representation is selected",
            "The pre-existing Section 42 bytes and exact-column-order owner remain unchanged",
        ),
        role="rw0.c2b_cross_reference",
    )
    h2_headings = tuple(title for level, title, _start, _end in headings if level == 2)
    assert h2_headings[-1].startswith("42. ")
    assert not any(heading.startswith("43.") for heading in h2_headings)


def test_k8_matches_static_source_and_l34_is_not_redefined() -> None:
    owner = _owner_text()
    source = _text(SELECTION_SOURCE_PATH)
    assert _parse_literal_tuple(source, "_K8_FIELDS") == K8_FIELDS
    assert "K8 field inventory, in order: " + ", ".join(K8_FIELDS) + "." in owner
    assert "The unchanged Section 41 source remains the sole exact L34 inventory authority." in owner
    assert "L34 field inventory, in order:" not in owner


def test_fixture_is_explicitly_non_authoritative_and_stale_able() -> None:
    owner = _owner_text()
    appendix = owner.split("## Non-authoritative initial proof fixture candidate", 1)[1]
    assert "b92bd9884106154d25342e1573dcc4c312311436" in appendix
    for path in (
        "PLANS.md",
        ".docs/system_overview/hybrid_integration_architecture_adr.md",
        "docs_contract_test.go",
    ):
        assert path in appendix
    _require_phrases(
        appendix,
        (
            "stale-able evidence only",
            "not a durable Coordinator contract",
            "not execution permission",
            "not a required future base or path set",
            "Immediately before RW0-E, the exact base and paths must be selected and verified again.",
        ),
        role="rw0.fixture",
    )


def test_identity_timeline_failure_and_decision_inventories_are_complete() -> None:
    owner = _owner_text()
    c2b_source = _text(".docs/c2b-durable-development-state.md")
    _assert_c2b_cancel_source_contract(c2b_source)
    for c2b_mutant in (
        c2b_source.replace("cancel\n```", "cancel\nterminal_outcome\n```", 1),
        c2b_source.replace(
            "cancel_effect:\n  exact cancel decision",
            "cancel_effect:\n  terminal-outcome fact",
            1,
        ),
        c2b_source.replace(
            "Consumption is atomic with the first accepted productive direct-local\ndecision.",
            "Consumption waits until the terminal-outcome fact commits.",
            1,
        ),
        c2b_source.replace(
            "decision bound to an older version remains immutable history but cannot\nestablish its effect; a new current-version decision is required.",
            "decision bound to an older version may establish its effect without a new decision.",
            1,
        ),
    ):
        assert c2b_mutant != c2b_source
        with pytest.raises(AssertionError, match="rw0.c2b"):
            _assert_c2b_cancel_source_contract(c2b_mutant)
    inventory = "Terminal outcomes: " + ", ".join(TERMINAL_OUTCOMES) + "."
    for heading, role in (
        ("Bounded RW0 scenario class", "scenario"),
        ("Capsule, validation, review, model, and decision", "decision"),
    ):
        start, end, lines = _terminal_outcome_owner_range(
            owner, heading=heading, role=role
        )
        assert sum(line.startswith("Terminal outcomes:") for line in lines) == 1
        position = owner.index(inventory, start, end) + len(inventory)
        mutant = (
            owner[:position]
            + "\n  Terminal outcomes: accept, repair, replan, terminal_reject, block, retry."
            + owner[position:]
        )
        _mutant_start, _mutant_end, mutant_lines = _terminal_outcome_owner_range(
            mutant, heading=heading, role=role
        )
        assert sum(line.startswith("Terminal outcomes:") for line in mutant_lines) == 1, (
            f"rw0.outcomes.{role}: broken column-zero predecessor control"
        )
        assert sum(
            line.lstrip(" ").startswith("Terminal outcomes:")
            for line in mutant_lines
        ) == 2, f"rw0.outcomes.{role}: visible indented duplicate"
    _validate_owner(owner)
    outcome_body = _owner_visible_body(owner)
    for name, phrase, mutant in RW0_TERMINAL_OUTCOME_REQUIREMENTS:
        assert _compact(phrase) in _compact(outcome_body), name
        candidate = _compact(outcome_body).replace(_compact(phrase), mutant, 1)
        assert candidate != _compact(outcome_body)
        with pytest.raises(AssertionError, match=name):
            _assert_rw0_terminal_outcome_contract(candidate)
    for name, sentence in RW0_TERMINAL_OUTCOME_CONTRADICTIONS:
        candidate = outcome_body + "\n" + sentence
        with pytest.raises(AssertionError, match=name):
            _assert_rw0_terminal_outcome_contract(candidate)
    for heading, role in (
        ("Bounded RW0 scenario class", "scenario"),
        ("Capsule, validation, review, model, and decision", "decision"),
    ):
        start, end, _lines = _terminal_outcome_owner_range(
            owner, heading=heading, role=role
        )
        position = owner.index(inventory, start, end) + len(inventory)
        mutant = owner[:position] + "\n  " + inventory + owner[position:]
        with pytest.raises(AssertionError, match=f"rw0.outcomes.{role}: exactly"):
            _validate_terminal_outcome_regions(mutant)
    sibling_inventory = owner.replace(
        "## Authority model",
        "## Authority model\n\n  " + inventory,
        1,
    )
    with pytest.raises(AssertionError, match="rw0.outcomes: no sibling"):
        _validate_terminal_outcome_regions(sibling_inventory)
    body = _owner_visible_body(owner)
    assert set(REPAIR_SEMANTIC_MUTANTS) == {
        name for name, _phrase in REPAIR_SEMANTIC_REQUIREMENTS
    }
    for name, phrase in REPAIR_SEMANTIC_REQUIREMENTS:
        assert _compact(phrase) in _compact(body), name
        mutant = _compact(body).replace(
            _compact(phrase), REPAIR_SEMANTIC_MUTANTS[name], 1
        )
        assert mutant != _compact(body)
        with pytest.raises(
            AssertionError,
            match=name if name in EXISTING_REPAIR_DIAGNOSTIC_NAMES else None,
        ):
            _assert_repair_semantics(mutant)

    def bounded_mutant(heading: str, next_heading: str, old: str, new: str) -> str:
        start = owner.index("## " + heading)
        end = owner.index("## " + next_heading, start)
        region = owner[start:end]
        assert region.count(old) == 1, (heading, old)
        return owner[:start] + region.replace(old, new, 1) + owner[end:]

    requirements = dict(REPAIR_SEMANTIC_REQUIREMENTS)
    for name in (
        "exact_author_lineage",
        "no_second_attempt",
        "no_second_effect",
        "no_second_command",
        "no_second_candidate",
        "no_second_invocation",
        "no_author_relaunch_or_redelivery",
    ):
        candidate = bounded_mutant(
            "Bounded RW0 scenario class", "Authority model",
            requirements[name], REPAIR_SEMANTIC_MUTANTS[name],
        )
        with pytest.raises(AssertionError):
            _validate_owner(candidate)

    basis = requirements["per_fence_basis_equality"]
    authority_mutants = (
        (basis, basis.replace("authorization-basis reference and digest byte-for-byte", "a substituted attempt authorization-basis reference")),
        (basis, basis.replace("authorization-basis reference and digest byte-for-byte", "a substituted author-effect authorization-basis digest")),
        (requirements["immutable_external_basis"], REPAIR_SEMANTIC_MUTANTS["immutable_external_basis"]),
        (requirements["separate_subordinate_record"], REPAIR_SEMANTIC_MUTANTS["separate_subordinate_record"]),
        (requirements["verified_basis_family"], REPAIR_SEMANTIC_MUTANTS["verified_basis_family"]),
        (requirements["basis_pairs_need_not_equal"], REPAIR_SEMANTIC_MUTANTS["basis_pairs_need_not_equal"]),
        (requirements["incompatible_basis_blocks"], REPAIR_SEMANTIC_MUTANTS["incompatible_basis_blocks"]),
        (requirements["subordinate_existing_binding"], REPAIR_SEMANTIC_MUTANTS["subordinate_existing_binding"]),
        (requirements["later_subordinate_bindings"], REPAIR_SEMANTIC_MUTANTS["later_subordinate_bindings"]),
        (requirements["immutable_external_basis"], "Existing author fences alone authorize launch."),
        ("The external standing-policy authority authors the immutable parent grant", "Coordinator authors the immutable parent grant"),
    )
    for old, new in authority_mutants:
        assert old != new
        candidate = bounded_mutant("Authority model", "WorkSpec and selected-plan custody", old, new)
        with pytest.raises(AssertionError):
            _validate_owner(candidate)

    chain = (
        "pre-effect C2B cancel decision → cancellation effect/fence/"
        "subordinate binding/delivery → request → acknowledgement → signal → "
        "process exit → workspace teardown → source-native reconciliation → "
        "RW0 terminal-outcome cancel or block"
    )
    cancellation_mutants = (
        (chain, chain.replace("workspace teardown → source-native reconciliation", "workspace teardown")),
        (chain, chain.replace("workspace teardown → source-native reconciliation", "source-native reconciliation → workspace teardown")),
        (requirements["ambiguous_reconciliation_blocks"], "Ambiguous source reconciliation produces terminal-outcome cancel."),
        (requirements["ambiguous_reconciliation_blocks"], "Unresolved reconciliation has no block result."),
        (requirements["early_control_not_final"], "A second post-teardown C2B cancel decision establishes terminal closure."),
        (requirements["one_final_decision"], "RW0 may commit two terminal-outcome facts."),
        (requirements["normal_has_no_cancel_control"], "The non-cancel branch commits a cancellation-control decision."),
        (requirements["early_control_not_final"], "The pre-effect cancel decision alone consumes the acceptance latch."),
        (requirements["reconciliation_not_decision"], "Source reconciliation itself commits terminal outcome."),
    )
    for old, new in cancellation_mutants:
        section, following = (
            ("Failure, ambiguity, cancellation, and recovery", "Capsule, validation, review, model, and decision")
            if old == chain else
            ("Bounded RW0 scenario class", "Authority model")
            if old in (requirements["early_control_not_final"], requirements["one_final_decision"], requirements["normal_has_no_cancel_control"])
            else ("Target fact timeline", "Failure, ambiguity, cancellation, and recovery")
        )
        candidate = bounded_mutant(section, following, old, new)
        with pytest.raises(AssertionError):
            _validate_owner(candidate)


@pytest.mark.parametrize(
    ("case", "required", "mutant"),
    (
        (
            "current_worker_capability",
            "No phase-entry, verifier, custody, adapter, supervisor, worker, Codex invocation, capsule store, validation or review executor, model invocation, post-execution decision runtime, acceptance latch, Git effect, ES route, service, queue, scheduler, or autonomous loop is implemented.",
            "The Coordinator currently implements remote worker contact.",
        ),
        (
            "external_subordinate_authorization",
            "Coordinator—not the external standing-policy authority—derives only narrower subordinate attempt/effect authorization records and issues attempt/effect fences inside the freshly verified parent grant.",
            "The external authority derives the subordinate attempt/effect authorization.",
        ),
        (
            "user_per_attempt_approval",
            "Standing operator provisioning is only a bounded proof candidate; the user is not a synchronous per-attempt approver and this candidate is not enduring architecture.",
            "The user approves every attempt synchronously.",
        ),
        (
            "safe_ref_permission",
            "A safe ref or digest is not retrieval permission.",
            "A safe ref or digest grants retrieval permission.",
        ),
        (
            "fixture_enduring",
            "stale-able evidence only",
            "The ES fixture is an enduring Coordinator contract.",
        ),
        (
            "absorb_base_drift",
            "Base or path drift requires replan and a new WorkSpec; it is never absorbed.",
            "Base drift is absorbed into the existing WorkSpec.",
        ),
        (
            "ssh_frozen",
            "A host-key-pinned SSH forced command is only a preferred future proof candidate; it is not governing architecture in RW0-A.",
            "SSH forced command is the governing target transport.",
        ),
        (
            "length_prefix_frozen",
            "RW0-A does not freeze length-prefix framing, exact frame encoding, terminal-result grammar, or numeric caps.",
            "Length-prefix framing is the governing target frame.",
        ),
        (
            "mac_fallback",
            "There is no Mac, Coordinator-host, or alternate-host fallback and no third adapter kind.",
            "Mac fallback is permitted.",
        ),
        (
            "coordinator_host_fallback",
            "There is no Mac, Coordinator-host, or alternate-host fallback and no third adapter kind.",
            "Coordinator-host fallback is permitted.",
        ),
        (
            "third_adapter",
            "There is no Mac, Coordinator-host, or alternate-host fallback and no third adapter kind.",
            "A third adapter kind is permitted.",
        ),
        (
            "second_delivery",
            "RW0 permits exactly one actual delivery and no second delivery or relaunch.",
            "A second RW0 delivery is permitted.",
        ),
        (
            "worker_relaunch",
            "RW0 permits exactly one actual delivery and no second delivery or relaunch.",
            "A worker relaunch is permitted in RW0.",
        ),
        (
            "second_acceptance",
            "At most one productive direct-local acceptance is permitted.",
            "A second productive direct-local acceptance is permitted.",
        ),
        (
            "collapse_decision_sources",
            "Delivery, source invocation, observation, candidate, capsule, validation, review, model proposal, Coordinator decision, and Git effect remain distinct facts.",
            "Validation, review, and model proposal are the Coordinator decision.",
        ),
        (
            "authoritative_evidence",
            "Validator and reviewer evidence, model output, reports, IM evidence, and transport receipts are non-authoritative evidence.",
            "Model, report, IM, or transport evidence is authoritative progression truth.",
        ),
        (
            "direct_local_owns_es",
            "Direct-local never owns ES admission, reliable submit, runtime lifecycle, cancellation, runtime identity or credentials, retained results, or route-owned correlations.",
            "Direct-local owns ES runtime lifecycle.",
        ),
        (
            "git_or_publication",
            "RW0 performs no Git effect and no publication.",
            "RW0 includes a Git effect or publication.",
        ),
        (
            "missing_terminal_outcome",
            "Terminal outcomes: accept, repair, replan, terminal_reject, block, cancel.",
            "Terminal outcomes: accept, repair, replan, terminal_reject, block.",
        ),
        (
            "successor_launch",
            "Every terminal outcome ends RW0, and repair or replan never launches a successor in RW0.",
            "Repair or replan launches a successor in RW0.",
        ),
        (
            "collapsed_cancellation",
            "decision/intent → cancellation effect/delivery → request → acknowledgement → signal → process exit → workspace teardown → semantic abandonment/cancellation",
            "Cancellation acknowledgement proves process exit and semantic cancellation.",
        ),
        (
            "implemented_migration_runtime",
            "Migration 0004, its tables and receipts, application-generation treatment, and acceptance-latch representation are not implemented or selected by RW0-A.",
            "Migration 0004 and the RW0 runtime are currently implemented.",
        ),
    ),
)
def test_causal_owner_mutants_fail(case: str, required: str, mutant: str) -> None:
    owner = _owner_text()
    red_required = {
        "external_subordinate_authorization": (
            "For each existing author fence, the subordinate record binds that fence's persisted authorization-basis reference and digest byte-for-byte and binds the exact existing fence reference and digest."
        ),
        "second_delivery": "No replacement or second semantic attempt occurs in RW0.",
        "collapsed_cancellation": "If active-cancel reconciliation is incomplete, contradictory, stale, or ambiguous, terminal-outcome block binds the same pre-effect cancel decision and unresolved evidence without a C2B block decision.",
        "second_acceptance": "The future guarded Coordinator writer commits exactly one durable RW0 terminal-outcome fact per run after outcome-specific evidence and current-head checks; it is not a development_decision, effect basis, executable permission, source observation, report, or projection.",
    }
    if case in red_required:
        assert red_required[case] in _compact(owner), f"missing repaired {case} contract"
    # Preserve the frozen parameter values and their collected node IDs.
    effective_required = {
        "current_worker_capability": (
            "No phase-entry, verifier, custody, adapter, supervisor, worker, Codex invocation, capsule store, validation or review executor, model invocation, post-execution decision or terminal-outcome runtime, acceptance latch, Git effect, ES route, service, queue, scheduler, or autonomous loop is implemented."
        ),
        "external_subordinate_authorization": (
            "Coordinator derives narrower subordinate authorization bound to "
            "the exact existing author attempt and effect fences only after "
            "fresh parent verification; it does not issue replacement author fences."
        ),
        "second_delivery": (
            "The existing author-candidate delivery identity permits exactly "
            "one actual author-candidate delivery in RW0."
        ),
        "worker_relaunch": (
            "The existing author-candidate delivery identity permits exactly "
            "one actual author-candidate delivery in RW0."
        ),
        "direct_local_owns_es": (
            "Direct-local never claims ES-route facts or creates a parallel "
            "ES lifecycle store."
        ),
        "collapsed_cancellation": (
            "pre-effect C2B cancel decision → cancellation effect/fence/"
            "subordinate binding/delivery → request → acknowledgement → signal → "
            "process exit → workspace teardown → source-native reconciliation → "
            "RW0 terminal-outcome cancel or block"
        ),
        "collapse_decision_sources": (
            "Delivery, source invocation, observation, candidate, capsule, validation, review, model proposal, C2B decision, RW0 terminal outcome, and Git effect remain distinct facts."
        ),
        "implemented_migration_runtime": (
            "Migration 0004, its tables and receipts, application-generation treatment, terminal-outcome representation, and acceptance-latch representation are not implemented or selected by RW0-A."
        ),
    }.get(case, required)
    assert effective_required in owner
    changed = owner.replace(effective_required, mutant, 1)
    assert changed != owner
    with pytest.raises(AssertionError):
        _validate_owner(changed)

    if case == "missing_terminal_outcome":
        scenario = "Bounded RW0 scenario class"
        decision = "Capsule, validation, review, model, and decision"
        _validate_terminal_outcome_regions(owner)
        controls = (
            (
                "scenario",
                changed,
                "rw0.outcomes.scenario",
            ),
            (
                "decision",
                _replace_owned_inventory(
                    owner,
                    heading=decision,
                    role="decision",
                    replacement=(
                        "Terminal outcomes: accept, replan, terminal_reject, "
                        "block, cancel."
                    ),
                ),
                "rw0.outcomes.decision",
            ),
        )
        for _role, candidate, diagnostic in controls:
            assert _broken_whole_document_outcome_checker(candidate)
            with pytest.raises(AssertionError, match=diagnostic):
                _validate_terminal_outcome_regions(candidate)

        additional_mutants = (
            (
                _replace_owned_inventory(
                    owner,
                    heading=scenario,
                    role="scenario",
                    replacement=(
                        "Terminal outcomes: repair, accept, replan, "
                        "terminal_reject, block, cancel."
                    ),
                ),
                "rw0.outcomes.scenario",
            ),
            (
                _replace_owned_inventory(
                    owner,
                    heading=decision,
                    role="decision",
                    replacement=(
                        "Terminal outcomes: accept, repair, replan, "
                        "terminal_reject, block, cancel, retry."
                    ),
                ),
                "rw0.outcomes.decision",
            ),
            (
                _replace_owned_inventory(
                    owner,
                    heading=scenario,
                    role="scenario",
                    replacement=(
                        "~~~text\nTerminal outcomes: accept, repair, replan, "
                        "terminal_reject, block, cancel.\n~~~"
                    ),
                ),
                "rw0.outcomes.scenario",
            ),
        )
        for candidate, diagnostic in additional_mutants:
            assert candidate != owner
            with pytest.raises(AssertionError, match=diagnostic):
                _validate_terminal_outcome_regions(candidate)
