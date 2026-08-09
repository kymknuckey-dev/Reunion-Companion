"""Build 18 Semantic Confidence Engine.

Consumes persistent Build 16 and Build 17 pipeline artifacts. It does not rerun
the probe corpus.

Confidence is assigned to individual canonical-region candidates using:
- Build 16 region confidence and specificity;
- Build 17 semantic component confidence;
- decoded-event support;
- Object Class support;
- alignment support;
- exclusivity to one semantic probe/component;
- contradiction when a Region ID maps to multiple semantic labels.

No score promotes a region to CANONICAL. Independent repeated same-field probes
remain required for that status.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from .pipeline_artifacts import (
    PipelineArtifact,
    hash_file,
    make_artifact,
    read_artifact,
    write_artifact,
)


@dataclass(frozen=True, slots=True)
class RegionConfidence:
    region_id: str
    probe_id: str
    semantic_label: str
    operation: str
    score: float
    grade: str
    base_region_confidence: float
    component_confidence: float
    specificity: float
    exclusivity: float
    contradiction_penalty: float
    decoded_support: bool
    object_class_support: bool
    alignment_support: bool
    occurrence_count: int
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfidenceSnapshot:
    regions: tuple[RegionConfidence, ...]
    semantic_regions: int
    high_confidence_regions: int
    verified_candidate_regions: int
    contradictory_regions: int
    exclusive_regions: int
    labels: int


def _unwrap(path: str | Path) -> tuple[dict[str, Any], str]:
    """Accept either a pipeline artifact or a raw stage payload JSON."""
    p = Path(path)
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("schema") == "reunion-companion.discovery-artifact.v1":
        artifact = read_artifact(p)
        return artifact.payload, artifact.payload_hash
    return doc, hash_file(p)


def load_pipeline(pipeline_dir: str | Path):
    base = Path(pipeline_dir).expanduser()
    stage16 = base / "stage-16-canonical-regions.json"
    stage17 = base / "stage-17-architecture.json"
    if not stage16.is_file():
        raise FileNotFoundError(f"Missing Stage 16 artifact: {stage16}")
    if not stage17.is_file():
        raise FileNotFoundError(f"Missing Stage 17 artifact: {stage17}")
    r16, h16 = _unwrap(stage16)
    r17, h17 = _unwrap(stage17)
    return r16, r17, stage16, stage17, h16, h17


def _grade(score: float, direct: bool) -> str:
    if score >= 0.95 and direct:
        return "VERIFIED_CANDIDATE"
    if score >= 0.90:
        return "HIGH_CONFIDENCE"
    if score >= 0.80:
        return "SUPPORTED"
    if score >= 0.65:
        return "TENTATIVE"
    return "LOW"


def build_confidence_snapshot(
    stage16_payload: dict[str, Any],
    stage17_payload: dict[str, Any],
) -> ConfidenceSnapshot:
    primary_by_probe = {
        c["probe_id"]: c
        for c in stage17_payload.get("components", [])
        if c.get("role") == "PRIMARY_CANDIDATE" and c.get("probe_id")
    }

    # A Region ID appearing under multiple semantic labels is a contradiction
    # signal. Duplicate occurrences within one label are counted but are not
    # treated as independent verification.
    labels_by_region: dict[str, set[str]] = defaultdict(set)
    occurrences = Counter()
    for region in stage16_payload.get("regions", []):
        rid = region["region_id"]
        labels_by_region[rid].add(region.get("semantic_label") or "")
        occurrences[rid] += 1

    scored: list[RegionConfidence] = []
    for region in stage16_payload.get("regions", []):
        probe_id = region.get("probe_id") or ""
        label = region.get("semantic_label") or ""
        component = primary_by_probe.get(probe_id, {})

        base = float(region.get("confidence", 0.0))
        component_conf = float(component.get("confidence", 0.0))
        specificity = float(region.get("specificity", 0.0))

        label_count = len({x for x in labels_by_region[region["region_id"]] if x})
        exclusive = 1.0 if label_count <= 1 else 0.0
        contradiction = 0.0 if label_count <= 1 else min(0.40, 0.18 * (label_count - 1))

        decoded = bool(region.get("decoded_event_support"))
        obj = bool(region.get("object_class_support"))
        alignment = bool(region.get("alignment_support"))
        direct = decoded or obj or alignment

        # Weighted evidence model. Build 16 remains the strongest signal;
        # Build 17 architecture confidence acts as a consistency prior.
        score = (
            0.46 * base
            + 0.22 * component_conf
            + 0.17 * specificity
            + 0.07 * exclusive
            + (0.05 if decoded else 0.0)
            + (0.04 if obj else 0.0)
            + (0.04 if alignment else 0.0)
            - contradiction
        )
        score = max(0.0, min(0.99, score))

        evidence = [
            f"Build16 region confidence={base:.3f}",
            f"Build17 component confidence={component_conf:.3f}",
            f"specificity={specificity:.3f}",
            f"semantic-label-count={label_count}",
        ]
        if decoded:
            evidence.append("decoded event support")
        if obj:
            evidence.append("Object Class support")
        if alignment:
            evidence.append("alignment support")
        if occurrences[region["region_id"]] > 1:
            evidence.append(
                f"region-id repeats {occurrences[region['region_id']]} times "
                "within the evidence corpus; not treated as independent verification"
            )
        if contradiction:
            evidence.append(
                f"contradiction penalty={contradiction:.3f}: Region ID occurs under multiple labels"
            )

        scored.append(
            RegionConfidence(
                region_id=region["region_id"],
                probe_id=probe_id,
                semantic_label=label,
                operation=region.get("operation") or "",
                score=score,
                grade=_grade(score, direct),
                base_region_confidence=base,
                component_confidence=component_conf,
                specificity=specificity,
                exclusivity=exclusive,
                contradiction_penalty=contradiction,
                decoded_support=decoded,
                object_class_support=obj,
                alignment_support=alignment,
                occurrence_count=occurrences[region["region_id"]],
                evidence=tuple(evidence),
            )
        )

    regions = tuple(
        sorted(
            scored,
            key=lambda r: (-r.score, r.semantic_label, r.region_id),
        )
    )
    return ConfidenceSnapshot(
        regions=regions,
        semantic_regions=len(regions),
        high_confidence_regions=sum(r.score >= 0.90 for r in regions),
        verified_candidate_regions=sum(r.grade == "VERIFIED_CANDIDATE" for r in regions),
        contradictory_regions=sum(r.contradiction_penalty > 0 for r in regions),
        exclusive_regions=sum(r.exclusivity == 1.0 for r in regions),
        labels=len({r.semantic_label for r in regions if r.semantic_label}),
    )


def confidence_document(snapshot: ConfidenceSnapshot) -> dict[str, Any]:
    return {
        "schema": "reunion-companion.semantic-confidence.v1",
        "phase": "Phase 3 - Database Architecture Reconstruction",
        "build": 18,
        "canonical_promotion_allowed": False,
        "canonical_requirement": "replicated independent same-semantic probes",
        "summary": {
            "semantic_regions": snapshot.semantic_regions,
            "high_confidence_regions": snapshot.high_confidence_regions,
            "verified_candidate_regions": snapshot.verified_candidate_regions,
            "contradictory_regions": snapshot.contradictory_regions,
            "exclusive_regions": snapshot.exclusive_regions,
            "semantic_labels": snapshot.labels,
        },
        "regions": [
            {
                "region_id": r.region_id,
                "probe_id": r.probe_id,
                "semantic_label": r.semantic_label,
                "operation": r.operation,
                "score": r.score,
                "grade": r.grade,
                "base_region_confidence": r.base_region_confidence,
                "component_confidence": r.component_confidence,
                "specificity": r.specificity,
                "exclusivity": r.exclusivity,
                "contradiction_penalty": r.contradiction_penalty,
                "decoded_support": r.decoded_support,
                "object_class_support": r.object_class_support,
                "alignment_support": r.alignment_support,
                "occurrence_count": r.occurrence_count,
                "evidence": list(r.evidence),
            }
            for r in snapshot.regions
        ],
    }


def build_confidence_from_pipeline(pipeline_dir: str | Path):
    r16, r17, p16, p17, h16, h17 = load_pipeline(pipeline_dir)
    snapshot = build_confidence_snapshot(r16, r17)
    return snapshot, p16, p17, h16, h17


def write_stage18_artifact(pipeline_dir: str | Path):
    snapshot, p16, p17, h16, h17 = build_confidence_from_pipeline(pipeline_dir)
    payload = confidence_document(snapshot)
    artifact = make_artifact(
        18,
        "semantic-confidence",
        payload,
        {
            "stage16_canonical_regions": hash_file(p16),
            "stage17_architecture": hash_file(p17),
        },
    )
    target = Path(pipeline_dir) / "stage-18-semantic-confidence.json"
    return write_artifact(target, artifact), snapshot
