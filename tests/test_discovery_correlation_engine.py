from reunion_companion.discovery.correlation_engine import (
    compare_people,
    correlate_memo,
    correlate_place,
    qualifier_summaries,
    rank_observations,
    structural_map,
)
from reunion_companion.discovery.event_scanner import EventObservation


def _obs(
    person_id: int,
    *,
    place: str | None = None,
    memo: bool = False,
    qualifier: int = 0,
    length: int = 100,
    date: str = "1 Jan 1900",
    context: bytes | None = None,
) -> EventObservation:
    if context is None:
        context = bytes([0] * 24) + bytes([10, 0, 8, 0, 0, 0, qualifier, 1, 2, 3, 4, 0, 0, 0]) + bytes([0] * 10)
        context = context[:48].ljust(48, b"\x00")
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
        context_hex=context.hex(" "),
    )


def test_place_correlation_groups_records() -> None:
    report = correlate_place([
        _obs(1, place="[[pt:1]]", length=200),
        _obs(2, place=None, length=100),
    ])
    assert report.left.count == 1
    assert report.right.count == 1
    assert report.record_length_mean_delta == 100


def test_memo_correlation_groups_records() -> None:
    report = correlate_memo([
        _obs(1, memo=True, length=300),
        _obs(2, memo=False, length=100),
    ])
    assert report.left.label == "with memo candidate"
    assert report.left.record_length_mean == 300


def test_qualifier_summary_does_not_assign_meaning() -> None:
    summaries = qualifier_summaries([
        _obs(1, qualifier=0x00, date="1 Jan 1900"),
        _obs(2, qualifier=0x80, date="1900"),
    ])
    assert [item.qualifier for item in summaries] == [0x00, 0x80]
    assert summaries[1].year_only_count == 1


def test_structural_map_contains_verified_regions() -> None:
    raw = bytearray([0] * 48)
    raw[24:30] = bytes.fromhex("0A 00 08 00 00 00")
    raw[30] = 0
    raw[31:35] = b"\x01\x02\x03\x04"
    raw[35:38] = b"\x00\x00\x00"
    raw[38:43] = b"[[pt:"
    structure = structural_map([_obs(1, place="[[pt:1]]", context=bytes(raw))])

    names = {region.name for region in structure.regions}
    assert "Event signature" in names
    assert "Packed date" in names
    assert "Place token start" in names


def test_rank_observations() -> None:
    values = [
        _obs(1, length=100),
        _obs(2, length=500),
        _obs(3, length=200),
    ]
    assert rank_observations(values, longest=True, limit=2)[0].person_id == 2
    assert rank_observations(values, longest=False, limit=2)[0].person_id == 1


def test_compare_people() -> None:
    result = compare_people([_obs(1), _obs(2, qualifier=0x80)], 1, 2)
    assert result is not None
    assert result.left.count == 1
    assert result.right.count == 1
