"""Phase 2 Build 12 semantic alignment and Object Class graph analysis.

The layer operates on Build 11 deterministic structural Object Classes.
"Semantic alignment" means measured structural/contextual association only;
it does not assign Reunion semantic field names.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import log2
from typing import Iterable

from .event_scanner import EventObservation
from .object_classification import (
    ObjectObservation,
    classify_objects,
    object_classes,
)


@dataclass(frozen=True, slots=True)
class AlignmentEdge:
    source_class_id: str
    target_class_id: str
    count: int
    source_probability: float
    target_probability: float
    lift: float
    confidence: float


@dataclass(frozen=True, slots=True)
class CooccurrencePair:
    left_class_id: str
    right_class_id: str
    people_together: int
    left_people: int
    right_people: int
    jaccard: float
    lift: float


@dataclass(frozen=True, slots=True)
class ObjectGraphNode:
    class_id: str
    occurrences: int
    people: int
    in_weight: int
    out_weight: int
    in_degree: int
    out_degree: int
    start_count: int
    end_count: int
    centrality: float


@dataclass(frozen=True, slots=True)
class AlignmentProfile:
    class_id: str
    occurrences: int
    people: int
    predecessors: tuple[AlignmentEdge, ...]
    successors: tuple[AlignmentEdge, ...]
    cooccurring: tuple[CooccurrencePair, ...]
    structural_role: str
    best_predecessor: str | None
    best_successor: str | None


@dataclass(frozen=True, slots=True)
class ObjectFamily:
    family_id: str
    class_ids: tuple[str, ...]
    total_occurrences: int
    people_covered: int
    strongest_edge_count: int


@dataclass(frozen=True, slots=True)
class PersonObjectPath:
    person_id: int
    person_name: str
    class_ids: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class AlignmentSummary:
    observations: int
    classified_objects: int
    object_classes: int
    directed_edges: int
    high_confidence_edges: int
    cooccurrence_pairs: int
    graph_families: int


def _class_id(item: ObjectObservation) -> str:
    return f"OC-{item.fingerprint.fingerprint_id}"


def object_sequences(
    observations: Iterable[EventObservation],
) -> list[tuple[int, str, list[str]]]:
    grouped: dict[int, list[ObjectObservation]] = defaultdict(list)
    names: dict[int, str] = {}

    for item in classify_objects(observations):
        grouped[item.person_id].append(item)
        names[item.person_id] = item.person_name

    result: list[tuple[int, str, list[str]]] = []
    for person_id, items in grouped.items():
        ordered = sorted(items, key=lambda item: item.object_index)
        result.append(
            (
                person_id,
                names.get(person_id, ""),
                [_class_id(item) for item in ordered],
            )
        )
    return sorted(result, key=lambda row: row[0])


def alignment_edges(
    observations: Iterable[EventObservation],
) -> list[AlignmentEdge]:
    sequences = object_sequences(observations)
    edge_counts: Counter[tuple[str, str]] = Counter()
    outgoing: Counter[str] = Counter()
    incoming: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()

    for _, _, sequence in sequences:
        class_counts.update(sequence)
        for source, target in zip(sequence, sequence[1:]):
            edge_counts[(source, target)] += 1
            outgoing[source] += 1
            incoming[target] += 1

    total_objects = sum(class_counts.values())
    edges: list[AlignmentEdge] = []

    for (source, target), count in edge_counts.items():
        source_probability = count / outgoing[source] if outgoing[source] else 0.0
        target_probability = count / incoming[target] if incoming[target] else 0.0
        target_base = class_counts[target] / total_objects if total_objects else 0.0
        lift = source_probability / target_base if target_base else 0.0

        population = min(1.0, log2(count + 1) / 10.0)
        directional = (source_probability + target_probability) / 2.0
        lift_score = min(1.0, lift / 10.0)
        confidence = min(
            1.0,
            0.45 * population + 0.40 * directional + 0.15 * lift_score,
        )

        edges.append(
            AlignmentEdge(
                source_class_id=source,
                target_class_id=target,
                count=count,
                source_probability=source_probability,
                target_probability=target_probability,
                lift=lift,
                confidence=confidence,
            )
        )

    return sorted(
        edges,
        key=lambda edge: (
            -edge.count,
            -edge.confidence,
            edge.source_class_id,
            edge.target_class_id,
        ),
    )


def cooccurrence_pairs(
    observations: Iterable[EventObservation],
    *,
    minimum_people: int = 5,
) -> list[CooccurrencePair]:
    sequences = object_sequences(observations)
    people_by_class: dict[str, set[int]] = defaultdict(set)

    for person_id, _, sequence in sequences:
        for class_id in set(sequence):
            people_by_class[class_id].add(person_id)

    classes = sorted(people_by_class)
    population = len(sequences)
    pairs: list[CooccurrencePair] = []

    for index, left in enumerate(classes):
        left_people = people_by_class[left]
        for right in classes[index + 1:]:
            right_people = people_by_class[right]
            together = left_people & right_people
            if len(together) < minimum_people:
                continue
            union = left_people | right_people
            expected = (
                len(left_people) * len(right_people) / population
                if population
                else 0.0
            )
            pairs.append(
                CooccurrencePair(
                    left_class_id=left,
                    right_class_id=right,
                    people_together=len(together),
                    left_people=len(left_people),
                    right_people=len(right_people),
                    jaccard=(len(together) / len(union)) if union else 0.0,
                    lift=(len(together) / expected) if expected else 0.0,
                )
            )

    return sorted(
        pairs,
        key=lambda item: (
            -item.people_together,
            -item.jaccard,
            item.left_class_id,
            item.right_class_id,
        ),
    )


def object_graph(
    observations: Iterable[EventObservation],
) -> tuple[list[ObjectGraphNode], list[AlignmentEdge]]:
    values = list(observations)
    classes = object_classes(values)
    profiles = {item.class_id: item for item in classes}
    sequences = object_sequences(values)
    edges = alignment_edges(values)

    incoming_weight: Counter[str] = Counter()
    outgoing_weight: Counter[str] = Counter()
    predecessors: dict[str, set[str]] = defaultdict(set)
    successors: dict[str, set[str]] = defaultdict(set)
    starts: Counter[str] = Counter()
    ends: Counter[str] = Counter()

    for _, _, sequence in sequences:
        if sequence:
            starts[sequence[0]] += 1
            ends[sequence[-1]] += 1

    for edge in edges:
        outgoing_weight[edge.source_class_id] += edge.count
        incoming_weight[edge.target_class_id] += edge.count
        successors[edge.source_class_id].add(edge.target_class_id)
        predecessors[edge.target_class_id].add(edge.source_class_id)

    max_weight = max(
        (
            incoming_weight[class_id] + outgoing_weight[class_id]
            for class_id in profiles
        ),
        default=1,
    )
    max_degree = max(
        (
            len(predecessors[class_id]) + len(successors[class_id])
            for class_id in profiles
        ),
        default=1,
    )

    nodes: list[ObjectGraphNode] = []
    for class_id, profile in profiles.items():
        weight = incoming_weight[class_id] + outgoing_weight[class_id]
        degree = len(predecessors[class_id]) + len(successors[class_id])
        centrality = (
            0.65 * (weight / max_weight if max_weight else 0.0)
            + 0.35 * (degree / max_degree if max_degree else 0.0)
        )
        nodes.append(
            ObjectGraphNode(
                class_id=class_id,
                occurrences=profile.occurrences,
                people=profile.people,
                in_weight=incoming_weight[class_id],
                out_weight=outgoing_weight[class_id],
                in_degree=len(predecessors[class_id]),
                out_degree=len(successors[class_id]),
                start_count=starts[class_id],
                end_count=ends[class_id],
                centrality=centrality,
            )
        )

    return (
        sorted(
            nodes,
            key=lambda node: (-node.centrality, -node.occurrences, node.class_id),
        ),
        edges,
    )


def _role(node: ObjectGraphNode) -> str:
    if node.start_count and node.in_degree == 0:
        return "entry-like"
    if node.end_count and node.out_degree == 0:
        return "terminal-like"
    if node.centrality >= 0.50:
        return "hub-like"
    if node.in_degree > 1 and node.out_degree <= 1:
        return "convergence-like"
    if node.out_degree > 1 and node.in_degree <= 1:
        return "branch-like"
    return "intermediate"


def alignment_profile(
    observations: Iterable[EventObservation],
    class_id: str,
) -> AlignmentProfile | None:
    values = list(observations)
    normal = class_id.upper()
    if not normal.startswith("OC-"):
        normal = "OC-" + normal

    classes = {item.class_id: item for item in object_classes(values)}
    profile = classes.get(normal)
    if profile is None:
        return None

    nodes, edges = object_graph(values)
    node = next(item for item in nodes if item.class_id == normal)

    predecessors = sorted(
        [edge for edge in edges if edge.target_class_id == normal],
        key=lambda edge: (-edge.count, -edge.confidence),
    )
    successors = sorted(
        [edge for edge in edges if edge.source_class_id == normal],
        key=lambda edge: (-edge.count, -edge.confidence),
    )
    cooccurring = [
        pair
        for pair in cooccurrence_pairs(values)
        if normal in (pair.left_class_id, pair.right_class_id)
    ][:20]

    return AlignmentProfile(
        class_id=normal,
        occurrences=profile.occurrences,
        people=profile.people,
        predecessors=tuple(predecessors[:20]),
        successors=tuple(successors[:20]),
        cooccurring=tuple(cooccurring),
        structural_role=_role(node),
        best_predecessor=predecessors[0].source_class_id if predecessors else None,
        best_successor=successors[0].target_class_id if successors else None,
    )


def object_families(
    observations: Iterable[EventObservation],
    *,
    minimum_edge_count: int = 10,
    minimum_confidence: float = 0.45,
) -> list[ObjectFamily]:
    values = list(observations)
    classes = {item.class_id: item for item in object_classes(values)}
    edges = alignment_edges(values)

    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.count < minimum_edge_count or edge.confidence < minimum_confidence:
            continue
        adjacency[edge.source_class_id].add(edge.target_class_id)
        adjacency[edge.target_class_id].add(edge.source_class_id)

    people_by_class: dict[str, set[int]] = defaultdict(set)
    for person_id, _, sequence in object_sequences(values):
        for class_id in set(sequence):
            people_by_class[class_id].add(person_id)

    visited: set[str] = set()
    families: list[ObjectFamily] = []
    for root in sorted(classes):
        if root in visited:
            continue
        queue = deque([root])
        component: list[str] = []
        visited.add(root)

        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbour in adjacency[current]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)

        covered: set[int] = set()
        for class_id in component:
            covered |= people_by_class[class_id]

        internal_edges = [
            edge.count
            for edge in edges
            if (
                edge.source_class_id in component
                and edge.target_class_id in component
            )
        ]

        families.append(
            ObjectFamily(
                family_id=f"OF-{len(families)+1:04d}",
                class_ids=tuple(sorted(component)),
                total_occurrences=sum(
                    classes[class_id].occurrences for class_id in component
                ),
                people_covered=len(covered),
                strongest_edge_count=max(internal_edges, default=0),
            )
        )

    return sorted(
        families,
        key=lambda family: (
            -family.total_occurrences,
            -len(family.class_ids),
            family.family_id,
        ),
    )


def person_object_path(
    observations: Iterable[EventObservation],
    person_id: int,
) -> PersonObjectPath | None:
    for pid, name, sequence in object_sequences(observations):
        if pid == person_id:
            return PersonObjectPath(
                person_id=pid,
                person_name=name,
                class_ids=tuple(sequence),
                edges=tuple(zip(sequence, sequence[1:])),
            )
    return None


def alignment_summary(
    observations: Iterable[EventObservation],
) -> AlignmentSummary:
    values = list(observations)
    objects = classify_objects(values)
    classes = object_classes(values)
    edges = alignment_edges(values)
    pairs = cooccurrence_pairs(values)
    families = object_families(values)

    return AlignmentSummary(
        observations=len(values),
        classified_objects=len(objects),
        object_classes=len(classes),
        directed_edges=len(edges),
        high_confidence_edges=sum(
            1
            for edge in edges
            if edge.count >= 25 and edge.confidence >= 0.60
        ),
        cooccurrence_pairs=len(pairs),
        graph_families=len(families),
    )


def alignment_knowledge(
    observations: Iterable[EventObservation],
    *,
    source_package: str,
) -> dict:
    values = list(observations)
    summary = alignment_summary(values)
    nodes, edges = object_graph(values)
    families = object_families(values)
    pairs = cooccurrence_pairs(values)

    return {
        "schema": "reunion-companion.semantic-alignment.v1",
        "phase": "Phase 2 - Semantic Discovery",
        "build": 12,
        "source_package": source_package,
        "semantic_labels_assigned": False,
        "summary": {
            "observations": summary.observations,
            "classified_objects": summary.classified_objects,
            "object_classes": summary.object_classes,
            "directed_edges": summary.directed_edges,
            "high_confidence_edges": summary.high_confidence_edges,
            "cooccurrence_pairs": summary.cooccurrence_pairs,
            "graph_families": summary.graph_families,
        },
        "nodes": [
            {
                "class_id": node.class_id,
                "occurrences": node.occurrences,
                "people": node.people,
                "in_weight": node.in_weight,
                "out_weight": node.out_weight,
                "in_degree": node.in_degree,
                "out_degree": node.out_degree,
                "start_count": node.start_count,
                "end_count": node.end_count,
                "centrality": node.centrality,
                "role": _role(node),
            }
            for node in nodes
        ],
        "edges": [
            {
                "source": edge.source_class_id,
                "target": edge.target_class_id,
                "count": edge.count,
                "source_probability": edge.source_probability,
                "target_probability": edge.target_probability,
                "lift": edge.lift,
                "confidence": edge.confidence,
            }
            for edge in edges
        ],
        "families": [
            {
                "family_id": family.family_id,
                "class_ids": list(family.class_ids),
                "total_occurrences": family.total_occurrences,
                "people_covered": family.people_covered,
                "strongest_edge_count": family.strongest_edge_count,
            }
            for family in families
        ],
        "top_cooccurrence_pairs": [
            {
                "left": pair.left_class_id,
                "right": pair.right_class_id,
                "people_together": pair.people_together,
                "jaccard": pair.jaccard,
                "lift": pair.lift,
            }
            for pair in pairs[:200]
        ],
    }
