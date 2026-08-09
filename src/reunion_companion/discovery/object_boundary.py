"""Candidate object-boundary discovery for Reunion person-record captures.

Build 7 deliberately speaks in terms of *candidate boundaries*, *block
signatures*, and *transition patterns*. It does not assign semantic event names.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable

from .event_scanner import EventObservation


@dataclass(frozen=True, slots=True)
class BoundaryCandidate:
    relative_offset: int
    absolute_capture_offset: int
    marker_distance: int
    pattern_hex: str
    pattern_width: int
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObjectBlock:
    start_relative: int
    end_relative: int
    length: int
    signature_hex: str
    ascii_preview: str


@dataclass(frozen=True, slots=True)
class PersonBoundaryMap:
    person_id: int
    person_name: str
    date_display: str
    boundaries: tuple[BoundaryCandidate, ...]
    blocks: tuple[ObjectBlock, ...]


@dataclass(frozen=True, slots=True)
class BoundarySignature:
    signature_hex: str
    count: int
    sample_person_ids: tuple[int, ...]
    sample_offsets: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class TransitionSignature:
    left_signature: str
    right_signature: str
    count: int


@dataclass(frozen=True, slots=True)
class BoundaryCorpusSummary:
    observations: int
    observations_with_boundaries: int
    total_boundaries: int
    mean_boundaries: float
    median_boundaries: float
    unique_boundary_signatures: int
    unique_transitions: int


# Known verified structure that should not itself be treated as a new object
# boundary. The scanner looks primarily *after* the current event/date object.
_DATE_MARKER = bytes.fromhex("0A 00 08 00 00 00")
_EVENT_SIGNATURE = bytes.fromhex("01 00 00 00 00 00 00 00 06 00 00 00")


def _capture_bytes(item: EventObservation) -> bytes:
    return bytes.fromhex(item.capture_hex) if item.capture_hex else bytes.fromhex(item.context_hex)


def _ascii_preview(raw: bytes, limit: int = 36) -> str:
    text = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in raw[:limit])
    return text.rstrip(".")


def _candidate_score(raw: bytes, start: int, marker: int) -> tuple[float, list[str]]:
    """Score a possible object start using structural evidence only."""
    reasons: list[str] = []
    score = 0.0

    # Common little-endian short length/tag shape: nn 00 xx 00
    if start + 4 <= len(raw):
        a, b, c, d = raw[start:start+4]
        if b == 0 and d == 0 and a != 0:
            score += 0.22
            reasons.append("two little-endian 16-bit values")
        if c in {0x08, 0x0B, 0x0D, 0x14, 0x15, 0x16, 0x1E, 0x23, 0x34, 0x3C, 0x3E, 0x3F, 0x4A, 0x4C, 0x56}:
            score += 0.08
            reasons.append("recurring field/tag byte")

    # Repeated 06 00 00 00 structural marker observed extensively in Builds 3-6.
    if raw[start:start+4] == b"\x06\x00\x00\x00":
        score += 0.45
        reasons.append("recurring 06 00 00 00 structural marker")

    # Existing generic date descriptor often appears shortly after a block start.
    lookahead = raw[start:min(len(raw), start + 48)]
    date_pos = lookahead.find(_DATE_MARKER)
    if date_pos >= 0:
        score += 0.22
        reasons.append(f"date descriptor within +{date_pos}")

    # Place reference tokens are strong structural evidence.
    place_pos = lookahead.find(b"[[pt:")
    if place_pos >= 0:
        score += 0.12
        reasons.append(f"place token within +{place_pos}")

    # Printable payload shortly after header.
    printable = sum(1 for byte in lookahead[:32] if 32 <= byte <= 126)
    if printable >= 8:
        score += 0.08
        reasons.append("printable payload nearby")

    # Candidate should normally be after marker for Build 7 stream analysis.
    relative = start - marker
    if relative >= 11:
        score += 0.05
        reasons.append("post-date position")

    return min(score, 1.0), reasons


def candidate_boundaries(
    observation: EventObservation,
    *,
    minimum_score: float = 0.35,
    minimum_relative: int = 11,
    maximum_relative: int = 480,
) -> list[BoundaryCandidate]:
    raw = _capture_bytes(observation)
    marker = observation.marker_offset_in_capture

    candidates: list[BoundaryCandidate] = []
    search_start = max(0, marker + minimum_relative)
    search_end = min(len(raw) - 4, marker + maximum_relative)

    for start in range(search_start, search_end + 1):
        score, reasons = _candidate_score(raw, start, marker)
        if score < minimum_score:
            continue

        # Suppress obvious continuation bytes inside [[pt:n]] tokens.
        token_window_start = max(0, start - 12)
        token_prefix = raw[token_window_start:start].rfind(b"[[pt:")
        token_close = raw[token_window_start:start].rfind(b"]]")
        if token_prefix > token_close:
            continue

        candidates.append(
            BoundaryCandidate(
                relative_offset=start - marker,
                absolute_capture_offset=start,
                marker_distance=start - marker,
                pattern_hex=raw[start:start+8].hex(" "),
                pattern_width=min(8, len(raw) - start),
                score=score,
                reasons=tuple(reasons),
            )
        )

    # Non-maximum suppression: keep strongest candidate in a 4-byte neighbourhood.
    selected: list[BoundaryCandidate] = []
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.relative_offset)):
        if any(abs(candidate.relative_offset - existing.relative_offset) <= 3 for existing in selected):
            continue
        selected.append(candidate)

    return sorted(selected, key=lambda item: item.relative_offset)


def build_person_boundary_map(
    observation: EventObservation,
    *,
    minimum_score: float = 0.35,
) -> PersonBoundaryMap:
    raw = _capture_bytes(observation)
    marker = observation.marker_offset_in_capture
    boundaries = candidate_boundaries(observation, minimum_score=minimum_score)

    starts = [item.absolute_capture_offset for item in boundaries]
    blocks: list[ObjectBlock] = []

    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(raw)
        if end <= start:
            continue
        chunk = raw[start:end]
        blocks.append(
            ObjectBlock(
                start_relative=start - marker,
                end_relative=end - marker,
                length=end - start,
                signature_hex=chunk[:12].hex(" "),
                ascii_preview=_ascii_preview(chunk),
            )
        )

    return PersonBoundaryMap(
        person_id=observation.person_id,
        person_name=observation.person_name,
        date_display=observation.date_display,
        boundaries=tuple(boundaries),
        blocks=tuple(blocks),
    )


def boundary_signatures(
    observations: Iterable[EventObservation],
    *,
    minimum_score: float = 0.35,
    signature_width: int = 8,
) -> list[BoundarySignature]:
    grouped: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for observation in observations:
        raw = _capture_bytes(observation)
        marker = observation.marker_offset_in_capture
        for candidate in candidate_boundaries(observation, minimum_score=minimum_score):
            start = candidate.absolute_capture_offset
            signature = raw[start:start+signature_width].hex(" ")
            grouped[signature].append((observation.person_id, start - marker))

    return sorted(
        [
            BoundarySignature(
                signature_hex=signature,
                count=len(values),
                sample_person_ids=tuple(person_id for person_id, _ in values[:5]),
                sample_offsets=tuple(offset for _, offset in values[:5]),
            )
            for signature, values in grouped.items()
        ],
        key=lambda item: (-item.count, item.signature_hex),
    )


def transition_signatures(
    observations: Iterable[EventObservation],
    *,
    minimum_score: float = 0.35,
    signature_width: int = 8,
) -> list[TransitionSignature]:
    counts: Counter[tuple[str, str]] = Counter()

    for observation in observations:
        mapping = build_person_boundary_map(observation, minimum_score=minimum_score)
        signatures = [block.signature_hex[: signature_width * 3 - 1] for block in mapping.blocks]
        for left, right in zip(signatures, signatures[1:]):
            counts[(left, right)] += 1

    return sorted(
        [
            TransitionSignature(left_signature=left, right_signature=right, count=count)
            for (left, right), count in counts.items()
        ],
        key=lambda item: (-item.count, item.left_signature, item.right_signature),
    )


def corpus_summary(
    observations: Iterable[EventObservation],
    *,
    minimum_score: float = 0.35,
) -> BoundaryCorpusSummary:
    values = list(observations)
    maps = [build_person_boundary_map(item, minimum_score=minimum_score) for item in values]
    counts = [len(item.boundaries) for item in maps]

    signatures = boundary_signatures(values, minimum_score=minimum_score)
    transitions = transition_signatures(values, minimum_score=minimum_score)

    return BoundaryCorpusSummary(
        observations=len(values),
        observations_with_boundaries=sum(1 for count in counts if count),
        total_boundaries=sum(counts),
        mean_boundaries=mean(counts) if counts else 0.0,
        median_boundaries=median(counts) if counts else 0.0,
        unique_boundary_signatures=len(signatures),
        unique_transitions=len(transitions),
    )
