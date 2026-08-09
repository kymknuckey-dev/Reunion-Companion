"""Structural correlation engine for Reunion event archaeology.

The engine correlates observable record properties with marker-centred binary
bytes and whole-record measurements. It deliberately distinguishes verified
structure from candidate/unknown structure.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import fsum
import re
from statistics import mean, median
from typing import Callable, Iterable

from .event_scanner import EventObservation


@dataclass(frozen=True, slots=True)
class GroupSummary:
    label: str
    count: int
    record_length_min: int | None
    record_length_max: int | None
    record_length_mean: float | None
    record_length_median: float | None
    marker_offset_min: int | None
    marker_offset_max: int | None
    marker_offset_mean: float | None


@dataclass(frozen=True, slots=True)
class ByteCorrelation:
    relative_offset: int
    left_samples: int
    right_samples: int
    left_common: int | None
    right_common: int | None
    left_common_share: float
    right_common_share: float
    total_variation: float


@dataclass(frozen=True, slots=True)
class PropertyCorrelation:
    property_name: str
    left: GroupSummary
    right: GroupSummary
    byte_correlations: tuple[ByteCorrelation, ...]

    @property
    def record_length_mean_delta(self) -> float | None:
        if self.left.record_length_mean is None or self.right.record_length_mean is None:
            return None
        return self.left.record_length_mean - self.right.record_length_mean


@dataclass(frozen=True, slots=True)
class QualifierSummary:
    qualifier: int
    count: int
    exact_date_count: int
    year_only_count: int
    with_place_count: int
    with_memo_count: int
    record_length_mean: float


@dataclass(frozen=True, slots=True)
class StructuralRegion:
    name: str
    start_offset: int
    end_offset: int
    status: str
    confidence: float
    evidence: str


@dataclass(frozen=True, slots=True)
class StructuralMap:
    observation_count: int
    regions: tuple[StructuralRegion, ...]


@dataclass(frozen=True, slots=True)
class RankedObservation:
    person_id: int
    person_name: str
    date_display: str
    record_length: int
    marker_offset: int
    has_place: bool
    has_memo_candidate: bool
    qualifier: int


_YEAR_ONLY = re.compile(r"^(?:abt |bef |aft |cal )?\d{3,4}\??$", re.IGNORECASE)


def _window(obs: EventObservation) -> dict[int, int]:
    raw = bytes.fromhex(obs.context_hex)
    marker_in_context = min(24, obs.marker_offset)
    return {index - marker_in_context: byte for index, byte in enumerate(raw)}


def _summary(label: str, observations: list[EventObservation]) -> GroupSummary:
    if not observations:
        return GroupSummary(label, 0, None, None, None, None, None, None, None)

    lengths = [item.record_length for item in observations]
    markers = [item.marker_offset for item in observations]
    return GroupSummary(
        label=label,
        count=len(observations),
        record_length_min=min(lengths),
        record_length_max=max(lengths),
        record_length_mean=mean(lengths),
        record_length_median=median(lengths),
        marker_offset_min=min(markers),
        marker_offset_max=max(markers),
        marker_offset_mean=mean(markers),
    )


def _distribution(values: list[int]) -> dict[int, float]:
    if not values:
        return {}
    counts = Counter(values)
    total = len(values)
    return {value: count / total for value, count in counts.items()}


def _total_variation(left: dict[int, float], right: dict[int, float]) -> float:
    keys = set(left) | set(right)
    return 0.5 * fsum(abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in keys)


def correlate_groups(
    property_name: str,
    left_label: str,
    left: Iterable[EventObservation],
    right_label: str,
    right: Iterable[EventObservation],
    *,
    min_offset: int = -24,
    max_offset: int = 23,
) -> PropertyCorrelation:
    left_values = list(left)
    right_values = list(right)
    left_windows = [_window(item) for item in left_values]
    right_windows = [_window(item) for item in right_values]

    correlations: list[ByteCorrelation] = []
    for offset in range(min_offset, max_offset + 1):
        lbytes = [window[offset] for window in left_windows if offset in window]
        rbytes = [window[offset] for window in right_windows if offset in window]

        ldist = _distribution(lbytes)
        rdist = _distribution(rbytes)
        lcommon = Counter(lbytes).most_common(1)[0] if lbytes else (None, 0)
        rcommon = Counter(rbytes).most_common(1)[0] if rbytes else (None, 0)

        correlations.append(
            ByteCorrelation(
                relative_offset=offset,
                left_samples=len(lbytes),
                right_samples=len(rbytes),
                left_common=lcommon[0],
                right_common=rcommon[0],
                left_common_share=(lcommon[1] / len(lbytes) * 100.0) if lbytes else 0.0,
                right_common_share=(rcommon[1] / len(rbytes) * 100.0) if rbytes else 0.0,
                total_variation=_total_variation(ldist, rdist),
            )
        )

    return PropertyCorrelation(
        property_name=property_name,
        left=_summary(left_label, left_values),
        right=_summary(right_label, right_values),
        byte_correlations=tuple(correlations),
    )


def correlate_place(observations: Iterable[EventObservation]) -> PropertyCorrelation:
    values = list(observations)
    return correlate_groups(
        "place",
        "with place",
        [item for item in values if item.place_token is not None],
        "without place",
        [item for item in values if item.place_token is None],
    )


def correlate_memo(observations: Iterable[EventObservation]) -> PropertyCorrelation:
    values = list(observations)
    return correlate_groups(
        "memo candidate",
        "with memo candidate",
        [item for item in values if item.memo_candidate],
        "without memo candidate",
        [item for item in values if not item.memo_candidate],
    )


def qualifier_summaries(
    observations: Iterable[EventObservation],
) -> list[QualifierSummary]:
    groups: dict[int, list[EventObservation]] = {}
    for item in observations:
        groups.setdefault(item.qualifier, []).append(item)

    result: list[QualifierSummary] = []
    for qualifier, items in sorted(groups.items()):
        exact = sum(
            1 for item in items
            if not _YEAR_ONLY.fullmatch(item.date_display.strip())
        )
        year_only = len(items) - exact
        result.append(
            QualifierSummary(
                qualifier=qualifier,
                count=len(items),
                exact_date_count=exact,
                year_only_count=year_only,
                with_place_count=sum(1 for item in items if item.place_token),
                with_memo_count=sum(1 for item in items if item.memo_candidate),
                record_length_mean=mean(item.record_length for item in items),
            )
        )
    return result


def _place_start_offsets(observations: Iterable[EventObservation]) -> list[int]:
    offsets: list[int] = []
    needle = b"[[pt:"
    for item in observations:
        if item.place_token is None:
            continue
        raw = bytes.fromhex(item.context_hex)
        marker_in_context = min(24, item.marker_offset)
        found = raw.find(needle)
        if found >= 0:
            offsets.append(found - marker_in_context)
    return offsets


def structural_map(observations: Iterable[EventObservation]) -> StructuralMap:
    values = list(observations)
    place_offsets = _place_start_offsets(values)
    place_mode = Counter(place_offsets).most_common(1)[0] if place_offsets else (None, 0)

    regions: list[StructuralRegion] = [
        StructuralRegion(
            name="Variable prelude",
            start_offset=-24,
            end_offset=-13,
            status="observed",
            confidence=0.90,
            evidence="Build 3 shows substantial variation before the stable event signature.",
        ),
        StructuralRegion(
            name="Event signature",
            start_offset=-12,
            end_offset=-1,
            status="verified structural",
            confidence=1.00,
            evidence="12-byte signature is identical across all currently observed Birth structures.",
        ),
        StructuralRegion(
            name="Date descriptor",
            start_offset=0,
            end_offset=5,
            status="verified structural",
            confidence=1.00,
            evidence="Constant generic date marker 0A 00 08 00 00 00.",
        ),
        StructuralRegion(
            name="Date qualifier",
            start_offset=6,
            end_offset=6,
            status="verified location / semantic pending",
            confidence=1.00,
            evidence="Two observed qualifier values; semantic meaning is not yet assigned.",
        ),
        StructuralRegion(
            name="Packed date",
            start_offset=7,
            end_offset=10,
            status="verified",
            confidence=1.00,
            evidence="Existing packed-date decoder reproduces Reunion display dates.",
        ),
        StructuralRegion(
            name="Post-date transition",
            start_offset=11,
            end_offset=13,
            status="unknown",
            confidence=0.65,
            evidence="Short region between packed date and optional place token; semantics not yet known.",
        ),
    ]

    if place_mode[0] is not None:
        share = place_mode[1] / len(place_offsets) if place_offsets else 0.0
        regions.append(
            StructuralRegion(
                name="Place token start",
                start_offset=place_mode[0],
                end_offset=place_mode[0] + 4,
                status="verified token",
                confidence=share,
                evidence=(
                    f"ASCII [[pt: prefix begins here in {place_mode[1]:,}/"
                    f"{len(place_offsets):,} captured place contexts."
                ),
            )
        )

    regions.append(
        StructuralRegion(
            name="Variable payload / tail",
            start_offset=14,
            end_offset=23,
            status="partially observed",
            confidence=0.75,
            evidence=(
                "Contains place-token bytes when present and other variable bytes when absent. "
                "Current scanner context ends at +23, so full memo/citation boundaries cannot yet be proved."
            ),
        )
    )

    return StructuralMap(observation_count=len(values), regions=tuple(regions))


def rank_observations(
    observations: Iterable[EventObservation],
    *,
    longest: bool,
    limit: int = 20,
) -> list[RankedObservation]:
    values = sorted(
        observations,
        key=lambda item: (item.record_length, item.person_id),
        reverse=longest,
    )
    return [
        RankedObservation(
            person_id=item.person_id,
            person_name=item.person_name,
            date_display=item.date_display,
            record_length=item.record_length,
            marker_offset=item.marker_offset,
            has_place=item.place_token is not None,
            has_memo_candidate=item.memo_candidate,
            qualifier=item.qualifier,
        )
        for item in values[:limit]
    ]


def compare_people(
    observations: Iterable[EventObservation],
    left_person_id: int,
    right_person_id: int,
) -> PropertyCorrelation | None:
    values = list(observations)
    left = [item for item in values if item.person_id == left_person_id]
    right = [item for item in values if item.person_id == right_person_id]
    if not left or not right:
        return None
    return correlate_groups(
        f"person {left_person_id} vs {right_person_id}",
        f"person {left_person_id}",
        [left[0]],
        f"person {right_person_id}",
        [right[0]],
    )
