"""Extended bounded event capture for Discovery Beta 1 Build 6."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable

from .event_scanner import EventObservation


@dataclass(frozen=True, slots=True)
class CaptureSummary:
    observations: int
    capture_length_min: int
    capture_length_max: int
    capture_length_mean: float
    capture_length_median: float
    truncated_left: int
    truncated_right: int


@dataclass(frozen=True, slots=True)
class TokenObservation:
    token: str
    count: int
    sample_person_ids: tuple[int, ...]
    sample_offsets: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class RepeatedSequence:
    sequence_hex: str
    count: int
    relative_offset: int | None


@dataclass(frozen=True, slots=True)
class CaptureCandidate:
    person_id: int
    person_name: str
    date_display: str
    record_length: int
    capture_length: int
    marker_offset: int
    has_place: bool
    memo_candidate: bool
    qualifier: int


def _capture_bytes(item: EventObservation) -> bytes:
    if item.capture_hex:
        return bytes.fromhex(item.capture_hex)
    return bytes.fromhex(item.context_hex)


def capture_summary(observations: Iterable[EventObservation]) -> CaptureSummary:
    values = list(observations)
    if not values:
        return CaptureSummary(0, 0, 0, 0.0, 0.0, 0, 0)

    lengths = [item.capture_length for item in values]
    return CaptureSummary(
        observations=len(values),
        capture_length_min=min(lengths),
        capture_length_max=max(lengths),
        capture_length_mean=mean(lengths),
        capture_length_median=median(lengths),
        truncated_left=sum(1 for item in values if item.capture_truncated_left),
        truncated_right=sum(1 for item in values if item.capture_truncated_right),
    )


def find_ascii_tokens(
    observations: Iterable[EventObservation],
    *,
    prefixes: tuple[bytes, ...] = (b"[[pt:",),
) -> list[TokenObservation]:
    grouped: dict[str, list[tuple[int, int]]] = {}

    for item in observations:
        raw = _capture_bytes(item)
        for prefix in prefixes:
            cursor = 0
            while True:
                found = raw.find(prefix, cursor)
                if found < 0:
                    break
                end = raw.find(b"]]", found)
                if end < 0:
                    break
                token_bytes = raw[found:end + 2]
                try:
                    token = token_bytes.decode("ascii")
                except UnicodeDecodeError:
                    cursor = found + 1
                    continue
                grouped.setdefault(token, []).append(
                    (item.person_id, found - item.marker_offset_in_capture)
                )
                cursor = end + 2

    return sorted(
        [
            TokenObservation(
                token=token,
                count=len(values),
                sample_person_ids=tuple(person_id for person_id, _ in values[:5]),
                sample_offsets=tuple(offset for _, offset in values[:5]),
            )
            for token, values in grouped.items()
        ],
        key=lambda item: (-item.count, item.token),
    )


def repeated_sequences(
    observations: Iterable[EventObservation],
    *,
    width: int = 4,
    minimum_count: int = 25,
    relative_start: int = 11,
    relative_end: int = 256,
) -> list[RepeatedSequence]:
    counts: Counter[tuple[int, bytes]] = Counter()

    for item in observations:
        raw = _capture_bytes(item)
        marker = item.marker_offset_in_capture
        for relative in range(relative_start, relative_end - width + 1):
            start = marker + relative
            end = start + width
            if start < 0 or end > len(raw):
                continue
            counts[(relative, raw[start:end])] += 1

    return sorted(
        [
            RepeatedSequence(sequence.hex(" "), count, relative)
            for (relative, sequence), count in counts.items()
            if count >= minimum_count
        ],
        key=lambda item: (-item.count, item.relative_offset or 0),
    )


def rank_capture_candidates(
    observations: Iterable[EventObservation],
    *,
    longest: bool = True,
    limit: int = 25,
) -> list[CaptureCandidate]:
    values = sorted(
        observations,
        key=lambda item: (item.record_length, item.person_id),
        reverse=longest,
    )
    return [
        CaptureCandidate(
            person_id=item.person_id,
            person_name=item.person_name,
            date_display=item.date_display,
            record_length=item.record_length,
            capture_length=item.capture_length,
            marker_offset=item.marker_offset,
            has_place=item.place_token is not None,
            memo_candidate=item.memo_candidate,
            qualifier=item.qualifier,
        )
        for item in values[:limit]
    ]


def capture_for_person(
    observations: Iterable[EventObservation],
    person_id: int,
) -> EventObservation | None:
    for item in observations:
        if item.person_id == person_id:
            return item
    return None


def marker_relative_hexdump(
    observation: EventObservation,
    *,
    width: int = 16,
    max_bytes: int | None = 512,
) -> str:
    raw = _capture_bytes(observation)
    if max_bytes is not None:
        raw = raw[:max_bytes]

    marker = observation.marker_offset_in_capture
    lines: list[str] = []
    for row_start in range(0, len(raw), width):
        chunk = raw[row_start:row_start + width]
        relative = row_start - marker
        hex_part = " ".join(f"{byte:02X}" for byte in chunk)
        ascii_part = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
        lines.append(f"{relative:+06d}  {hex_part:<47}  |{ascii_part}|")
    return "\n".join(lines)
