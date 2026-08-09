"""Phase 2 Build 13 Semantic Probe Verification Engine.

The engine compares controlled before/after Reunion packages using the
deterministic structural vocabulary established by Builds 11 and 12.

A probe's declared semantic label records what the human deliberately changed
in Reunion. It is evidence metadata, not an automatic interpretation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import json

from .event_scanner import EventScanner
from .object_classification import classify_objects, object_classes
from .semantic_alignment import alignment_edges, object_graph


STATUS_ORDER = {
    "UNKNOWN": 0,
    "HYPOTHESIS": 1,
    "LIKELY": 2,
    "PROBABLE": 3,
    "VERIFIED": 4,
    "CANONICAL": 5,
}


@dataclass(frozen=True, slots=True)
class ProbeSnapshot:
    package_path: str
    package_hash: str
    observations: int
    structural_objects: int
    object_classes: int
    class_counts: tuple[tuple[str, int], ...]
    edge_counts: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True, slots=True)
class ClassDelta:
    class_id: str
    before_count: int
    after_count: int
    delta: int


@dataclass(frozen=True, slots=True)
class EdgeDelta:
    source_class_id: str
    target_class_id: str
    before_count: int
    after_count: int
    delta: int


@dataclass(frozen=True, slots=True)
class ProbeResult:
    probe_id: str
    semantic_label: str
    before_path: str
    after_path: str
    before_hash: str
    after_hash: str
    observation_delta: int
    object_delta: int
    class_deltas: tuple[ClassDelta, ...]
    edge_deltas: tuple[EdgeDelta, ...]
    unchanged: bool


@dataclass(frozen=True, slots=True)
class ProbePriority:
    rank: int
    class_id: str
    occurrences: int
    people: int
    centrality: float
    in_degree: int
    out_degree: int
    score: float


@dataclass(frozen=True, slots=True)
class SemanticEvidence:
    semantic_label: str
    class_id: str
    direction: str
    supporting_probes: tuple[str, ...]
    contradicting_probes: tuple[str, ...]
    support: int
    contradictions: int
    consistency: float
    confidence: float
    status: str


def _main_data_path(package_path: str | Path) -> Path:
    package = Path(package_path).expanduser()
    candidate = package / "familyfile.familydata"
    if candidate.is_file():
        return candidate
    return package


def package_hash(package_path: str | Path) -> str:
    path = _main_data_path(package_path)
    digest = sha256()
    if path.is_file():
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    # Stable fallback for directory-shaped fixtures.
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(str(item.relative_to(path)).encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def snapshot_package(package_path: str | Path) -> ProbeSnapshot:
    path = Path(package_path).expanduser()
    scan = EventScanner().scan(path)
    observations = list(scan.observations)
    objects = classify_objects(observations)
    classes = object_classes(observations)
    edges = alignment_edges(observations)

    return ProbeSnapshot(
        package_path=str(path),
        package_hash=package_hash(path),
        observations=len(observations),
        structural_objects=len(objects),
        object_classes=len(classes),
        class_counts=tuple(
            sorted(
                ((item.class_id, item.occurrences) for item in classes),
                key=lambda row: row[0],
            )
        ),
        edge_counts=tuple(
            sorted(
                (
                    (edge.source_class_id, edge.target_class_id, edge.count)
                    for edge in edges
                ),
                key=lambda row: (row[0], row[1]),
            )
        ),
    )


def compare_snapshots(
    before: ProbeSnapshot,
    after: ProbeSnapshot,
    *,
    probe_id: str,
    semantic_label: str,
) -> ProbeResult:
    before_classes = dict(before.class_counts)
    after_classes = dict(after.class_counts)
    class_ids = sorted(set(before_classes) | set(after_classes))

    class_deltas = [
        ClassDelta(
            class_id=class_id,
            before_count=before_classes.get(class_id, 0),
            after_count=after_classes.get(class_id, 0),
            delta=after_classes.get(class_id, 0) - before_classes.get(class_id, 0),
        )
        for class_id in class_ids
        if before_classes.get(class_id, 0) != after_classes.get(class_id, 0)
    ]

    before_edges = {(s, t): count for s, t, count in before.edge_counts}
    after_edges = {(s, t): count for s, t, count in after.edge_counts}
    edge_keys = sorted(set(before_edges) | set(after_edges))

    edge_deltas = [
        EdgeDelta(
            source_class_id=source,
            target_class_id=target,
            before_count=before_edges.get((source, target), 0),
            after_count=after_edges.get((source, target), 0),
            delta=after_edges.get((source, target), 0)
            - before_edges.get((source, target), 0),
        )
        for source, target in edge_keys
        if before_edges.get((source, target), 0)
        != after_edges.get((source, target), 0)
    ]

    return ProbeResult(
        probe_id=probe_id,
        semantic_label=semantic_label,
        before_path=before.package_path,
        after_path=after.package_path,
        before_hash=before.package_hash,
        after_hash=after.package_hash,
        observation_delta=after.observations - before.observations,
        object_delta=after.structural_objects - before.structural_objects,
        class_deltas=tuple(
            sorted(class_deltas, key=lambda item: (-abs(item.delta), item.class_id))
        ),
        edge_deltas=tuple(
            sorted(
                edge_deltas,
                key=lambda item: (
                    -abs(item.delta),
                    item.source_class_id,
                    item.target_class_id,
                ),
            )
        ),
        unchanged=(
            before.package_hash == after.package_hash
            and not class_deltas
            and not edge_deltas
        ),
    )


def compare_packages(
    before_path: str | Path,
    after_path: str | Path,
    *,
    probe_id: str,
    semantic_label: str,
) -> ProbeResult:
    before = snapshot_package(before_path)
    after = snapshot_package(after_path)
    return compare_snapshots(
        before,
        after,
        probe_id=probe_id,
        semantic_label=semantic_label,
    )


def rank_probe_targets(
    observations: Iterable,
    *,
    limit: int = 25,
) -> list[ProbePriority]:
    values = list(observations)
    nodes, _ = object_graph(values)
    priorities = []
    for node in nodes:
        # High centrality and population matter most; degree rewards classes
        # capable of explaining many neighbouring structures.
        score = (
            0.55 * node.centrality
            + 0.25 * min(1.0, node.occurrences / 2500)
            + 0.10 * min(1.0, node.people / 2500)
            + 0.10 * min(1.0, (node.in_degree + node.out_degree) / 200)
        )
        priorities.append(
            ProbePriority(
                rank=0,
                class_id=node.class_id,
                occurrences=node.occurrences,
                people=node.people,
                centrality=node.centrality,
                in_degree=node.in_degree,
                out_degree=node.out_degree,
                score=score,
            )
        )

    priorities.sort(key=lambda item: (-item.score, item.class_id))
    return [
        ProbePriority(
            rank=index,
            class_id=item.class_id,
            occurrences=item.occurrences,
            people=item.people,
            centrality=item.centrality,
            in_degree=item.in_degree,
            out_degree=item.out_degree,
            score=item.score,
        )
        for index, item in enumerate(priorities[:limit], start=1)
    ]


def _evidence_status(
    support: int,
    contradictions: int,
    confidence: float,
) -> str:
    if support == 0:
        return "UNKNOWN"
    if support == 1:
        return "HYPOTHESIS"
    if support >= 3 and contradictions == 0 and confidence >= 0.95:
        return "VERIFIED"
    if support >= 3 and confidence >= 0.80:
        return "PROBABLE"
    if support >= 2 and confidence >= 0.65:
        return "LIKELY"
    return "HYPOTHESIS"


def aggregate_evidence(results: Iterable[ProbeResult]) -> list[SemanticEvidence]:
    values = list(results)
    by_label: dict[str, list[ProbeResult]] = defaultdict(list)
    for result in values:
        by_label[result.semantic_label].append(result)

    evidence: list[SemanticEvidence] = []

    for semantic_label, probes in sorted(by_label.items()):
        all_classes = sorted(
            {
                delta.class_id
                for probe in probes
                for delta in probe.class_deltas
            }
        )

        for class_id in all_classes:
            directions = []
            supporting = []
            contradicting = []

            for probe in probes:
                delta = next(
                    (
                        item.delta
                        for item in probe.class_deltas
                        if item.class_id == class_id
                    ),
                    0,
                )
                if delta > 0:
                    directions.append("added")
                elif delta < 0:
                    directions.append("removed")
                else:
                    directions.append("unchanged")

            changed = [direction for direction in directions if direction != "unchanged"]
            if not changed:
                continue

            primary = Counter(changed).most_common(1)[0][0]
            for probe, direction in zip(probes, directions):
                if direction == primary:
                    supporting.append(probe.probe_id)
                else:
                    contradicting.append(probe.probe_id)

            support = len(supporting)
            contradictions = len(contradicting)
            total = len(probes)
            consistency = support / total if total else 0.0
            replication = min(1.0, support / 3.0)
            confidence = min(
                1.0,
                0.65 * consistency + 0.35 * replication,
            )
            status = _evidence_status(support, contradictions, confidence)

            evidence.append(
                SemanticEvidence(
                    semantic_label=semantic_label,
                    class_id=class_id,
                    direction=primary,
                    supporting_probes=tuple(supporting),
                    contradicting_probes=tuple(contradicting),
                    support=support,
                    contradictions=contradictions,
                    consistency=consistency,
                    confidence=confidence,
                    status=status,
                )
            )

    return sorted(
        evidence,
        key=lambda item: (
            item.semantic_label.casefold(),
            -STATUS_ORDER[item.status],
            -item.confidence,
            item.class_id,
        ),
    )


def load_probe_manifest(path: str | Path) -> dict:
    document = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("probes"), list):
        raise ValueError("Probe manifest must contain a 'probes' list.")
    return document


def run_probe_manifest(path: str | Path) -> tuple[list[ProbeResult], list[SemanticEvidence]]:
    manifest = load_probe_manifest(path)
    results = []
    for index, item in enumerate(manifest["probes"], start=1):
        probe_id = str(item.get("id") or f"probe-{index:03d}")
        semantic_label = str(item.get("semantic_label") or "").strip()
        before = item.get("before")
        after = item.get("after")
        if not semantic_label or not before or not after:
            raise ValueError(
                f"Probe {probe_id!r} requires semantic_label, before and after."
            )
        results.append(
            compare_packages(
                before,
                after,
                probe_id=probe_id,
                semantic_label=semantic_label,
            )
        )
    return results, aggregate_evidence(results)


def evidence_document(
    results: Iterable[ProbeResult],
    evidence: Iterable[SemanticEvidence],
    *,
    manifest_path: str | None = None,
) -> dict:
    return {
        "schema": "reunion-companion.semantic-probes.v1",
        "phase": "Phase 2 - Semantic Discovery",
        "build": 13,
        "manifest_path": manifest_path,
        "semantic_labels_are_declared_probe_inputs": True,
        "automatic_canonical_promotion": False,
        "results": [
            {
                "probe_id": result.probe_id,
                "semantic_label": result.semantic_label,
                "before_path": result.before_path,
                "after_path": result.after_path,
                "before_hash": result.before_hash,
                "after_hash": result.after_hash,
                "observation_delta": result.observation_delta,
                "object_delta": result.object_delta,
                "unchanged": result.unchanged,
                "class_deltas": [
                    {
                        "class_id": item.class_id,
                        "before_count": item.before_count,
                        "after_count": item.after_count,
                        "delta": item.delta,
                    }
                    for item in result.class_deltas
                ],
                "edge_deltas": [
                    {
                        "source": item.source_class_id,
                        "target": item.target_class_id,
                        "before_count": item.before_count,
                        "after_count": item.after_count,
                        "delta": item.delta,
                    }
                    for item in result.edge_deltas
                ],
            }
            for result in results
        ],
        "evidence": [
            {
                "semantic_label": item.semantic_label,
                "class_id": item.class_id,
                "direction": item.direction,
                "supporting_probes": list(item.supporting_probes),
                "contradicting_probes": list(item.contradicting_probes),
                "support": item.support,
                "contradictions": item.contradictions,
                "consistency": item.consistency,
                "confidence": item.confidence,
                "status": item.status,
            }
            for item in evidence
        ],
    }
