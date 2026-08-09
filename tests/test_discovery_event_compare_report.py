from reunion_companion.discovery.event_compare import (
    compare_layouts,
    discover_event_layouts,
)
from reunion_companion.discovery.event_compare_report import (
    event_comparison_markdown,
    format_event_comparison,
    format_event_lengths,
    format_layout,
    format_layout_diff,
    format_observation_hexdump,
)
from reunion_companion.discovery.event_scanner import EventObservation


def _obs(person_id: int, *, place=None, memo=False, length=100):
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=100,
        record_length=length,
        marker_offset=24,
        raw_date_offset=31,
        date_display="1 Jan 1900",
        qualifier=0,
        place_token=place,
        memo_candidate=memo,
        signature="aa bb",
        context_hex=(bytes(range(48))).hex(" "),
    )


def test_comparison_formatter() -> None:
    report = discover_event_layouts([_obs(1), _obs(2, place="[[pt:1]]")])
    output = format_event_comparison(report)
    assert "Event Structure Comparison" in output
    assert "Layout 1" in output


def test_layout_formatter() -> None:
    report = discover_event_layouts([_obs(1)])
    output = format_layout(report.layouts[0])
    assert "Occurrences" in output
    assert "Signature" in output


def test_diff_formatter() -> None:
    report = discover_event_layouts([_obs(1), _obs(2, place="[[pt:1]]")])
    output = format_layout_diff(compare_layouts(report.layouts[0], report.layouts[1]))
    assert "Event Layout Diff" in output
    assert "place" in output


def test_length_formatter() -> None:
    report = discover_event_layouts([_obs(1, length=100), _obs(2, length=120)])
    output = format_event_lengths(report)
    assert "Event Record Lengths" in output
    assert "100" in output


def test_observation_hexdump_formatter() -> None:
    output = format_observation_hexdump(_obs(1, place="[[pt:1]]"))
    assert "Person 1" in output
    assert "Context (relative to marker)" in output


def test_comparison_markdown() -> None:
    report = discover_event_layouts([_obs(1)])
    output = event_comparison_markdown(report)
    assert "# Event Structure Comparison" in output
    assert "| ID | Count |" in output
