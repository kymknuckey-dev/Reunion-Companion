from reunion_companion.discovery.correlation_engine import (
    correlate_memo,
    correlate_place,
    qualifier_summaries,
    rank_observations,
    structural_map,
)
from reunion_companion.discovery.correlation_report import (
    archaeology_markdown,
    format_archaeology_dashboard,
    format_property_correlation,
    format_qualifier_analysis,
    format_ranked_observations,
    format_region_map,
)
from reunion_companion.discovery.event_scanner import EventObservation


def _obs(person_id, *, place=None, memo=False, qualifier=0, length=100, date="1 Jan 1900"):
    raw = bytearray([0] * 48)
    raw[24:30] = bytes.fromhex("0A 00 08 00 00 00")
    raw[30] = qualifier
    raw[31:35] = b"\x01\x02\x03\x04"
    if place:
        raw[38:43] = b"[[pt:"
    return EventObservation(
        person_id=person_id,
        person_name=f"Person {person_id}",
        record_offset=0,
        record_length=length,
        marker_offset=24,
        raw_date_offset=31,
        date_display=date,
        qualifier=qualifier,
        place_token=place,
        memo_candidate=memo,
        signature="01 00 00 00 00 00 00 00 06 00 00 00",
        context_hex=bytes(raw).hex(" "),
    )


def _parts():
    values = [
        _obs(1, place="[[pt:1]]", memo=True, length=300),
        _obs(2, length=100, qualifier=0x80, date="1900"),
    ]
    return (
        structural_map(values),
        correlate_place(values),
        correlate_memo(values),
        qualifier_summaries(values),
        values,
    )


def test_property_formatter() -> None:
    _, place, _, _, _ = _parts()
    output = format_property_correlation(place)
    assert "Strongest marker-centred byte differences" in output


def test_qualifier_formatter() -> None:
    _, _, _, qualifiers, _ = _parts()
    output = format_qualifier_analysis(qualifiers)
    assert "0x80" in output
    assert "Semantic meaning" in output


def test_region_map_formatter() -> None:
    structure, _, _, _, _ = _parts()
    output = format_region_map(structure)
    assert "Event signature" in output
    assert "Place token start" in output


def test_ranked_formatter() -> None:
    _, _, _, _, values = _parts()
    ranked = rank_observations(values, longest=True)
    output = format_ranked_observations("Longest", ranked)
    assert "Person 1" in output


def test_dashboard_and_markdown() -> None:
    structure, place, memo, qualifiers, _ = _parts()
    dashboard = format_archaeology_dashboard(structure, place, memo, qualifiers)
    markdown = archaeology_markdown(structure, place, memo, qualifiers)

    assert "Knowledge Status" in dashboard
    assert "Memo presence" in dashboard
    assert "# Birth/Event Structural Correlation" in markdown
