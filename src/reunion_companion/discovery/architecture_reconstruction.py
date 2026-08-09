from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from .canonical_regions import extract_region_corpus, region_document
from .pipeline_artifacts import make_artifact, write_artifact, hash_file

@dataclass(frozen=True, slots=True)
class ArchitectureComponent:
    component_id: str
    role: str
    label: str
    probe_id: str | None
    region_ids: tuple
    confidence: float
    evidence: tuple

@dataclass(frozen=True, slots=True)
class ArchitectureLink:
    source: str
    target: str
    relation: str
    confidence: float

@dataclass(frozen=True, slots=True)
class ArchitectureSnapshot:
    components: tuple
    links: tuple
    primary_candidates: int
    structural_candidates: int
    derived_save_state: int
    unresolved: int
    region_candidates: int
    strong_regions: int

def _cid(role, label, probe_id):
    return "AC-" + sha1(f"{role}|{label}|{probe_id or ''}".encode()).hexdigest()[:10].upper()

def reconstruct_architecture(manifest_path):
    corpus = extract_region_corpus(manifest_path)
    components, links = [], []
    by_probe = defaultdict(list)
    for region in corpus.regions:
        by_probe[region.probe_id].append(region)

    for result in corpus.results:
        probe = result.spec
        regions = by_probe.get(probe.probe_id, [])
        if not regions:
            continue
        decoded = any(r.decoded_event_support for r in regions)
        structural = any(r.object_class_support or r.alignment_support for r in regions)
        mean_conf = sum(r.confidence for r in regions) / len(regions)
        evidence = ["controlled semantic probe", f"operation={probe.operation}"]
        if decoded:
            evidence.append("decoded event delta")
        if structural:
            evidence.append("object/graph structural delta")

        primary_id = _cid("PRIMARY_CANDIDATE", probe.semantic_label, probe.probe_id)
        components.append(ArchitectureComponent(
            primary_id, "PRIMARY_CANDIDATE", probe.semantic_label, probe.probe_id,
            tuple(r.region_id for r in regions),
            min(.99, mean_conf + (.05 if decoded else 0)),
            tuple(evidence),
        ))

        structural_regions = [r for r in regions if r.object_class_support or r.alignment_support]
        if structural_regions:
            sid = _cid("STRUCTURAL_CANDIDATE", probe.semantic_label, probe.probe_id)
            conf = max(r.confidence for r in structural_regions)
            components.append(ArchitectureComponent(
                sid, "STRUCTURAL_CANDIDATE", probe.semantic_label + " structure",
                probe.probe_id, tuple(r.region_id for r in structural_regions),
                conf, ("Object Class/alignment evidence",),
            ))
            links.append(ArchitectureLink(
                primary_id, sid, "HAS_STRUCTURAL_REPRESENTATION", conf
            ))

    noise = defaultdict(list)
    for span in corpus.spans:
        if span.region_category in {"KNOWN_SAVE_NOISE", "RECURRENT_SAVE_NOISE"}:
            label = span.original_category if span.region_category == "KNOWN_SAVE_NOISE" else "RECURRENT_UNKNOWN_SAVE_PATTERN"
            noise[label].append(span.confidence)
    for label, values in sorted(noise.items()):
        components.append(ArchitectureComponent(
            _cid("DERIVED_SAVE_STATE", label, None),
            "DERIVED_SAVE_STATE", label, None, (),
            sum(values) / len(values),
            (f"{len(values)} recurrent/suppressed span(s)",),
        ))

    if corpus.residual_unknown:
        components.append(ArchitectureComponent(
            _cid("UNRESOLVED", "Unresolved differential regions", None),
            "UNRESOLVED", "Unresolved differential regions", None, (), 0.0,
            (f"{corpus.residual_unknown} residual UNKNOWN span(s)",),
        ))

    primary = {c.probe_id: c.component_id for c in components if c.role == "PRIMARY_CANDIDATE"}
    for overlap in corpus.overlaps:
        if overlap.left_probe in primary and overlap.right_probe in primary:
            links.append(ArchitectureLink(
                primary[overlap.left_probe], primary[overlap.right_probe],
                "SHARES_REGION_SIGNATURE", overlap.jaccard
            ))

    roles = [c.role for c in components]
    snapshot = ArchitectureSnapshot(
        tuple(sorted(components, key=lambda c: (c.role, c.label, c.component_id))),
        tuple(sorted(links, key=lambda l: (l.relation, l.source, l.target))),
        roles.count("PRIMARY_CANDIDATE"),
        roles.count("STRUCTURAL_CANDIDATE"),
        roles.count("DERIVED_SAVE_STATE"),
        roles.count("UNRESOLVED"),
        len(corpus.regions),
        sum(r.status == "STRONG_CANDIDATE" for r in corpus.regions),
    )
    return snapshot, corpus

def architecture_document(snapshot, corpus):
    return {
        "schema": "reunion-companion.architecture-snapshot.v1",
        "phase": "Phase 3 - Database Architecture Reconstruction",
        "build": 17,
        "evidence_boundary": {
            "implementation_claims_proven": False,
            "write_safety_proven": False,
            "primary_authority_proven": False,
            "roles_are_evidence_based_candidates": True,
        },
        "summary": {
            "components": len(snapshot.components),
            "links": len(snapshot.links),
            "primary_candidates": snapshot.primary_candidates,
            "structural_candidates": snapshot.structural_candidates,
            "derived_save_state": snapshot.derived_save_state,
            "unresolved_components": snapshot.unresolved,
            "region_candidates": snapshot.region_candidates,
            "strong_regions": snapshot.strong_regions,
            "residual_unknown_spans": corpus.residual_unknown,
        },
        "components": [
            {
                "component_id": c.component_id,
                "role": c.role,
                "label": c.label,
                "probe_id": c.probe_id,
                "region_ids": list(c.region_ids),
                "confidence": c.confidence,
                "evidence": list(c.evidence),
            } for c in snapshot.components
        ],
        "links": [
            {
                "source": l.source, "target": l.target,
                "relation": l.relation, "confidence": l.confidence,
            } for l in snapshot.links
        ],
    }

def build_pipeline_artifacts(manifest_path, output_dir):
    snapshot, corpus = reconstruct_architecture(manifest_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stage16 = write_artifact(
        output_dir / "stage-16-canonical-regions.json",
        make_artifact(
            16, "canonical-regions", region_document(corpus),
            {"probe_manifest": hash_file(manifest_path)},
        ),
    )
    stage17 = write_artifact(
        output_dir / "stage-17-architecture.json",
        make_artifact(
            17, "architecture-reconstruction",
            architecture_document(snapshot, corpus),
            {
                "probe_manifest": hash_file(manifest_path),
                "canonical_regions_artifact": hash_file(stage16),
            },
        ),
    )
    return stage16, stage17
