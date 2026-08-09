"""Directed graph analysis over the neutral structural grammar.

Build 10 converts Build 9 class sequences into a graph of neutral grammar
classes and weighted transitions. The graph remains semantic-free.
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from .event_scanner import EventObservation
from .structural_grammar import class_sequences, discover_grammar_classes


@dataclass(frozen=True, slots=True)
class GraphNode:
    class_id: int
    class_key: str
    occurrences: int
    in_weight: int
    out_weight: int
    in_degree: int
    out_degree: int
    root_count: int
    leaf_count: int
    hub_score: float


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: int
    target: int
    count: int
    probability: float


@dataclass(frozen=True, slots=True)
class SuccessorProfile:
    class_id: int
    total_outgoing: int
    successors: tuple[tuple[int, int, float], ...]
    mandatory_successor: int | None


@dataclass(frozen=True, slots=True)
class GraphMotif:
    motif_type: str
    classes: tuple[int, ...]
    count: int
    sample_person_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PersonGraph:
    person_id: int
    sequence: tuple[int, ...]
    nodes: tuple[int, ...]
    edges: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class GraphSummary:
    observations: int
    nodes: int
    edges: int
    roots: int
    leaves: int
    hubs: int
    mandatory_successors: int
    motifs: int


def build_graph(
    observations: Iterable[EventObservation],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    values = list(observations)
    classes, _ = discover_grammar_classes(values)
    class_by_id = {item.class_id: item for item in classes}
    sequences = class_sequences(values)

    node_occurrences: Counter[int] = Counter()
    edge_counts: Counter[tuple[int, int]] = Counter()
    outgoing: Counter[int] = Counter()
    incoming: Counter[int] = Counter()
    roots: Counter[int] = Counter()
    leaves: Counter[int] = Counter()
    successors: dict[int, set[int]] = defaultdict(set)
    predecessors: dict[int, set[int]] = defaultdict(set)

    for _, sequence in sequences:
        node_occurrences.update(sequence)
        if sequence:
            roots[sequence[0]] += 1
            leaves[sequence[-1]] += 1
        for source, target in zip(sequence, sequence[1:]):
            edge_counts[(source, target)] += 1
            outgoing[source] += 1
            incoming[target] += 1
            successors[source].add(target)
            predecessors[target].add(source)

    edges = sorted(
        [
            GraphEdge(
                source=source,
                target=target,
                count=count,
                probability=(count / outgoing[source]) if outgoing[source] else 0.0,
            )
            for (source, target), count in edge_counts.items()
        ],
        key=lambda item: (-item.count, item.source, item.target),
    )

    max_weight = max(
        [incoming[c.class_id] + outgoing[c.class_id] for c in classes],
        default=1,
    )

    nodes = []
    for item in classes:
        cid = item.class_id
        weighted = incoming[cid] + outgoing[cid]
        degree = len(predecessors[cid]) + len(successors[cid])
        hub_score = 0.0
        if max_weight:
            hub_score = 0.7 * (weighted / max_weight)
        if classes:
            hub_score += 0.3 * (degree / max(1, len(classes) - 1))
        nodes.append(
            GraphNode(
                class_id=cid,
                class_key=item.class_key,
                occurrences=node_occurrences[cid],
                in_weight=incoming[cid],
                out_weight=outgoing[cid],
                in_degree=len(predecessors[cid]),
                out_degree=len(successors[cid]),
                root_count=roots[cid],
                leaf_count=leaves[cid],
                hub_score=hub_score,
            )
        )

    return sorted(nodes, key=lambda n: n.class_id), edges


def successor_profiles(
    observations: Iterable[EventObservation],
    *,
    mandatory_threshold: float = 0.95,
    minimum_outgoing: int = 25,
) -> list[SuccessorProfile]:
    nodes, edges = build_graph(observations)
    grouped: dict[int, list[GraphEdge]] = defaultdict(list)
    for edge in edges:
        grouped[edge.source].append(edge)

    result = []
    for node in nodes:
        rows = sorted(grouped[node.class_id], key=lambda e: (-e.count, e.target))
        mandatory = None
        if node.out_weight >= minimum_outgoing and rows:
            if rows[0].probability >= mandatory_threshold:
                mandatory = rows[0].target
        result.append(
            SuccessorProfile(
                class_id=node.class_id,
                total_outgoing=node.out_weight,
                successors=tuple((e.target, e.count, e.probability) for e in rows),
                mandatory_successor=mandatory,
            )
        )
    return result


def root_nodes(
    observations: Iterable[EventObservation],
    *,
    limit: int = 25,
) -> list[GraphNode]:
    nodes, _ = build_graph(observations)
    return sorted(nodes, key=lambda n: (-n.root_count, -n.occurrences, n.class_id))[:limit]


def leaf_nodes(
    observations: Iterable[EventObservation],
    *,
    limit: int = 25,
) -> list[GraphNode]:
    nodes, _ = build_graph(observations)
    return sorted(nodes, key=lambda n: (-n.leaf_count, -n.occurrences, n.class_id))[:limit]


def hub_nodes(
    observations: Iterable[EventObservation],
    *,
    limit: int = 25,
) -> list[GraphNode]:
    nodes, _ = build_graph(observations)
    return sorted(nodes, key=lambda n: (-n.hub_score, -n.occurrences, n.class_id))[:limit]


def person_graph(
    observations: Iterable[EventObservation],
    person_id: int,
) -> PersonGraph | None:
    for pid, sequence in class_sequences(observations):
        if pid == person_id:
            edges = tuple(zip(sequence, sequence[1:]))
            return PersonGraph(
                person_id=pid,
                sequence=tuple(sequence),
                nodes=tuple(dict.fromkeys(sequence)),
                edges=edges,
            )
    return None


def discover_graph_motifs(
    observations: Iterable[EventObservation],
    *,
    minimum_count: int = 25,
) -> list[GraphMotif]:
    grouped: dict[tuple[str, tuple[int, ...]], list[int]] = defaultdict(list)

    for person_id, sequence in class_sequences(observations):
        # Directed 3-node paths.
        for i in range(len(sequence) - 2):
            motif = tuple(sequence[i:i+3])
            grouped[("path3", motif)].append(person_id)

        # Return/ABA structures.
        for i in range(len(sequence) - 2):
            a, b, c = sequence[i:i+3]
            if a == c and a != b:
                grouped[("return", (a, b, c))].append(person_id)

        # Fan-out within a local four-class window: A->B and A->C.
        for i in range(len(sequence) - 3):
            a, b, c, d = sequence[i:i+4]
            if a == c and b != d:
                grouped[("alternating", (a, b, c, d))].append(person_id)

    motifs = [
        GraphMotif(
            motif_type=kind,
            classes=classes,
            count=len(person_ids),
            sample_person_ids=tuple(person_ids[:5]),
        )
        for (kind, classes), person_ids in grouped.items()
        if len(person_ids) >= minimum_count
    ]
    return sorted(
        motifs,
        key=lambda m: (-m.count, m.motif_type, m.classes),
    )


def graph_summary(
    observations: Iterable[EventObservation],
) -> GraphSummary:
    values = list(observations)
    nodes, edges = build_graph(values)
    profiles = successor_profiles(values)
    motifs = discover_graph_motifs(values)

    nonzero_roots = sum(1 for n in nodes if n.root_count)
    nonzero_leaves = sum(1 for n in nodes if n.leaf_count)
    hubs = sum(1 for n in nodes if n.hub_score >= 0.20)
    mandatory = sum(1 for p in profiles if p.mandatory_successor is not None)

    return GraphSummary(
        observations=len(values),
        nodes=len(nodes),
        edges=len(edges),
        roots=nonzero_roots,
        leaves=nonzero_leaves,
        hubs=hubs,
        mandatory_successors=mandatory,
        motifs=len(motifs),
    )


def graphviz_dot(
    observations: Iterable[EventObservation],
    *,
    max_nodes: int = 40,
    min_edge_count: int = 25,
) -> str:
    nodes, edges = build_graph(observations)
    chosen = {
        node.class_id
        for node in sorted(nodes, key=lambda n: (-n.occurrences, n.class_id))[:max_nodes]
    }

    lines = [
        "digraph ReunionGrammar {",
        '  rankdir="LR";',
        '  node [shape=box];',
    ]
    for node in nodes:
        if node.class_id not in chosen:
            continue
        label = f"C{node.class_id}\\n{node.class_key}\\n{node.occurrences}"
        lines.append(f'  C{node.class_id} [label="{label}"];')

    for edge in edges:
        if edge.count < min_edge_count:
            continue
        if edge.source not in chosen or edge.target not in chosen:
            continue
        lines.append(
            f'  C{edge.source} -> C{edge.target} '
            f'[label="{edge.count} / {edge.probability:.0%}"];'
        )
    lines.append("}")
    return "\n".join(lines) + "\n"
