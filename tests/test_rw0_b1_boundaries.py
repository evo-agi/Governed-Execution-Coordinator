"""B1 private source and privacy boundaries."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import NamedTuple

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
from test_rw0_b1_vectors import mapping_for

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ge_nwp_coordinator/_rw0_phase_entry_semantic_values.py"
PACKAGE = ROOT / "src/ge_nwp_coordinator"
OWNER = ROOT / ".docs/rw0-b1-pure-phase-values.md"


class _B1RegistryProjection(NamedTuple):
    version: int
    rows: tuple[tuple[object, ...], ...]


_B1_REGISTRY_HEADING = "## Current-contract registry"
_B1_REGISTRY_POLICY = (
    "Only the bounded registry below is machine-authoritative for the facts that it",
    "owns. Projection rows consume their named owner and create no second authority.",
)
_B1_REGISTRY_BEGIN = "<!-- RW0_B1_CURRENT_CONTRACT_REGISTRY_BEGIN -->"
_B1_REGISTRY_END = "<!-- RW0_B1_CURRENT_CONTRACT_REGISTRY_END -->"
_B1_REGISTRY_VERSION = "Registry version: 1"
_B1_REGISTRY_HEADER = "| Fact | Value | Role | Source |"
_B1_REGISTRY_SEPARATOR = "| --- | --- | --- | --- |"
_B1_REGISTRY_ROW_LINES = (
    "| component | RW0-B1 | authority | this_document |",
    "| lifecycle_status | current_implemented | projection | .docs/rw0-remote-worker-contact-phase-entry.md |",
    "| contract_class | private_pure_no_io_semantics | projection | .docs/rw0-remote-worker-contact-phase-entry.md |",
    "| retrieval_event_sequence_work_maximum | 1285 | authority | this_document |",
    "| sole_current_cross_module_production_consumer | RW0-B2-Capability | authority | this_document |",
    "| source_authentication | none | authority | this_document |",
    "| executable_permission | none | authority | this_document |",
    "| durable_persistence | none | authority | this_document |",
    "| semantic_acceptance | none | authority | this_document |",
    "| future_bootstrap_acceptance_guard_owner | RW0-C | projection | .docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md |",
    "| future_durable_ingest_completeness_recovery_terminal_owner | RW0-C | projection | .docs/rw0-remote-worker-contact-phase-entry.md |",
    "| future_physical_custody_transport_process_cancellation_owner | RW0-D | projection | .docs/rw0-remote-worker-contact-phase-entry.md |",
    "| future_separately_authorized_live_proof_owner | RW0-E | projection | .docs/rw0-remote-worker-contact-phase-entry.md |",
    "| es_admission_reliable_submit_runtime_identity_lifecycle_cancellation_results_owner | Execution Substrate | projection | .docs/rw0-remote-worker-contact-phase-entry.md |",
)
_B1_CANONICAL_BLOCK_LINES = (
    _B1_REGISTRY_HEADING,
    "",
    *_B1_REGISTRY_POLICY,
    "",
    _B1_REGISTRY_BEGIN,
    _B1_REGISTRY_VERSION,
    "",
    _B1_REGISTRY_HEADER,
    _B1_REGISTRY_SEPARATOR,
    *_B1_REGISTRY_ROW_LINES,
    _B1_REGISTRY_END,
)
_B1_CANONICAL_BLOCK = "\n".join(_B1_CANONICAL_BLOCK_LINES)
_B1_EXPECTED_PROJECTION = _B1RegistryProjection(
    1,
    (
        ("component", "RW0-B1", "authority", "this_document"),
        ("lifecycle_status", "current_implemented", "projection", ".docs/rw0-remote-worker-contact-phase-entry.md"),
        ("contract_class", "private_pure_no_io_semantics", "projection", ".docs/rw0-remote-worker-contact-phase-entry.md"),
        ("retrieval_event_sequence_work_maximum", 1285, "authority", "this_document"),
        ("sole_current_cross_module_production_consumer", "RW0-B2-Capability", "authority", "this_document"),
        ("source_authentication", "none", "authority", "this_document"),
        ("executable_permission", "none", "authority", "this_document"),
        ("durable_persistence", "none", "authority", "this_document"),
        ("semantic_acceptance", "none", "authority", "this_document"),
        ("future_bootstrap_acceptance_guard_owner", "RW0-C", "projection", ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md"),
        ("future_durable_ingest_completeness_recovery_terminal_owner", "RW0-C", "projection", ".docs/rw0-remote-worker-contact-phase-entry.md"),
        ("future_physical_custody_transport_process_cancellation_owner", "RW0-D", "projection", ".docs/rw0-remote-worker-contact-phase-entry.md"),
        ("future_separately_authorized_live_proof_owner", "RW0-E", "projection", ".docs/rw0-remote-worker-contact-phase-entry.md"),
        ("es_admission_reliable_submit_runtime_identity_lifecycle_cancellation_results_owner", "Execution Substrate", "projection", ".docs/rw0-remote-worker-contact-phase-entry.md"),
    ),
)

_B1_PROSE_AUTHORITY_POLICY = {
    "enumerated_facts": "registry_is_sole_machine_authority",
    "surrounding_prose": "governing_explanatory_contract_text",
    "natural_language_contradiction_detection": "not_claimed",
    "arbitrary_semantic_equivalence": "outside_parser_contract",
}


def _b1_registry_fail(reason: str) -> None:
    allowed = {
        "b1.registry.encoding", "b1.registry.fence", "b1.registry.marker",
        "b1.registry.visibility", "b1.registry.location", "b1.registry.version",
        "b1.registry.shape", "b1.registry.order", "b1.registry.value",
        "b1.registry.projection",
    }
    assert reason in allowed
    raise AssertionError(reason)


def _b1_fence_candidate(line: str) -> tuple[str, int, str] | None:
    indent = len(line) - len(line.lstrip(" "))
    if indent > 3:
        return None
    rest = line[indent:]
    if not rest or rest[0] not in "`~":
        return None
    marker = rest[0]
    run = len(rest) - len(rest.lstrip(marker))
    if run < 3:
        return None
    return marker, run, rest[run:]


def _b1_registry_visibility(lines: tuple[str, ...]) -> tuple[bool, ...]:
    visible: list[bool] = []
    fence: tuple[str, int] | None = None
    in_comment = False
    marker_lines = {_B1_REGISTRY_BEGIN, _B1_REGISTRY_END}
    for line in lines:
        if fence is not None:
            visible.append(False)
            candidate = _b1_fence_candidate(line)
            if (
                candidate is not None
                and candidate[0] == fence[0]
                and candidate[1] >= fence[1]
                and all(character in " \t" for character in candidate[2])
            ):
                fence = None
            continue
        if in_comment:
            visible.append(False)
            if "-->" in line:
                in_comment = False
            continue
        if line in marker_lines:
            visible.append(True)
            continue
        comment_at = line.find("<!--")
        if comment_at != -1:
            visible.append(False)
            if line.find("-->", comment_at + 4) == -1:
                in_comment = True
            continue
        candidate = _b1_fence_candidate(line)
        if candidate is not None and (
            candidate[0] != "`" or "`" not in candidate[2]
        ):
            visible.append(False)
            fence = candidate[:2]
            continue
        visible.append(True)
    return tuple(visible)


def _b1_bounded_atx_h2(line: str) -> bool:
    indent = len(line) - len(line.lstrip(" "))
    if indent > 3:
        return False
    source = line[indent:]
    return (
        source.startswith("##")
        and (len(source) == 2 or source[2] in " \t")
    )


def _b1_ascii_decimal(value: str) -> int:
    if not value or any(character < "0" or character > "9" for character in value):
        _b1_registry_fail("b1.registry.value")
    return int(value)


def _b1_parse_row(line: str) -> tuple[str, str, str, str]:
    if not line.startswith("| ") or not line.endswith(" |") or "\t" in line:
        _b1_registry_fail("b1.registry.shape")
    cells = tuple(line[2:-2].split(" | "))
    if len(cells) != 4 or any(not cell for cell in cells):
        _b1_registry_fail("b1.registry.shape")
    return cells  # type: ignore[return-value]


def _parse_b1_registry(raw: bytes) -> _B1RegistryProjection:
    if raw.startswith(b"\xef\xbb\xbf"):
        _b1_registry_fail("b1.registry.encoding")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _b1_registry_fail("b1.registry.encoding")
    lines = tuple(text.split("\n"))
    for token in (_B1_REGISTRY_HEADING, _B1_REGISTRY_BEGIN, _B1_REGISTRY_END):
        if lines.count(token) != 1:
            _b1_registry_fail("b1.registry.marker")
    if lines.count(_B1_REGISTRY_VERSION) != 1:
        _b1_registry_fail("b1.registry.version")
    if lines.count(_B1_REGISTRY_HEADER) != 1:
        _b1_registry_fail("b1.registry.shape")

    heading_index = lines.index(_B1_REGISTRY_HEADING)
    begin_index = lines.index(_B1_REGISTRY_BEGIN)
    end_index = lines.index(_B1_REGISTRY_END)
    visible = _b1_registry_visibility(lines)
    canonical_indices = (heading_index, begin_index, end_index)
    if not all(visible[index] for index in canonical_indices):
        _b1_registry_fail("b1.registry.visibility")
    visible_h2 = tuple(
        index for index, line in enumerate(lines)
        if visible[index] and _b1_bounded_atx_h2(line)
    )
    closed_indices = tuple(
        index for index, line in enumerate(lines) if line == "## Closed value grammar"
    )
    if (
        not visible_h2
        or visible_h2[0] != heading_index
        or len(closed_indices) != 1
    ):
        _b1_registry_fail("b1.registry.location")
    closed_index = closed_indices[0]
    if not visible[closed_index] or closed_index not in visible_h2:
        _b1_registry_fail("b1.registry.location")
    if not (heading_index < begin_index < end_index < closed_index):
        _b1_registry_fail("b1.registry.location")
    if end_index + 2 != closed_index or lines[end_index + 1] != "":
        _b1_registry_fail("b1.registry.location")
    section = lines[heading_index:end_index + 1]
    if any("\r" in line for line in section):
        _b1_registry_fail("b1.registry.shape")
    if len(section) != len(_B1_CANONICAL_BLOCK_LINES):
        _b1_registry_fail("b1.registry.shape")
    fixed_positions = tuple(range(10)) + (len(section) - 1,)
    if any(section[index] != _B1_CANONICAL_BLOCK_LINES[index] for index in fixed_positions):
        _b1_registry_fail("b1.registry.shape")
    row_lines = section[10:-1]
    rows = tuple(_b1_parse_row(line) for line in row_lines)
    expected_facts = tuple(row[0] for row in _B1_EXPECTED_PROJECTION.rows)
    observed_facts = tuple(row[0] for row in rows)
    if observed_facts != expected_facts:
        if len(observed_facts) == len(expected_facts) and set(observed_facts) == set(expected_facts):
            _b1_registry_fail("b1.registry.order")
        _b1_registry_fail("b1.registry.shape")
    if tuple(row_lines) != _B1_REGISTRY_ROW_LINES:
        _b1_registry_fail("b1.registry.value")
    if not all(visible[index] for index in range(heading_index, end_index + 1)):
        _b1_registry_fail("b1.registry.visibility")
    version = _b1_ascii_decimal(section[6].removeprefix("Registry version: "))
    typed_rows: list[tuple[object, ...]] = []
    for fact, value, role, source in rows:
        typed_value: object = (
            _b1_ascii_decimal(value)
            if fact == "retrieval_event_sequence_work_maximum"
            else value
        )
        typed_rows.append((fact, typed_value, role, source))
    projection = _B1RegistryProjection(version, tuple(typed_rows))
    if projection != _B1_EXPECTED_PROJECTION:
        _b1_registry_fail("b1.registry.projection")
    return projection


def _b1_replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1
    return text.replace(old, new, 1)


_B1_STRUCTURE_CASES = (
    "missing_heading", "duplicate_heading", "heading_in_fence",
    "heading_in_larger_comment", "missing_begin", "missing_end",
    "reversed_markers", "duplicate_begin", "duplicate_end",
    "begin_marker_in_fence", "end_marker_in_comment", "missing_version",
    "wrong_version", "duplicate_version", "missing_header", "wrong_header",
    "duplicate_header", "missing_row", "extra_row", "duplicate_row",
    "unknown_row", "renamed_field", "reordered_rows", "relocated_block",
    "registry_after_wrong_heading", "block_hidden_backtick_fence",
    "block_hidden_tilde_fence", "unclosed_fence",
    "opposite_marker_nonclosure", "shorter_closer_nonclosure",
    "backtick_info_with_backtick_nonopener", "four_space_fence_nonopener",
    "cr_in_registry_line", "bom", "unicode_line_separator", "tab",
    "trailing_space", "nbsp", "unicode_digit", "inline_emphasis",
    "inline_link", "inline_code", "extra_pipe",
    "multiline_comment_spanning_registry", "comment_spliced_registry_line",
)
_B1_STRUCTURE_ACCEPTED = {
    "backtick_info_with_backtick_nonopener", "four_space_fence_nonopener",
}


def _b1_structure_mutant(raw: bytes, case: str) -> bytes:
    text = raw.decode("utf-8")
    row0, row1 = _B1_REGISTRY_ROW_LINES[:2]
    if case == "missing_heading":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "## Current contract registry")
    elif case == "duplicate_heading":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, _B1_REGISTRY_HEADING + "\n" + _B1_REGISTRY_HEADING)
    elif case == "heading_in_fence":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "```text\n" + _B1_REGISTRY_HEADING + "\n```")
    elif case == "heading_in_larger_comment":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "<!-- heading-only\n" + _B1_REGISTRY_HEADING + "\n-->")
    elif case == "missing_begin":
        text = _b1_replace_once(text, _B1_REGISTRY_BEGIN + "\n", "")
    elif case == "missing_end":
        text = _b1_replace_once(text, _B1_REGISTRY_END, "<!-- missing b1 registry end -->")
    elif case == "reversed_markers":
        text = text.replace(_B1_REGISTRY_BEGIN, "__B1_BEGIN__", 1).replace(_B1_REGISTRY_END, _B1_REGISTRY_BEGIN, 1).replace("__B1_BEGIN__", _B1_REGISTRY_END, 1)
    elif case == "duplicate_begin":
        text = _b1_replace_once(text, _B1_REGISTRY_BEGIN, _B1_REGISTRY_BEGIN + "\n" + _B1_REGISTRY_BEGIN)
    elif case == "duplicate_end":
        text = _b1_replace_once(text, _B1_REGISTRY_END, _B1_REGISTRY_END + "\n" + _B1_REGISTRY_END)
    elif case == "begin_marker_in_fence":
        text = _b1_replace_once(text, _B1_REGISTRY_BEGIN, "```text\n" + _B1_REGISTRY_BEGIN + "\n```")
    elif case == "end_marker_in_comment":
        text = _b1_replace_once(text, _B1_REGISTRY_END, "<!-- enclosing-end\n" + _B1_REGISTRY_END + "\n-->")
    elif case == "missing_version":
        text = _b1_replace_once(text, _B1_REGISTRY_VERSION + "\n", "")
    elif case == "wrong_version":
        text = _b1_replace_once(text, _B1_REGISTRY_VERSION, "Registry version: 2")
    elif case == "duplicate_version":
        text = _b1_replace_once(text, _B1_REGISTRY_VERSION, _B1_REGISTRY_VERSION + "\n" + _B1_REGISTRY_VERSION)
    elif case == "missing_header":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADER + "\n", "")
    elif case == "wrong_header":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADER, "| Fact | Value | Source | Role |")
    elif case == "duplicate_header":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADER, _B1_REGISTRY_HEADER + "\n" + _B1_REGISTRY_HEADER)
    elif case == "missing_row":
        text = _b1_replace_once(text, row0 + "\n", "")
    elif case == "extra_row":
        text = _b1_replace_once(text, row0, row0 + "\n| extra_fact | none | authority | this_document |")
    elif case == "duplicate_row":
        text = _b1_replace_once(text, row0, row0 + "\n" + row0)
    elif case == "unknown_row":
        text = _b1_replace_once(text, row0, "| unknown_fact | RW0-B1 | authority | this_document |")
    elif case == "renamed_field":
        text = _b1_replace_once(text, row1, row1.replace("lifecycle_status", "lifecycle_state", 1))
    elif case == "reordered_rows":
        text = _b1_replace_once(text, row0 + "\n" + row1, row1 + "\n" + row0)
    elif case == "relocated_block":
        text = _b1_replace_once(text, _B1_CANONICAL_BLOCK + "\n\n", "")
        text = text.rstrip() + "\n\n" + _B1_CANONICAL_BLOCK + "\n"
    elif case == "registry_after_wrong_heading":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "## Earlier machine heading\n\n" + _B1_REGISTRY_HEADING)
    elif case == "block_hidden_backtick_fence":
        text = _b1_replace_once(text, _B1_CANONICAL_BLOCK, "```registry\n" + _B1_CANONICAL_BLOCK + "\n```")
    elif case == "block_hidden_tilde_fence":
        text = _b1_replace_once(text, _B1_CANONICAL_BLOCK, "~~~registry\n" + _B1_CANONICAL_BLOCK + "\n~~~")
    elif case == "unclosed_fence":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "```registry\n" + _B1_REGISTRY_HEADING)
    elif case == "opposite_marker_nonclosure":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "```registry\n~~~\n" + _B1_REGISTRY_HEADING)
    elif case == "shorter_closer_nonclosure":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "````registry\n```\n" + _B1_REGISTRY_HEADING)
    elif case == "backtick_info_with_backtick_nonopener":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "```bad`info\n" + _B1_REGISTRY_HEADING)
    elif case == "four_space_fence_nonopener":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADING, "    ```\n" + _B1_REGISTRY_HEADING)
    elif case == "cr_in_registry_line":
        text = _b1_replace_once(text, _B1_REGISTRY_HEADER, _B1_REGISTRY_HEADER + "\r")
    elif case == "bom":
        return b"\xef\xbb\xbf" + raw
    elif case == "unicode_line_separator":
        text = _b1_replace_once(text, row0, row0.replace("component", "compo\u2028nent", 1))
    elif case == "tab":
        text = _b1_replace_once(text, row0, row0.replace(" | RW0-B1", "\t| RW0-B1", 1))
    elif case == "trailing_space":
        text = _b1_replace_once(text, row0, row0 + " ")
    elif case == "nbsp":
        text = _b1_replace_once(text, row0, row0.replace(" | RW0-B1", "\u00a0| RW0-B1", 1))
    elif case == "unicode_digit":
        text = _b1_replace_once(text, _B1_REGISTRY_VERSION, "Registry version: \u0661")
    elif case == "inline_emphasis":
        text = _b1_replace_once(text, row0, row0.replace("component", "*component*", 1))
    elif case == "inline_link":
        text = _b1_replace_once(text, row0, row0.replace("component", "[component](owner)", 1))
    elif case == "inline_code":
        text = _b1_replace_once(text, row0, row0.replace("component", "`component`", 1))
    elif case == "extra_pipe":
        text = _b1_replace_once(text, row0, row0[:-1] + " extra |")
    elif case == "multiline_comment_spanning_registry":
        text = _b1_replace_once(text, _B1_CANONICAL_BLOCK, "<!-- entire-registry-hidden\n" + _B1_CANONICAL_BLOCK + "\n-->")
    else:
        assert case == "comment_spliced_registry_line"
        text = _b1_replace_once(text, row0, row0.replace("component", "com<!-- splice -->ponent", 1))
    return text.encode("utf-8")


def _b1_wrong_cell(value: str, row_index: int, column_index: int) -> str:
    if value == "1285":
        return "1283"
    return f"{value}-wrong-{row_index}-{column_index}"


_B1_VALUE_CASES = tuple(
    (f"row-{row_index}-column-{column_index}", row_index, column_index, None)
    for row_index in range(len(_B1_REGISTRY_ROW_LINES))
    for column_index in (1, 2, 3)
) + (
    ("maximum-1284", 3, 1, "1284"),
    ("maximum-1286", 3, 1, "1286"),
    ("maximum-signed", 3, 1, "+1285"),
    ("maximum-leading-zero", 3, 1, "01285"),
    ("maximum-unicode-digit", 3, 1, "128\u0665"),
)


def _b1_value_mutant(raw: bytes, case: tuple[str, int, int, str | None]) -> bytes:
    _case_id, row_index, column_index, explicit = case
    text = raw.decode("utf-8")
    old_line = _B1_REGISTRY_ROW_LINES[row_index]
    cells = list(_b1_parse_row(old_line))
    cells[column_index] = explicit or _b1_wrong_cell(cells[column_index], row_index, column_index)
    new_line = "| " + " | ".join(cells) + " |"
    return _b1_replace_once(text, old_line, new_line).encode("utf-8")


_B1_FALSE_POSITIVE_CASES = (
    ("unrelated_before", "Unrelated explanatory prose appears before the registry."),
    ("unrelated_after", "Unrelated explanatory prose appears after the registry."),
    ("status_words", "Current future blocked and deferred are ordinary explanatory words here."),
    ("setext_title", "Current-contract registry\n---"),
    ("inline_title", "The *Current-contract registry* phrase is explanatory only."),
    ("four_space_title", "    ## Current-contract registry"),
    ("fenced_example", "```text\n## Current contract registry\nRegistry version example: 7\n```"),
    ("historical", "Historical prose may say a former tranche was future."),
    ("restatement", "RW0-B1 is current implemented pure semantics in explanatory prose."),
    ("ordinary_comment", "<!-- An ordinary comment outside the registry. -->"),
    ("unicode_prose", "Explanatory prose may contain café, λ, and \u2028 separators."),
)

_B1_BOUNDED_H2_LOCATION_CASES = (
    ("earlier-h2-0-space", "## Earlier live H2", False),
    ("earlier-h2-1-space", " ## Earlier live H2", False),
    ("earlier-h2-2-space", "  ## Earlier live H2", False),
    ("earlier-h2-3-space", "   ## Earlier live H2", False),
    ("earlier-h2-tab-delimiter", "##\tEarlier live H2", False),
    ("four-space-literal", "    ## literal", True),
    ("nbsp-delimiter", "##\u00a0literal", True),
    ("h3-before-registry", "### Earlier H3", True),
    ("ordinary-prose", "Ordinary visible prose before the registry.", True),
    ("fenced-h2", "```text\n## Ordinary fenced H2\n```", True),
    ("commented-h2", "<!--\n## Ordinary commented H2\n-->", True),
)
_B1_BOUNDED_H2_RECOGNIZER_CASES = (
    ("##", True),
    (" ## heading", True),
    ("  ##\theading", True),
    ("   ## heading", True),
    ("    ## literal", False),
    ("##\u00a0literal", False),
    ("##\u2003literal", False),
    ("### H3", False),
    ("##not-a-heading", False),
)


def _b1_false_positive(raw: bytes, case: tuple[str, str]) -> bytes:
    case_id, insertion = case
    text = raw.decode("utf-8")
    if case_id == "unrelated_after":
        return (text.rstrip() + "\n\n" + insertion + "\n").encode("utf-8")
    return _b1_replace_once(text, _B1_REGISTRY_HEADING, insertion + "\n\n" + _B1_REGISTRY_HEADING).encode("utf-8")


def _b1_location_document(raw: bytes, insertion: str) -> bytes:
    text = raw.decode("utf-8")
    return _b1_replace_once(
        text,
        _B1_REGISTRY_HEADING,
        insertion + "\n\n" + _B1_REGISTRY_HEADING,
    ).encode("utf-8")


def test_private_module_has_no_package_exports_or_production_importer() -> None:
    assert b1.__all__ == ()
    import ge_nwp_coordinator
    assert not any(name.startswith("RW0") for name in ge_nwp_coordinator.__dict__)
    capability_path = PACKAGE / "_rw0_worker_mechanism_capability_values.py"
    c1_values_path = PACKAGE / "_rw0_c1_semantic_values.py"
    c1_runtime_path = PACKAGE / "_sqlite_rw0_c1.py"
    post_execution_values_path = PACKAGE / "_post_execution_evidence_values.py"
    expected_importers = {
        capability_path,
        c1_values_path,
        c1_runtime_path,
        post_execution_values_path,
    }
    importers = []
    for path in PACKAGE.rglob("*.py"):
        if path == SOURCE:
            continue
        source = path.read_text()
        if "_rw0_phase_entry_semantic_values" not in source:
            continue
        importers.append(path)
        imports = [
            node for node in ast.parse(source).body
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
        ]
        if path == capability_path:
            owner_imports = [
                node for node in imports
                if node.module == "_rw0_phase_entry_semantic_values"
            ]
            assert len(owner_imports) == 1
            assert {alias.name for alias in owner_imports[0].names} == {
                "RW0PhaseEntryBasisV1",
                "RW0AuthorityVerificationObservationV1",
                "RW0RemoteHostReadinessObservationV1",
                "RW0EffectHostQualificationV1",
                "_validate_host_qualification_with_snapshots",
            }
        elif path == c1_values_path:
            owner_imports = [
                node for node in imports
                if node.module == "_rw0_phase_entry_semantic_values"
            ]
            assert len(owner_imports) == 1
            assert {alias.name for alias in owner_imports[0].names} == {
                "RW0AuthorityVerificationObservationV1",
                "RW0CustodyAvailabilityObservationV1",
                "RW0EffectHostQualificationV1",
                "RW0PhaseEntryBasisV1",
                "RW0RemoteHostReadinessObservationV1",
                "RW0RetrievalCapabilityEventObservationV1",
                "RW0SubordinateAuthorizationProposalV1",
            }
        elif path == c1_runtime_path:
            assert path == c1_runtime_path
            owner_imports = [
                node for node in imports
                if node.module is None
                and [(alias.name, alias.asname) for alias in node.names]
                == [("_rw0_phase_entry_semantic_values", "_b1")]
            ]
            assert len(owner_imports) == 1
        else:
            assert path == post_execution_values_path
            owner_imports = [
                node for node in imports
                if node.module is None
                and [(alias.name, alias.asname) for alias in node.names]
                == [("_rw0_phase_entry_semantic_values", "_phase_values")]
            ]
            assert len(owner_imports) == 1
            assert "_validate_host_qualification_with_snapshots" not in source
    assert set(importers) == expected_importers
    assert "_rw0_worker_mechanism_capability_values" not in SOURCE.read_text()


def test_pure_import_and_ast_boundary() -> None:
    tree = ast.parse(SOURCE.read_text())
    allowed_std = {"datetime", "hashlib", "json", "re", "typing"}
    allowed_private = {
        "_worker_execution_semantic_values",
        "_development_pre_execution_plan_disposition_contracts",
        "_cognitive_proposal_row_values", "_development_effect_row_values",
        "_development_program_row_values", "_development_decision_row_values",
        "persistence_contracts",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed_std for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.level == 1 and node.module in allowed_private or (
                node.module == "__future__" and node.level == 0)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"now", "utcnow", "time", "monotonic",
                                          "open", "connect", "run", "Popen"}
    assert "__all__: tuple[str, ...] = ()" in SOURCE.read_text()


def test_privacy_sentinels_and_error_content_free() -> None:
    cls = b1.RW0RemoteHostReadinessObservationV1
    payload = mapping_for(cls)
    for forbidden in ("hostname", "ip_address", "endpoint", "host_key",
                      "username", "bearer_token", "credential_secret",
                      "absolute_path", "stdout", "transcript", "provider_session"):
        with pytest.raises(b1.RW0PhaseValueError) as caught:
            bounded = dict(payload)
            del bounded["observation_ref"]
            bounded[forbidden] = "SENTINEL-PRIVATE"
            cls.from_mapping(bounded)
        assert caught.value.reason == "privacy_forbidden_material"
        assert "SENTINEL-PRIVATE" not in str(caught.value)
        assert "SENTINEL-PRIVATE" not in repr(caught.value)
        assert caught.value.__cause__ is None
    value = cls.from_mapping(payload)
    assert "ref-safe-host-correlation-ref" not in repr(value)
    assert "ref-safe-host-correlation-ref" not in str(value)


def _assert_no_hidden_runtime_or_identity_shortcut(source: str) -> None:
    tree = ast.parse(source)
    forbidden_calls = {"eval", "exec", "compile", "__import__", "open"}
    forbidden_attributes = {
        "open", "connect", "run", "Popen", "set_int_max_str_digits",
        "import_module", "getenv", "system", "now", "utcnow",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_attributes
        if isinstance(node, ast.Compare) and any(isinstance(op, ast.Is) for op in node.ops):
            names = {member.id for member in (node.left, *node.comparators)
                     if isinstance(member, ast.Name)}
            assert names != {"current_effect_fence", "author_effect_fence"}


def test_private_source_forbids_runtime_calls_and_fence_identity_shortcut() -> None:
    source = SOURCE.read_text()
    _assert_no_hidden_runtime_or_identity_shortcut(source)
    for mutation in (
        "\nimport os\nos.system('forbidden')\n",
        "\nimport sys\nsys.set_int_max_str_digits(0)\n",
        "\ndef bad(current_effect_fence, author_effect_fence):\n"
        "    return current_effect_fence is author_effect_fence\n",
    ):
        with pytest.raises(AssertionError):
            _assert_no_hidden_runtime_or_identity_shortcut(source + mutation)



def _assert_cardinality_precedes_caller_traversal(source: str) -> None:
    tree = ast.parse(source)
    helper = next(node for node in tree.body
                  if isinstance(node, ast.FunctionDef) and node.name == "_closed_mapping")
    # Test-owned structural oracle: an exact-type guard, then an O(1) size
    # rejection, before even aliasing or passing the caller mapping elsewhere.
    expected_type = ast.parse("type(payload) is not dict", mode="eval").body
    expected_size = ast.parse("len(payload) > len(fields)", mode="eval").body
    first, guard = helper.body[:2]
    assert isinstance(first, ast.If) and ast.dump(first.test) == ast.dump(expected_type)
    assert isinstance(guard, ast.If) and ast.dump(guard.test) == ast.dump(expected_size)
    assert len(guard.body) == 1 and not guard.orelse
    rejection = guard.body[0]
    assert isinstance(rejection, ast.Expr) and isinstance(rejection.value, ast.Call)
    call = rejection.value
    assert isinstance(call.func, ast.Name) and call.func.id == "_fail"
    assert [ast.dump(arg) for arg in call.args] == [
        ast.dump(ast.Constant("unknown_field")), ast.dump(ast.Name(id="label", ctx=ast.Load()))]
    # No caller sort, copy, or collection materialization is part of closure.
    for node in ast.walk(helper):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"sorted", "list", "tuple", "set", "dict"}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"sort", "copy", "keys", "items"}


def test_fourth_closed_mapping_cardinality_precedes_caller_traversal() -> None:
    _assert_cardinality_precedes_caller_traversal(SOURCE.read_text())


def test_fourth_all_eight_constructors_use_common_closed_mapping(monkeypatch) -> None:
    classes = (
        b1.RW0PhaseEntryBasisV1, b1.RW0AuthorityVerificationObservationV1,
        b1.RW0SubordinateAuthorizationProposalV1, b1.RW0CustodyAvailabilityObservationV1,
        b1.RW0RetrievalCapabilityEventObservationV1, b1.RW0RemoteHostReadinessObservationV1,
        b1.RW0EffectHostQualificationV1, b1.RW0TerminalOutcomeV1,
    )
    original = b1._closed_mapping
    seen = []
    def measured(payload, fields, label):
        seen.append((payload, fields, label))
        return original(payload, fields, label)
    monkeypatch.setattr(b1, "_closed_mapping", measured)
    for cls in classes:
        seen.clear()
        payload = mapping_for(cls)
        assert cls.from_mapping.__func__ is b1._B1Value.from_mapping.__func__
        assert cls.from_mapping(payload) is not None
        assert sum(item[0] is payload for item in seen) == 1
        assert seen[0] == (payload, cls._FIELDS, cls.__name__)


def test_b1_live_registry_projection() -> None:
    projection = _parse_b1_registry(OWNER.read_bytes())
    assert projection == _B1_EXPECTED_PROJECTION
    assert _parse_b1_registry(OWNER.read_bytes()) is not projection
    assert isinstance(projection.rows, tuple)
    assert all(isinstance(row, tuple) for row in projection.rows)


def test_b1_registry_prose_authority_policy_is_explicit() -> None:
    assert _B1_PROSE_AUTHORITY_POLICY == {
        "enumerated_facts": "registry_is_sole_machine_authority",
        "surrounding_prose": "governing_explanatory_contract_text",
        "natural_language_contradiction_detection": "not_claimed",
        "arbitrary_semantic_equivalence": "outside_parser_contract",
    }
    source = OWNER.read_text(encoding="utf-8")
    assert "\n".join(_B1_REGISTRY_POLICY) in source


@pytest.mark.parametrize("case", _B1_STRUCTURE_CASES)
def test_b1_finite_registry_structure_and_visibility_contract(case: str) -> None:
    raw = OWNER.read_bytes()
    _parse_b1_registry(raw)
    mutant = _b1_structure_mutant(raw, case)
    assert mutant != raw
    if case in _B1_STRUCTURE_ACCEPTED:
        assert _parse_b1_registry(mutant) == _B1_EXPECTED_PROJECTION
    else:
        with pytest.raises(AssertionError, match=r"^b1\.registry\.[a-z_]+$"):
            _parse_b1_registry(mutant)


@pytest.mark.parametrize(
    "case", _B1_VALUE_CASES, ids=lambda case: case[0],
)
def test_b1_finite_registry_value_contract(
    case: tuple[str, int, int, str | None],
) -> None:
    raw = OWNER.read_bytes()
    mutant = _b1_value_mutant(raw, case)
    assert mutant != raw
    with pytest.raises(AssertionError, match=r"^b1\.registry\.(?:value|projection)$"):
        _parse_b1_registry(mutant)


@pytest.mark.parametrize(
    "case", _B1_FALSE_POSITIVE_CASES, ids=lambda case: case[0],
)
def test_b1_explanatory_prose_is_outside_registry_oracle(
    case: tuple[str, str],
) -> None:
    raw = OWNER.read_bytes()
    baseline = _parse_b1_registry(raw)
    candidate = _b1_false_positive(raw, case)
    assert candidate != raw
    assert _parse_b1_registry(candidate) == baseline


@pytest.mark.parametrize(
    ("case_id", "insertion", "accepted"),
    _B1_BOUNDED_H2_LOCATION_CASES,
    ids=tuple(case[0] for case in _B1_BOUNDED_H2_LOCATION_CASES),
)
def test_b1_bounded_visible_h2_location_is_causal(
    case_id: str,
    insertion: str,
    accepted: bool,
) -> None:
    raw = OWNER.read_bytes()
    candidate = _b1_location_document(raw, insertion)
    assert candidate != raw, case_id
    if accepted:
        assert _parse_b1_registry(candidate) == _B1_EXPECTED_PROJECTION
    else:
        with pytest.raises(AssertionError, match=r"^b1\.registry\.location$"):
            _parse_b1_registry(candidate)


@pytest.mark.parametrize(
    ("line", "expected"),
    _B1_BOUNDED_H2_RECOGNIZER_CASES,
    ids=(
        "end-of-line", "one-space-indent", "tab-delimiter",
        "three-space-indent", "four-space-literal", "nbsp-delimiter",
        "em-space-delimiter", "h3", "missing-delimiter",
    ),
)
def test_b1_bounded_atx_h2_source_grammar(line: str, expected: bool) -> None:
    assert _b1_bounded_atx_h2(line) is expected


def test_b1_generated_registry_documents_have_unique_bytes_and_purposes() -> None:
    raw = OWNER.read_bytes()
    documents: list[tuple[str, bytes]] = []
    documents.extend(
        ("structure:" + case, _b1_structure_mutant(raw, case))
        for case in _B1_STRUCTURE_CASES
    )
    documents.extend(
        ("value:" + case[0], _b1_value_mutant(raw, case))
        for case in _B1_VALUE_CASES
    )
    documents.extend(
        ("prose:" + case[0], _b1_false_positive(raw, case))
        for case in _B1_FALSE_POSITIVE_CASES
    )
    documents.extend(
        ("location:" + case_id, _b1_location_document(raw, insertion))
        for case_id, insertion, _accepted in _B1_BOUNDED_H2_LOCATION_CASES
    )
    purposes = tuple(purpose for purpose, _document in documents)
    digests = tuple(hashlib.sha256(document).hexdigest() for _purpose, document in documents)
    assert len(purposes) == len(set(purposes))
    assert len(digests) == len(set(digests))


def _assert_bootstrap_legacy_compatibility(text):
    compact = ' '.join(text.split())
    required = (
        'The exact v1 names `latch_postimage_ref` and `latch_postimage_digest` remain legacy representation names.',
        'Their replacement-target binding is the immutable bootstrap-acceptance fact identity/digest',
        'They imply no mutable preimage, available/consumed state, transition, revision, or separate classifier.',
        'Current B1 validates pair presence/absence and supplied-value coherence only.',
        'It proves no lineage scope, standing-policy admission, uniqueness, commitment, atomic family membership, or recovery truth.',
        'No new target implementation may consume the pair as durable guard proof until a separately accepted safe-value compatibility/versioning decision.',
        'Source, schema ID, field order, nullability, canonical bytes, digest domain, and budgets are unchanged.',
    )
    for sentence in required:
        if sentence not in compact:
            raise AssertionError('b1:legacy_compatibility:' + sentence)


def test_bootstrap_legacy_pair_is_representation_nonproof_only():
    _assert_bootstrap_legacy_compatibility(OWNER.read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '4be365d3a494088d5353592f6f689682d59217ac211072f6b27edc874dd2df36', 'b1:unchanged_source_schema_fields_domains_budgets'

    for name in ('latch_postimage_ref', 'latch_postimage_digest'):
        assert name in SOURCE.read_text(), 'b1:legacy_field_preserved:' + name
    source = SOURCE.read_text()
    assert 'bootstrap_acceptance_guard' not in source, 'b1:no_guard_consumer'


def test_bootstrap_legacy_proof_overclaim_is_rejected():
    text = OWNER.read_text().replace('Current B1 validates pair presence/absence and supplied-value coherence only.', 'Current B1 proves durable guard commitment.')
    with pytest.raises(AssertionError, match='^b1:legacy_compatibility:Current B1'):
        _assert_bootstrap_legacy_compatibility(text)
