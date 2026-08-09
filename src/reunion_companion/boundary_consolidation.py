"""Boundary consolidation and neutral block-family discovery.

Build 8 consumes Build 7 candidate boundaries and collapses internal-field
candidates into higher-level recurring block families. It deliberately
avoids assigning semantic Reunion names.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable

from .event_scanner import EventObservation
from .object_boundary import BoundaryCandidate, candidate_boundaries


@dataclass(frozen=True, slots=True)
class ConsolidatedBoundary:
    relative_offset: int
    absolute_capture_offset: int
    score: float
    pattern_hex: str
    reasons: tuple[str, ...]
    suppressed_children: int


@dataclass(frozen=True, slots=True)
class ConsolidatedBlock:
    start_relative: int
    end_relative: int
    length: int
    family_key: str
    prefix_hex: str
    field_words: tuple[int, ...]
    ascii_preview: str
    child_candidates: int


@dataclass(frozen=True, slots=True)
class ConsolidatedPersonMap:
    person_id: int
    person_name: str
    date_display: str
    boundaries: tuple[ConsolidatedBoundary, ...]
    blocks: tuple[ConsolidatedBlock, ...]


@dataclass(frozen=True, slots=True)
class BlockFamily:
    family_id: int
    family_key: str
    count: int
    length_min: int
    length_max: int
    length_mean: float
    length_median: float
    sample_person_ids: tuple[int, ...]
    sample_offsets: tuple[int, ...]
    sample_prefixes: tuple[str, ...]
    common_field_words: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class FamilyTransition:
    left_family_id: int
    right_family_id: int
    count: int


@dataclass(frozen=True, slots=True)
class ConsolidationSummary:
    observations: int
    raw_candidates: int
    consolidated_boundaries: int
    suppressed_candidates: int
    block_families: int
    family_transitions: int


def _capture_bytes(item: EventObservation) -> bytes:
    return bytes.fromhex(item.capture_hex) if item.capture_hex else bytes.fromhex(item.context_hex)


def _u16_words(raw: bytes, start: int, count: int = 6) -> tuple[int, ...]:
    values: list[int] = []
    for index in range(count):
        pos = start + index * 2
        if pos + 2 > len(raw):
            break
        values.append(int.from_bytes(raw[pos:pos+2], "little"))
    return tuple(values)


def _ascii_preview(raw: bytes, limit: int = 48) -> str:
    chars = []
    for byte in raw[:limit]:
        chars.append(chr(byte) if 32 <= byte <= 126 else ".")
    return "".join(chars).rstrip(".")


def _is_internal_field_candidate(
    parent: BoundaryCandidate,
    child: BoundaryCandidate,
    raw: bytes,
) -> bool:
    """Return True when child is likely an internal field of parent.

    Evidence from Build 7 shows many candidate pairs separated by 4 bytes where
    the later candidate begins with the field words already present immediately
    after a 06 00 00 00 marker. Those should be consolidated.
    """
    delta = child.absolute_capture_offset - parent.absolute_capture_offset
    if delta <= 0:
        return False

    # Extremely common Build 7 false split:
    # 06 00 00 00 | xx 00 yy 00 ...   then candidate again at +4
    if raw[parent.absolute_capture_offset:parent.absolute_capture_offset+4] == b"\x06\x00\x00\x00":
        if delta in {4, 8}:
            return True

    # Place-token wrapper candidates such as:
    # 0e 00 00 00 [[pt:...]]
    # are payload wrappers, not peer-level objects, when found shortly after a
    # stronger preceding structural marker.
    child_prefix = raw[child.absolute_capture_offset:child.absolute_capture_offset+8]
    if len(child_prefix) >= 8 and child_prefix[4:8] == b"[[pt":
        if delta <= 24:
            return True

    # Text-length wrappers (nn 00 00 00 + printable bytes) are usually payload
    # blocks rather than peer-level objects if tightly nested.
    if delta <= 24 and child.absolute_capture_offset + 8 <= len(raw):
        chunk = raw[child.absolute_capture_offset:child.absolute_capture_offset+8]
        if chunk[1:4] == b"\x00\x00\x00":
            printable = sum(1 for b in chunk[4:8] if 32 <= b <= 126)
            if printable >= 2:
                return True

    return False


def consolidate_boundaries(
    observation: EventObservation,
    *,
    minimum_score: float = 0.35,
) -> list[ConsolidatedBoundary]:
    raw = _capture_bytes(observation)
    raw_candidates = candidate_boundaries(observation, minimum_score=minimum_score)
    if not raw_candidates:
        return []

    selected: list[BoundaryCandidate] = []
    suppressed: Counter[int] = Counter()

    for candidate in raw_candidates:
        if not selected:
            selected.append(candidate)
            continue

        parent = selected[-1]
        if _is_internal_field_candidate(parent, candidate, raw):
            suppressed[parent.relative_offset] += 1
            continue

        selected.append(candidate)

    return [
        ConsolidatedBoundary(
            relative_offset=item.relative_offset,
            absolute_capture_offset=item.absolute_capture_offset,
            score=item.score,
            pattern_hex=item.pattern_hex,
            reasons=item.reasons,
            suppressed_children=suppressed[item.relative_offset],
        )
        for item in selected
    ]


def _family_key(raw: bytes, start: int) -> str:
    """Create a neutral structural family key from the first 12 bytes.

    The key intentionally normalises payload-like values while retaining
    recurring structural words.
    """
    words = _u16_words(raw, start, 6)
    if not words:
        return "EMPTY"

    # Strongest observed peer-level structural marker family.
    if raw[start:start+4] == b"\x06\x00\x00\x00":
        second = words[2] if len(words) > 2 else -1
        third = words[3] if len(words) > 3 else -1
        return f"S06:{second:04x}:{third:04x}"

    # 01 00 00 00... family seen 2,500+ times in Build 7.
    if raw[start:start+8] == b"\x01\x00\x00\x00\x00\x00\x00\x00":
        return "S01"

    # Length-prefixed place wrapper.
    if start + 8 <= len(raw) and raw[start+4:start+8] == b"[[pt":
        return "PLACE-WRAPPER"

    # Length-prefixed printable payload wrapper.
    if start + 8 <= len(raw) and raw[start+1:start+4] == b"\x00\x00\x00":
        printable = sum(1 for b in raw[start+4:start+8] if 32 <= b <= 126)
        if printable >= 2:
            return "TEXT-WRAPPER"

    # Generic first four little-endian words, but normalise high-entropy words.
    normalised = []
    for word in words[:4]:
        normalised.append(f"{word:04x}" if word <= 0x0200 else "xxxx")
    return "GEN:" + ":".join(normalised)


def build_consolidated_map(
    observation: EventObservation,
    *,
    minimum_score: float = 0.35,
) -> ConsolidatedPersonMap:
    raw = _capture_bytes(observation)
    marker = observation.marker_offset_in_capture
    boundaries = consolidate_boundaries(observation, minimum_score=minimum_score)

    blocks: list[ConsolidatedBlock] = []
    starts = [item.absolute_capture_offset for item in boundaries]

    for index, boundary in enumerate(boundaries):
        start = boundary.absolute_capture_offset
        end = starts[index + 1] if index + 1 < len(starts) else len(raw)
        if end <= start:
            continue
        chunk = raw[start:end]
        blocks.append(
            ConsolidatedBlock(
                start_relative=start - marker,
                end_relative=end - marker,
                length=end - start,
                family_key=_family_key(raw, start),
                prefix_hex=chunk[:12].hex(" "),
                field_words=_u16_words(raw, start, 6),
                ascii_preview=_ascii_preview(chunk),
                child_candidates=boundary.suppressed_children,
            )
        )

    return ConsolidatedPersonMap(
        person_id=observation.person_id,
        person_name=observation.person_name,
        date_display=observation.date_display,
        boundaries=tuple(boundaries),
        blocks=tuple(blocks),
    )


def discover_block_families(
    observations: Iterable[EventObservation],
    *,
    minimum_score: float = 0.35,
) -> tuple[list[BlockFamily], dict[str, int]]:
    grouped: dict[str, list[tuple[int, ConsolidatedBlock]]] = defaultdict(list)

    for observation in observations:
        mapping = build_consolidated_map(observation, minimum_score=minimum_score)
        for block in mapping.blocks:
            grouped[block.family_key].append((observation.person_id, block))

    sorted_groups = sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0]))
    family_ids: dict[str, int] = {}
    families: list[BlockFamily] = []

    for family_id, (key, values) in enumerate(sorted_groups, start=1):
        family_ids[key] = family_id
        lengths = [block.length for _, block in values]

        word_columns: list[list[int]] = [[] for _ in range(6)]
        for _, block in values:
            for index, word in enumerate(block.field_words[:6]):
                word_columns[index].append(word)

        common_words: list[int] = []
        for column in word_columns:
            if not column:
                break
            common_words.append(Counter(column).most_common(1)[0][0])

        families.append(
            BlockFamily(
                family_id=family_id,
                family_key=key,
                count=len(values),
                length_min=min(lengths),
                length_max=max(lengths),
                length_mean=mean(lengths),
                length_median=median(lengths),
                sample_person_ids=tuple(person_id for person_id, _ in values[:5]),
                sample_offsets=tuple(block.start_relative for _, block in values[:5]),
                sample_prefixes=tuple(block.prefix_hex for _, block in values[:3]),
                common_field_words=tuple(common_words),
            )
        )

    return families, family_ids


def discover_family_transitions(
    observations: Iterable[EventObservation],
    *,
    minimum_score: float = 0.35,
) -> list[FamilyTransition]:
    families, family_ids = discover_block_families(
        observations, minimum_score=minimum_score
    )
    counts: Counter[tuple[int, int]] = Counter()

    for observation in observations:
        mapping = build_consolidated_map(observation, minimum_score=minimum_score)
        ids = [family_ids[block.family_key] for block in mapping.blocks]
        for left, right in zip(ids, ids[1:]):
            counts[(left, right)] += 1

    return sorted(
        [
            FamilyTransition(left_family_id=left, right_family_id=right, count=count)
            for (left, right), count in counts.items()
        ],
        key=lambda item: (-item.count, item.left_family_id, item.right_family_id),
    )


def consolidation_summary(
    observations: Iterable[EventObservation],
    *,
    minimum_score: float = 0.35,
) -> ConsolidationSummary:
    values = list(observations)
    raw_count = 0
    consolidated_count = 0

    for item in values:
        raw_count += len(candidate_boundaries(item, minimum_score=minimum_score))
        consolidated_count += len(consolidate_boundaries(item, minimum_score=minimum_score))

    families, _ = discover_block_families(values, minimum_score=minimum_score)
    transitions = discover_family_transitions(values, minimum_score=minimum_score)

    return ConsolidationSummary(
        observations=len(values),
        raw_candidates=raw_count,
        consolidated_boundaries=consolidated_count,
        suppressed_candidates=raw_count - consolidated_count,
        block_families=len(families),
        family_transitions=len(transitions),
    )
