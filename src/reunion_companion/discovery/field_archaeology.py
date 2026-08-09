"""Statistical field archaeology over raw event observations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .event_scanner import EventObservation


@dataclass(frozen=True, slots=True)
class ByteStat:
    relative_offset: int
    sample_count: int
    distinct_values: int
    most_common_value: int
    most_common_count: int
    most_common_percent: float

    @property
    def is_constant(self) -> bool:
        return self.distinct_values == 1


@dataclass(frozen=True, slots=True)
class WordStat:
    relative_offset: int
    width: int
    sample_count: int
    distinct_values: int
    most_common_value: int
    most_common_count: int
    most_common_percent: float


@dataclass(frozen=True, slots=True)
class FieldArchaeologyReport:
    observation_count: int
    byte_stats: tuple[ByteStat, ...]
    word_stats: tuple[WordStat, ...]

    def byte_at(self, relative_offset: int) -> ByteStat | None:
        for item in self.byte_stats:
            if item.relative_offset == relative_offset:
                return item
        return None

    def word_at(self, relative_offset: int, width: int = 2) -> WordStat | None:
        for item in self.word_stats:
            if item.relative_offset == relative_offset and item.width == width:
                return item
        return None


def _context_bytes(observation: EventObservation) -> bytes:
    return bytes.fromhex(observation.context_hex)


def analyse_observations(
    observations: Iterable[EventObservation],
    *,
    pre_bytes: int = 24,
    post_bytes: int = 24,
) -> FieldArchaeologyReport:
    values = list(observations)
    if not values:
        return FieldArchaeologyReport(0, (), ())

    # Build a marker-centred window from each observation's stored context.
    # Build 2 stores up to 24 bytes either side of the marker.
    windows: list[dict[int, int]] = []
    for obs in values:
        raw = _context_bytes(obs)
        # marker itself starts 24 bytes into a full-width context; if the
        # record begins closer than 24 bytes, marker position moves left.
        marker_in_context = min(24, obs.marker_offset)
        mapping = {}
        for idx, byte in enumerate(raw):
            rel = idx - marker_in_context
            if -pre_bytes <= rel < post_bytes:
                mapping[rel] = byte
        windows.append(mapping)

    byte_stats = []
    for rel in range(-pre_bytes, post_bytes):
        samples = [window[rel] for window in windows if rel in window]
        if not samples:
            continue
        counts = Counter(samples)
        value, count = counts.most_common(1)[0]
        byte_stats.append(
            ByteStat(
                relative_offset=rel,
                sample_count=len(samples),
                distinct_values=len(counts),
                most_common_value=value,
                most_common_count=count,
                most_common_percent=(count / len(samples)) * 100.0,
            )
        )

    word_stats = []
    for width in (2, 4):
        for rel in range(-pre_bytes, post_bytes - width + 1):
            samples = []
            for window in windows:
                if all((rel + delta) in window for delta in range(width)):
                    raw = bytes(window[rel + delta] for delta in range(width))
                    samples.append(int.from_bytes(raw, "little"))
            if not samples:
                continue
            counts = Counter(samples)
            value, count = counts.most_common(1)[0]
            word_stats.append(
                WordStat(
                    relative_offset=rel,
                    width=width,
                    sample_count=len(samples),
                    distinct_values=len(counts),
                    most_common_value=value,
                    most_common_count=count,
                    most_common_percent=(count / len(samples)) * 100.0,
                )
            )

    return FieldArchaeologyReport(
        observation_count=len(values),
        byte_stats=tuple(byte_stats),
        word_stats=tuple(word_stats),
    )


def rank_variable_bytes(
    report: FieldArchaeologyReport,
    *,
    minimum_samples: int = 10,
) -> list[ByteStat]:
    """Return high-coverage variable offsets, most stable first."""
    items = [
        item
        for item in report.byte_stats
        if item.sample_count >= minimum_samples and item.distinct_values > 1
    ]
    return sorted(
        items,
        key=lambda item: (-item.most_common_percent, item.distinct_values, item.relative_offset),
    )


def rank_constant_bytes(
    report: FieldArchaeologyReport,
    *,
    minimum_samples: int = 10,
) -> list[ByteStat]:
    return [
        item
        for item in report.byte_stats
        if item.sample_count >= minimum_samples and item.is_constant
    ]
