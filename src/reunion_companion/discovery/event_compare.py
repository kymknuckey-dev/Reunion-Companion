"""Event layout comparison for Reunion Discovery Lab.

Build 4 compares observed binary layouts only. A layout is not assigned a
semantic Reunion event name until controlled-probe or independent evidence
confirms that identity.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from .event_scanner import EventObservation


@dataclass(frozen=True, slots=True)
class EventLayoutKey:
    signature: str
    has_place: bool
    has_memo_candidate: bool
    qualifier: int


@dataclass(frozen=True, slots=True)
class EventLayout:
    layout_id: int
    key: EventLayoutKey
    count: int
    record_length_min: int
    record_length_max: int
    record_length_mean: float
    marker_offset_min: int
    marker_offset_max: int
    sample_person_ids: tuple[int, ...]
    sample_names: tuple[str, ...]
    sample_dates: tuple[str, ...]

    @property
    def has_place(self) -> bool:
        return self.key.has_place

    @property
    def has_memo_candidate(self) -> bool:
        return self.key.has_memo_candidate


@dataclass(frozen=True, slots=True)
class LayoutDifference:
    field: str
    left: str
    right: str


@dataclass(frozen=True, slots=True)
class EventComparison:
    left: EventLayout
    right: EventLayout
    differences: tuple[LayoutDifference, ...]

    @property
    def identical(self) -> bool:
        return not self.differences


@dataclass(frozen=True, slots=True)
class LengthBucket:
    length: int
    count: int


@dataclass(frozen=True, slots=True)
class EventComparisonReport:
    observation_count: int
    layouts: tuple[EventLayout, ...]
    record_lengths: tuple[LengthBucket, ...]

    def layout(self, layout_id: int) -> EventLayout:
        for item in self.layouts:
            if item.layout_id == layout_id:
                return item
        raise KeyError(layout_id)


def discover_event_layouts(
    observations: Iterable[EventObservation],
) -> EventComparisonReport:
    values = list(observations)
    grouped: dict[EventLayoutKey, list[EventObservation]] = defaultdict(list)

    for item in values:
        key = EventLayoutKey(
            signature=item.signature,
            has_place=item.place_token is not None,
            has_memo_candidate=item.memo_candidate,
            qualifier=item.qualifier,
        )
        grouped[key].append(item)

    sorted_groups = sorted(
        grouped.items(),
        key=lambda pair: (
            -len(pair[1]),
            pair[0].signature,
            pair[0].has_place,
            pair[0].has_memo_candidate,
            pair[0].qualifier,
        ),
    )

    layouts: list[EventLayout] = []
    for layout_id, (key, items) in enumerate(sorted_groups, start=1):
        lengths = [item.record_length for item in items]
        marker_offsets = [item.marker_offset for item in items]
        layouts.append(
            EventLayout(
                layout_id=layout_id,
                key=key,
                count=len(items),
                record_length_min=min(lengths),
                record_length_max=max(lengths),
                record_length_mean=mean(lengths),
                marker_offset_min=min(marker_offsets),
                marker_offset_max=max(marker_offsets),
                sample_person_ids=tuple(item.person_id for item in items[:5]),
                sample_names=tuple(item.person_name for item in items[:5]),
                sample_dates=tuple(item.date_display for item in items[:5]),
            )
        )

    length_counts = Counter(item.record_length for item in values)
    record_lengths = tuple(
        LengthBucket(length=length, count=count)
        for length, count in sorted(
            length_counts.items(),
            key=lambda pair: (-pair[1], pair[0]),
        )
    )

    return EventComparisonReport(
        observation_count=len(values),
        layouts=tuple(layouts),
        record_lengths=record_lengths,
    )


def compare_layouts(left: EventLayout, right: EventLayout) -> EventComparison:
    comparisons = (
        ("signature", left.key.signature, right.key.signature),
        ("place", str(left.key.has_place), str(right.key.has_place)),
        (
            "memo_candidate",
            str(left.key.has_memo_candidate),
            str(right.key.has_memo_candidate),
        ),
        ("qualifier", str(left.key.qualifier), str(right.key.qualifier)),
        (
            "record_length_range",
            f"{left.record_length_min}-{left.record_length_max}",
            f"{right.record_length_min}-{right.record_length_max}",
        ),
        (
            "marker_offset_range",
            f"{left.marker_offset_min}-{left.marker_offset_max}",
            f"{right.marker_offset_min}-{right.marker_offset_max}",
        ),
    )

    differences = tuple(
        LayoutDifference(field=field, left=left_value, right=right_value)
        for field, left_value, right_value in comparisons
        if left_value != right_value
    )
    return EventComparison(left=left, right=right, differences=differences)


def observations_for_layout(
    observations: Iterable[EventObservation],
    layout: EventLayout,
) -> list[EventObservation]:
    key = layout.key
    return [
        item
        for item in observations
        if item.signature == key.signature
        and (item.place_token is not None) == key.has_place
        and item.memo_candidate == key.has_memo_candidate
        and item.qualifier == key.qualifier
    ]


def hexdump(data: bytes, *, width: int = 16, start_offset: int = 0) -> str:
    lines: list[str] = []
    for row_start in range(0, len(data), width):
        chunk = data[row_start : row_start + width]
        hex_part = " ".join(f"{byte:02X}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
        lines.append(
            f"{start_offset + row_start:08X}  "
            f"{hex_part:<{width * 3 - 1}}  |{ascii_part}|"
        )
    return "\n".join(lines)
