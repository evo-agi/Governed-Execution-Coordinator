from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _doc() -> str:
    return (ROOT / ".docs" / "p1-1-transition-event-algebra.md").read_text(encoding="utf-8")


def test_event_algebra_doc_pins_single_responsibility_owners() -> None:
    text = _doc()
    for phrase in (
        "The parser and model layer owns",
        "The atomic apply boundary owns",
        "The pure evaluator owns",
        "The report layer owns projection only",
    ):
        assert phrase in text


def test_event_algebra_doc_pins_failure_taxonomy_and_expected_version() -> None:
    text = _doc()
    for phrase in (
        "Pre-Apply Invalid Command",
        "Apply Conflict",
        "Durable Domain Rejection",
        "Committed Acceptance",
        "Exact Replay",
        "Expected-version mismatch is an apply conflict",
        "The event is the receipt",
        "Caller code never provides proposed state or proposed event",
        "External versioned inputs are exact-shape and non-coercing",
        "Malformed\narray-like input must not be canonicalized into an accepted command identity",
    ):
        assert phrase in text
