"""Neutral structural grammar discovery for Reunion object streams.

Build 9 consumes Build 8 consolidated block families and transitions and
derives higher-level structural classes and recurring sequence motifs.
It remains deliberately semantic-free.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .boundary_consolidation import (
    BlockFamily,
    build_consolidated_map,
    discover_block_families,
)
from .event_scanner import EventObservation


@dataclass(frozen=True, slots=True)
class GrammarClass:
    class_id: int
    class_key: str
    family_ids: tuple[int, ...]
    total_count: int
    member_families: int
    length_min: int
    length_max: int
    length_median: float
    dominant_prefix: str


@dataclass(frozen=True, slots=True)
class GrammarRule:
    left_class_id: int
    right_class_id: int
    count: int
    probability: float


@dataclass(frozen=True, slots=True)
class SequenceMotif:
    motif: tuple[int, ...]
    count: int
    sample_person_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class RepetitionPattern:
    class_id: int
    run_length: int
    count: int
    sample_person_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class GrammarSummary:
    observations: int
    block_families: int
    grammar_classes: int
    grammar_rules: int
    motifs: int
    repetition_patterns: int


def _family_class_key(family: BlockFamily) -> str:
    key = family.family_key

    if key.startswith("S06:"):
        parts = key.split(":")
        subtype = parts[1] if len(parts) > 1 else "????"
        return f"C06:{subtype}"

    if key == "S01":
        return "C01"

    if key == "PLACE-WRAPPER":
        return "PAYLOAD:PLACE"

    if key == "TEXT-WRAPPER":
        return "PAYLOAD:TEXT"

    if key.startswith("GEN:"):
        parts = key.split(":")
        return ":".join(parts[:3])

    return key


def discover_grammar_classes(
    observations: Iterable[EventObservation],
) -> tuple[list[GrammarClass], dict[int, int]]:
    families, _ = discover_block_families(observations)
    grouped: dict[str, list[BlockFamily]] = defaultdict(list)

    for family in families:
        grouped[_family_class_key(family)].append(family)

    sorted_groups = sorted(
        grouped.items(),
        key=lambda pair: (-sum(item.count for item in pair[1]), pair[0]),
    )

    classes: list[GrammarClass] = []
    family_to_class: dict[int, int] = {}

    for class_id, (key, members) in enumerate(sorted_groups, start=1):
        for family in members:
            family_to_class[family.family_id] = class_id

        total_count = sum(item.count for item in members)
        length_min = min(item.length_min for item in members)
        length_max = max(item.length_max for item in members)

        expanded_medians: list[float] = []
        for item in members:
            expanded_medians.extend([item.length_median] * max(1, item.count))
        length_median = median(expanded_medians) if expanded_medians else 0.0

        dominant = max(members, key=lambda item: item.count)
        classes.append(
            GrammarClass(
                class_id=class_id,
                class_key=key,
                family_ids=tuple(item.family_id for item in members),
                total_count=total_count,
                member_families=len(members),
                length_min=length_min,
                length_max=length_max,
                length_median=length_median,
                dominant_prefix=dominant.sample_prefixes[0] if dominant.sample_prefixes else "",
            )
        )

    return classes, family_to_class


def class_sequences(
    observations: Iterable[EventObservation],
) -> list[tuple[int, list[int]]]:
    values = list(observations)
    _, family_ids_by_key = discover_block_families(values)
    _, family_to_class = discover_grammar_classes(values)

    result: list[tuple[int, list[int]]] = []
    for observation in values:
        mapping = build_consolidated_map(observation)
        family_ids = [family_ids_by_key[block.family_key] for block in mapping.blocks]
        class_ids = [family_to_class[family_id] for family_id in family_ids]
        result.append((observation.person_id, class_ids))
    return result


def discover_grammar_rules(
    observations: Iterable[EventObservation],
) -> list[GrammarRule]:
    sequences = class_sequences(observations)
    edge_counts: Counter[tuple[int, int]] = Counter()
    outgoing: Counter[int] = Counter()

    for _, sequence in sequences:
        for left, right in zip(sequence, sequence[1:]):
            edge_counts[(left, right)] += 1
            outgoing[left] += 1

    return sorted(
        [
            GrammarRule(
                left_class_id=left,
                right_class_id=right,
                count=count,
                probability=(count / outgoing[left]) if outgoing[left] else 0.0,
            )
            for (left, right), count in edge_counts.items()
        ],
        key=lambda item: (-item.count, item.left_class_id, item.right_class_id),
    )


def discover_sequence_motifs(
    observations: Iterable[EventObservation],
    *,
    min_length: int = 2,
    max_length: int = 4,
    minimum_count: int = 25,
) -> list[SequenceMotif]:
    grouped: dict[tuple[int, ...], list[int]] = defaultdict(list)

    for person_id, sequence in class_sequences(observations):
        for length in range(min_length, max_length + 1):
            if len(sequence) < length:
                continue
            for start in range(0, len(sequence) - length + 1):
                motif = tuple(sequence[start:start + length])
                grouped[motif].append(person_id)

    motifs = [
        SequenceMotif(
            motif=motif,
            count=len(person_ids),
            sample_person_ids=tuple(person_ids[:5]),
        )
        for motif, person_ids in grouped.items()
        if len(person_ids) >= minimum_count
    ]

    return sorted(motifs, key=lambda item: (-item.count, -len(item.motif), item.motif))


def discover_repetition_patterns(
    observations: Iterable[EventObservation],
    *,
    minimum_count: int = 10,
) -> list[RepetitionPattern]:
    grouped: dict[tuple[int, int], list[int]] = defaultdict(list)

    for person_id, sequence in class_sequences(observations):
        if not sequence:
            continue
        current = sequence[0]
        run = 1
        for class_id in sequence[1:]:
            if class_id == current:
                run += 1
            else:
                if run >= 2:
                    grouped[(current, run)].append(person_id)
                current = class_id
                run = 1
        if run >= 2:
            grouped[(current, run)].append(person_id)

    patterns = [
        RepetitionPattern(
            class_id=class_id,
            run_length=run_length,
            count=len(person_ids),
            sample_person_ids=tuple(person_ids[:5]),
        )
        for (class_id, run_length), person_ids in grouped.items()
        if len(person_ids) >= minimum_count
    ]

    return sorted(
        patterns,
        key=lambda item: (-item.count, item.class_id, item.run_length),
    )


def grammar_summary(
    observations: Iterable[EventObservation],
) -> GrammarSummary:
    values = list(observations)
    families, _ = discover_block_families(values)
    classes, _ = discover_grammar_classes(values)
    rules = discover_grammar_rules(values)
    motifs = discover_sequence_motifs(values)
    repetitions = discover_repetition_patterns(values)

    return GrammarSummary(
        observations=len(values),
        block_families=len(families),
        grammar_classes=len(classes),
        grammar_rules=len(rules),
        motifs=len(motifs),
        repetition_patterns=len(repetitions),
    )
