from reunion_companion.discovery.event_compare import (
    compare_layouts,
    discover_event_layouts,
    hexdump,
    observations_for_layout,
)
from reunion_companion.discovery.event_scanner import EventObservation


def _obs(
    person_id: int,
    *,
    signature: str = "aa bb",
    place: str | None = None,
    memo: bool = False,
    qualifier: int = 0,
    length: int = 100,
    marker: int = 40,
) -> EventObservation:
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=person_id * 100,
        record_length=length,
        marker_offset=marker,
        raw_date_offset=marker + 7,
        date_display=f"{person_id} Jan 1900",
        qualifier=qualifier,
        place_token=place,
        memo_candidate=memo,
        signature=signature,
        context_hex=(bytes(range(48))).hex(" "),
    )


def test_discover_layouts_groups_by_structural_key() -> None:
    observations = [
        _obs(1, place="[[pt:1]]"),
        _obs(2, place="[[pt:2]]"),
        _obs(3, place=None),
        _obs(4, place=None, memo=True),
    ]
    report = discover_event_layouts(observations)

    assert report.observation_count == 4
    assert len(report.layouts) == 3
    assert report.layouts[0].count == 2


def test_layout_summary_tracks_lengths_and_offsets() -> None:
    observations = [
        _obs(1, length=100, marker=40, place="[[pt:1]]"),
        _obs(2, length=120, marker=60, place="[[pt:2]]"),
    ]
    layout = discover_event_layouts(observations).layouts[0]

    assert layout.record_length_min == 100
    assert layout.record_length_max == 120
    assert layout.marker_offset_min == 40
    assert layout.marker_offset_max == 60


def test_compare_layouts_reports_structural_differences() -> None:
    report = discover_event_layouts([
        _obs(1, place="[[pt:1]]"),
        _obs(2, place=None, memo=True),
    ])
    comparison = compare_layouts(report.layouts[0], report.layouts[1])

    assert comparison.identical is False
    assert any(item.field == "place" for item in comparison.differences)


def test_observations_for_layout() -> None:
    observations = [
        _obs(1, place="[[pt:1]]"),
        _obs(2, place=None),
    ]
    report = discover_event_layouts(observations)
    selected = observations_for_layout(observations, report.layouts[0])

    assert len(selected) == 1


def test_hexdump_has_ascii_and_offsets() -> None:
    output = hexdump(b"Hello\x00World")
    assert "00000000" in output
    assert "Hello.World" in output
