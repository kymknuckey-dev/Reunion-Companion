"""Phase 2 object classification over the neutral Discovery grammar.

Build 11 classifies consolidated structural blocks by measured behaviour.
Class IDs are deterministic hashes of canonical fingerprints. Semantic Reunion
names are intentionally not assigned here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import math
from statistics import mean, median
from typing import Iterable

from .boundary_consolidation import ConsolidatedBlock, build_consolidated_map
from .event_scanner import EventObservation
from .structural_grammar import (
    class_sequences,
    discover_grammar_classes,
    discover_block_families,
)


DATE_DESCRIPTOR = bytes.fromhex("0A 00 08 00 00 00")


@dataclass(frozen=True, slots=True)
class ObjectFingerprint:
    fingerprint_id: str
    family_key: str
    grammar_class_id: int
    prefix_group: str
    length_bucket: str
    contains_ascii: bool
    contains_place: bool
    contains_date_descriptor: bool
    binary_ratio_bucket: str
    child_candidate_bucket: str

    def canonical(self) -> str:
        return "|".join(
            [
                self.family_key,
                f"G{self.grammar_class_id}",
                self.prefix_group,
                self.length_bucket,
                f"A{int(self.contains_ascii)}",
                f"P{int(self.contains_place)}",
                f"D{int(self.contains_date_descriptor)}",
                self.binary_ratio_bucket,
                self.child_candidate_bucket,
            ]
        )


@dataclass(frozen=True, slots=True)
class ObjectObservation:
    person_id: int
    person_name: str
    date_display: str
    object_index: int
    start_relative: int
    length: int
    fingerprint: ObjectFingerprint
    previous_grammar_class: int | None
    next_grammar_class: int | None
    ascii_preview: str


@dataclass(frozen=True, slots=True)
class ObjectClassProfile:
    class_id: str
    fingerprint_id: str
    canonical_fingerprint: str
    occurrences: int
    people: int
    length_min: int
    length_max: int
    length_mean: float
    length_median: float
    place_share: float
    ascii_share: float
    date_share: float
    common_previous_class: int | None
    common_previous_share: float
    common_next_class: int | None
    common_next_share: float
    sample_person_ids: tuple[int, ...]
    sample_previews: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class SimilarClass:
    left_class_id: str
    right_class_id: str
    similarity: float
    shared_features: tuple[str, ...]
    differing_features: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClassificationSummary:
    observations: int
    structural_objects: int
    object_classes: int
    singleton_classes: int
    mean_class_population: float
    mean_confidence: float


def _capture_bytes(item: EventObservation) -> bytes:
    return bytes.fromhex(item.capture_hex) if item.capture_hex else bytes.fromhex(item.context_hex)


def _length_bucket(length: int) -> str:
    if length <= 16:
        return "L00-16"
    if length <= 32:
        return "L17-32"
    if length <= 64:
        return "L33-64"
    if length <= 128:
        return "L65-128"
    if length <= 256:
        return "L129-256"
    return "L257+"


def _binary_ratio_bucket(raw: bytes) -> str:
    if not raw:
        return "B0"
    printable = sum(1 for b in raw if 32 <= b <= 126)
    binary_ratio = 1.0 - (printable / len(raw))
    if binary_ratio < 0.25:
        return "B0-25"
    if binary_ratio < 0.50:
        return "B25-50"
    if binary_ratio < 0.75:
        return "B50-75"
    return "B75-100"


def _child_bucket(count: int) -> str:
    if count == 0:
        return "C0"
    if count == 1:
        return "C1"
    return "C2+"


def _prefix_group(block: ConsolidatedBlock) -> str:
    prefix = bytes.fromhex(block.prefix_hex)
    if prefix[:4] == b"\x06\x00\x00\x00":
        return "P06"
    if prefix[:8] == b"\x01\x00\x00\x00\x00\x00\x00\x00":
        return "P01"
    if b"[[pt" in prefix:
        return "PPLACE"
    if prefix and prefix[1:4] == b"\x00\x00\x00":
        return "PLENGTH"
    return prefix[:4].hex() if prefix else "PEMPTY"


def fingerprint_block(
    block: ConsolidatedBlock,
    raw: bytes,
    absolute_start: int,
    grammar_class_id: int,
) -> ObjectFingerprint:
    chunk = raw[absolute_start:absolute_start + block.length]
    contains_ascii = sum(1 for b in chunk if 32 <= b <= 126) >= 4
    contains_place = b"[[pt:" in chunk
    contains_date = DATE_DESCRIPTOR in chunk

    provisional = ObjectFingerprint(
        fingerprint_id="",
        family_key=block.family_key,
        grammar_class_id=grammar_class_id,
        prefix_group=_prefix_group(block),
        length_bucket=_length_bucket(block.length),
        contains_ascii=contains_ascii,
        contains_place=contains_place,
        contains_date_descriptor=contains_date,
        binary_ratio_bucket=_binary_ratio_bucket(chunk),
        child_candidate_bucket=_child_bucket(block.child_candidates),
    )
    digest = hashlib.sha1(provisional.canonical().encode("utf-8")).hexdigest()[:10].upper()
    return ObjectFingerprint(
        fingerprint_id=digest,
        family_key=provisional.family_key,
        grammar_class_id=provisional.grammar_class_id,
        prefix_group=provisional.prefix_group,
        length_bucket=provisional.length_bucket,
        contains_ascii=provisional.contains_ascii,
        contains_place=provisional.contains_place,
        contains_date_descriptor=provisional.contains_date_descriptor,
        binary_ratio_bucket=provisional.binary_ratio_bucket,
        child_candidate_bucket=provisional.child_candidate_bucket,
    )


def classify_objects(
    observations: Iterable[EventObservation],
) -> list[ObjectObservation]:
    values = list(observations)
    _, family_ids_by_key = discover_block_families(values)
    _, family_to_grammar = discover_grammar_classes(values)
    result: list[ObjectObservation] = []

    for observation in values:
        mapping = build_consolidated_map(observation)
        raw = _capture_bytes(observation)
        marker = observation.marker_offset_in_capture

        grammar_ids: list[int] = []
        for block in mapping.blocks:
            family_id = family_ids_by_key[block.family_key]
            grammar_ids.append(family_to_grammar[family_id])

        for index, block in enumerate(mapping.blocks):
            grammar_class_id = grammar_ids[index]
            absolute_start = marker + block.start_relative
            fingerprint = fingerprint_block(
                block,
                raw,
                absolute_start,
                grammar_class_id,
            )
            result.append(
                ObjectObservation(
                    person_id=observation.person_id,
                    person_name=observation.person_name,
                    date_display=observation.date_display,
                    object_index=index,
                    start_relative=block.start_relative,
                    length=block.length,
                    fingerprint=fingerprint,
                    previous_grammar_class=grammar_ids[index - 1] if index else None,
                    next_grammar_class=grammar_ids[index + 1] if index + 1 < len(grammar_ids) else None,
                    ascii_preview=block.ascii_preview,
                )
            )
    return result


def _confidence(
    occurrences: int,
    people: int,
    previous_share: float,
    next_share: float,
) -> float:
    population = min(1.0, math.log10(occurrences + 1) / 3.0)
    people_score = min(1.0, math.log10(people + 1) / 3.0)
    context = (previous_share + next_share) / 2.0
    score = 0.45 * population + 0.25 * people_score + 0.30 * context
    return max(0.0, min(1.0, score))


def object_classes(
    observations: Iterable[EventObservation],
) -> list[ObjectClassProfile]:
    objects = classify_objects(observations)
    grouped: dict[str, list[ObjectObservation]] = defaultdict(list)

    for item in objects:
        grouped[item.fingerprint.fingerprint_id].append(item)

    profiles: list[ObjectClassProfile] = []
    for fingerprint_id, members in grouped.items():
        first = members[0]
        lengths = [item.length for item in members]
        people = {item.person_id for item in members}
        previous = Counter(item.previous_grammar_class for item in members if item.previous_grammar_class is not None)
        following = Counter(item.next_grammar_class for item in members if item.next_grammar_class is not None)

        prev_id = previous.most_common(1)[0][0] if previous else None
        prev_share = previous.most_common(1)[0][1] / len(members) if previous else 0.0
        next_id = following.most_common(1)[0][0] if following else None
        next_share = following.most_common(1)[0][1] / len(members) if following else 0.0

        profiles.append(
            ObjectClassProfile(
                class_id=f"OC-{fingerprint_id}",
                fingerprint_id=fingerprint_id,
                canonical_fingerprint=first.fingerprint.canonical(),
                occurrences=len(members),
                people=len(people),
                length_min=min(lengths),
                length_max=max(lengths),
                length_mean=mean(lengths),
                length_median=median(lengths),
                place_share=sum(item.fingerprint.contains_place for item in members) / len(members),
                ascii_share=sum(item.fingerprint.contains_ascii for item in members) / len(members),
                date_share=sum(item.fingerprint.contains_date_descriptor for item in members) / len(members),
                common_previous_class=prev_id,
                common_previous_share=prev_share,
                common_next_class=next_id,
                common_next_share=next_share,
                sample_person_ids=tuple(item.person_id for item in members[:5]),
                sample_previews=tuple(item.ascii_preview for item in members[:3]),
                confidence=_confidence(len(members), len(people), prev_share, next_share),
            )
        )

    return sorted(profiles, key=lambda item: (-item.occurrences, item.class_id))


def classification_summary(
    observations: Iterable[EventObservation],
) -> ClassificationSummary:
    values = list(observations)
    objects = classify_objects(values)
    classes = object_classes(values)
    return ClassificationSummary(
        observations=len(values),
        structural_objects=len(objects),
        object_classes=len(classes),
        singleton_classes=sum(1 for item in classes if item.occurrences == 1),
        mean_class_population=(len(objects) / len(classes)) if classes else 0.0,
        mean_confidence=mean([item.confidence for item in classes]) if classes else 0.0,
    )


def find_object_class(
    observations: Iterable[EventObservation],
    class_id: str,
) -> ObjectClassProfile | None:
    normal = class_id.upper()
    if not normal.startswith("OC-"):
        normal = "OC-" + normal
    return next((item for item in object_classes(observations) if item.class_id == normal), None)


def person_object_map(
    observations: Iterable[EventObservation],
    person_id: int,
) -> list[ObjectObservation]:
    return [
        item
        for item in classify_objects(observations)
        if item.person_id == person_id
    ]


def similarity(
    left: ObjectClassProfile,
    right: ObjectClassProfile,
) -> SimilarClass:
    lf = left.canonical_fingerprint.split("|")
    rf = right.canonical_fingerprint.split("|")
    labels = [
        "family",
        "grammar",
        "prefix",
        "length",
        "ascii",
        "place",
        "date",
        "binary-ratio",
        "children",
    ]
    shared = [label for label, a, b in zip(labels, lf, rf) if a == b]
    different = [label for label, a, b in zip(labels, lf, rf) if a != b]
    score = len(shared) / len(labels)
    return SimilarClass(
        left_class_id=left.class_id,
        right_class_id=right.class_id,
        similarity=score,
        shared_features=tuple(shared),
        differing_features=tuple(different),
    )


def nearest_classes(
    observations: Iterable[EventObservation],
    *,
    limit: int = 40,
) -> list[SimilarClass]:
    classes = object_classes(observations)
    pairs: list[SimilarClass] = []
    for index, left in enumerate(classes):
        for right in classes[index + 1:]:
            item = similarity(left, right)
            if item.similarity >= 0.55:
                pairs.append(item)
    return sorted(
        pairs,
        key=lambda item: (-item.similarity, item.left_class_id, item.right_class_id),
    )[:limit]


def cluster_classes(
    observations: Iterable[EventObservation],
) -> list[tuple[str, tuple[str, ...], int]]:
    """Coarse structural clusters above stable object classes."""
    grouped: dict[str, list[ObjectClassProfile]] = defaultdict(list)
    for item in object_classes(observations):
        parts = item.canonical_fingerprint.split("|")
        # family + grammar class + prefix are the stable structural core.
        key = "|".join(parts[:3])
        grouped[key].append(item)

    rows = [
        (
            f"CL-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:8].upper()}",
            tuple(item.class_id for item in sorted(members, key=lambda x: (-x.occurrences, x.class_id))),
            sum(item.occurrences for item in members),
        )
        for key, members in grouped.items()
    ]
    return sorted(rows, key=lambda row: (-row[2], row[0]))


def knowledge_document(
    observations: Iterable[EventObservation],
    *,
    source_package: str,
) -> dict:
    summary = classification_summary(observations)
    classes = object_classes(observations)
    clusters = cluster_classes(observations)
    return {
        "schema": "reunion-companion.object-classification.v1",
        "phase": "Phase 2 - Semantic Discovery",
        "build": 11,
        "source_package": source_package,
        "semantic_labels_assigned": False,
        "summary": {
            "observations": summary.observations,
            "structural_objects": summary.structural_objects,
            "object_classes": summary.object_classes,
            "singleton_classes": summary.singleton_classes,
            "mean_class_population": summary.mean_class_population,
            "mean_confidence": summary.mean_confidence,
        },
        "classes": [
            {
                "class_id": item.class_id,
                "fingerprint_id": item.fingerprint_id,
                "canonical_fingerprint": item.canonical_fingerprint,
                "occurrences": item.occurrences,
                "people": item.people,
                "length": {
                    "min": item.length_min,
                    "max": item.length_max,
                    "mean": item.length_mean,
                    "median": item.length_median,
                },
                "features": {
                    "place_share": item.place_share,
                    "ascii_share": item.ascii_share,
                    "date_share": item.date_share,
                },
                "context": {
                    "previous_grammar_class": item.common_previous_class,
                    "previous_share": item.common_previous_share,
                    "next_grammar_class": item.common_next_class,
                    "next_share": item.common_next_share,
                },
                "confidence": item.confidence,
                "sample_person_ids": list(item.sample_person_ids),
                "sample_previews": list(item.sample_previews),
            }
            for item in classes
        ],
        "clusters": [
            {
                "cluster_id": cluster_id,
                "class_ids": list(class_ids),
                "occurrences": occurrences,
            }
            for cluster_id, class_ids, occurrences in clusters
        ],
    }
