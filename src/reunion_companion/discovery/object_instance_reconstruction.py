"""Build 21 Object Instance Reconstruction Engine.

Build 20 reconstructed semantic object families. Build 21 attempts to split
those families into individual logical instance candidates.

This engine is deliberately conservative. It only forms an instance when at
least one locality signal exists in Stage 16/18/19 evidence:

- an explicit person_id or record_id shared by regions;
- overlapping/adjacent canonical byte spans in the same probe context;
- a strong Build 19 relation between members of the same reconstructed object;
- a single-region object family (e.g. current Occupation evidence).

If locality evidence is absent, regions remain UNRESOLVED rather than being
forced into an artificial instance.

No Build 21 instance is CANONICAL, writable, or claimed to correspond exactly
to Reunion's private internal object implementation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any
import json

from .pipeline_artifacts import hash_file, make_artifact, read_artifact, write_artifact


@dataclass(frozen=True, slots=True)
class RegionEvidence:
    region_id: str
    object_id: str
    object_type: str
    semantic_label: str
    role: str
    score: float
    person_id: str | None
    record_id: str | None
    probe_id: str | None
    before_start: int | None
    before_end: int | None
    after_start: int | None
    after_end: int | None


@dataclass(frozen=True, slots=True)
class InstanceCandidate:
    instance_id: str
    object_id: str
    object_type: str
    confidence: float
    status: str
    region_ids: tuple[str, ...]
    roles: tuple[str, ...]
    person_id: str | None
    record_id: str | None
    probe_ids: tuple[str, ...]
    evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InstanceSnapshot:
    instances: tuple[InstanceCandidate, ...]
    unresolved_regions: tuple[str, ...]
    resolved_regions: int
    unresolved_region_count: int
    object_families: int
    families_with_instances: int
    singleton_instances: int
    multi_region_instances: int


def _unwrap(path: Path) -> dict[str, Any]:
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("schema") == "reunion-companion.discovery-artifact.v1":
        return read_artifact(path).payload
    return d


def load_pipeline(directory: str | Path):
    base = Path(directory).expanduser()
    paths = [
        base / "stage-16-canonical-regions.json",
        base / "stage-17-architecture.json",
        base / "stage-18-semantic-confidence.json",
        base / "stage-19-region-dependency-graph.json",
        base / "stage-20-object-reconstruction.json",
    ]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing pipeline artifact(s): " + ", ".join(missing))
    payloads = [_unwrap(p) for p in paths]
    return (*payloads, *paths)


def _instance_id(object_id: str, region_ids: list[str], person_id=None, record_id=None) -> str:
    raw = "|".join([object_id, person_id or "", record_id or "", *sorted(region_ids)])
    return "OI-" + sha1(raw.encode("utf-8")).hexdigest()[:10].upper()


def _first(d: dict[str, Any], *keys):
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


def _as_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _stage16_rows(stage16: dict) -> list[dict]:
    # Support both known/likely Build 16 payload shapes.
    if isinstance(stage16.get("regions"), list):
        return stage16["regions"]
    if isinstance(stage16.get("canonical_regions"), list):
        return stage16["canonical_regions"]
    payload = stage16.get("payload")
    if isinstance(payload, dict):
        if isinstance(payload.get("regions"), list):
            return payload["regions"]
        if isinstance(payload.get("canonical_regions"), list):
            return payload["canonical_regions"]
    return []


def _object_members(stage20: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    object_by_region = {}
    object_by_id = {}
    for obj in stage20.get("objects", []):
        object_by_id[obj["object_id"]] = obj
        for m in obj.get("members", []):
            object_by_region[m["region_id"]] = {
                "object_id": obj["object_id"],
                "object_type": obj["object_type"],
                "semantic_label": m.get("semantic_label", ""),
                "role": m.get("role", "UNKNOWN"),
                "score": float(m.get("membership_confidence", m.get("score", 0.0))),
            }
    return object_by_region, object_by_id


def collect_region_evidence(stage16: dict, stage20: dict) -> list[RegionEvidence]:
    object_by_region, _ = _object_members(stage20)
    s16_by_region = defaultdict(list)
    for r in _stage16_rows(stage16):
        rid = r.get("region_id")
        if rid:
            s16_by_region[rid].append(r)

    evidence = []
    for rid, member in object_by_region.items():
        rows = s16_by_region.get(rid) or [{}]
        # A region can appear multiple times in Stage 16. Keep each occurrence
        # because differing person/record/probe coordinates can identify instances.
        for row in rows:
            evidence.append(
                RegionEvidence(
                    region_id=rid,
                    object_id=member["object_id"],
                    object_type=member["object_type"],
                    semantic_label=member["semantic_label"],
                    role=member["role"],
                    score=member["score"],
                    person_id=str(_first(row, "person_id", "person", "owner_person_id"))
                        if _first(row, "person_id", "person", "owner_person_id") is not None else None,
                    record_id=str(_first(row, "record_id", "record", "person_record_id"))
                        if _first(row, "record_id", "record", "person_record_id") is not None else None,
                    probe_id=_first(row, "probe_id", "probe", "semantic_probe"),
                    before_start=_as_int(_first(row, "before_start", "before_offset", "left_start")),
                    before_end=_as_int(_first(row, "before_end", "before_stop", "left_end")),
                    after_start=_as_int(_first(row, "after_start", "after_offset", "right_start")),
                    after_end=_as_int(_first(row, "after_end", "after_stop", "right_end")),
                )
            )
    return evidence


def _span_distance(a: RegionEvidence, b: RegionEvidence) -> int | None:
    candidates = []
    for a0, a1, b0, b1 in (
        (a.before_start, a.before_end, b.before_start, b.before_end),
        (a.after_start, a.after_end, b.after_start, b.after_end),
    ):
        if None in (a0, a1, b0, b1):
            continue
        if a1 >= b0 and b1 >= a0:
            candidates.append(0)
        elif a1 < b0:
            candidates.append(b0 - a1)
        else:
            candidates.append(a0 - b1)
    return min(candidates) if candidates else None


def _strong_same_object_edges(stage19: dict, object_region_ids: set[str]) -> set[tuple[str, str]]:
    links = set()
    for e in stage19.get("edges", []):
        a, b = e.get("source"), e.get("target")
        if a not in object_region_ids or b not in object_region_ids:
            continue
        if float(e.get("confidence", 0.0)) < 0.80:
            continue
        if e.get("relation") not in {"SAME_SEMANTIC_COMPONENT", "SHARED_STRUCTURAL_SUPPORT"}:
            continue
        links.add(tuple(sorted((a, b))))
    return links


class _DSU:
    def __init__(self, items):
        self.p = {x: x for x in items}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def reconstruct_instances(stage16: dict, stage17: dict, stage18: dict, stage19: dict, stage20: dict,
                          locality_gap: int = 96) -> InstanceSnapshot:
    evidence = collect_region_evidence(stage16, stage20)
    by_object = defaultdict(list)
    for ev in evidence:
        by_object[ev.object_id].append(ev)

    instances = []
    unresolved = set()
    resolved_regions = set()

    for object_id, evs in by_object.items():
        # Collapse repeated evidence occurrences to region-level representatives
        # while retaining the best available coordinates/IDs.
        by_region = defaultdict(list)
        for ev in evs:
            by_region[ev.region_id].append(ev)
        region_ids = sorted(by_region)
        object_type = evs[0].object_type

        # Singleton family is a legitimate singleton instance candidate.
        if len(region_ids) == 1:
            ev = by_region[region_ids[0]][0]
            instances.append(
                InstanceCandidate(
                    instance_id=_instance_id(object_id, region_ids, ev.person_id, ev.record_id),
                    object_id=object_id,
                    object_type=object_type,
                    confidence=min(0.95, ev.score),
                    status="SINGLETON_INSTANCE_CANDIDATE",
                    region_ids=tuple(region_ids),
                    roles=(ev.role,),
                    person_id=ev.person_id,
                    record_id=ev.record_id,
                    probe_ids=tuple(sorted({x.probe_id for x in by_region[ev.region_id] if x.probe_id})),
                    evidence=("single-region object family",),
                )
            )
            resolved_regions.add(ev.region_id)
            continue

        dsu = _DSU(region_ids)
        merge_evidence = defaultdict(list)
        strong_edges = _strong_same_object_edges(stage19, set(region_ids))

        for i, a_id in enumerate(region_ids):
            for b_id in region_ids[i+1:]:
                best_reason = None
                best_strength = 0.0
                for a in by_region[a_id]:
                    for b in by_region[b_id]:
                        # Explicit person/record identity outranks all other signals.
                        if a.record_id and b.record_id and a.record_id == b.record_id:
                            best_reason = f"shared record_id={a.record_id}"
                            best_strength = max(best_strength, 0.98)
                        elif a.person_id and b.person_id and a.person_id == b.person_id:
                            best_reason = f"shared person_id={a.person_id}"
                            best_strength = max(best_strength, 0.94)

                        # Same probe context + close/overlapping byte spans.
                        dist = _span_distance(a, b)
                        if (
                            a.probe_id and b.probe_id and a.probe_id == b.probe_id
                            and dist is not None and dist <= locality_gap
                        ):
                            strength = 0.90 if dist == 0 else max(0.80, 0.90 - dist / 1000)
                            if strength > best_strength:
                                best_reason = f"same probe={a.probe_id}, span-distance={dist}"
                                best_strength = strength

                # Strong graph relation is supportive, but never sufficient alone
                # unless there is also a locality identity signal.
                edge_support = tuple(sorted((a_id, b_id))) in strong_edges
                if best_reason:
                    if edge_support:
                        best_strength = min(0.99, best_strength + 0.03)
                        best_reason += ", strong Build19 support"
                    dsu.union(a_id, b_id)
                    merge_evidence[(a_id, b_id)].append((best_strength, best_reason))

        components = defaultdict(list)
        for rid in region_ids:
            components[dsu.find(rid)].append(rid)

        for comp in components.values():
            # A multi-region instance is only accepted if at least one actual merge occurred.
            if len(comp) == 1:
                unresolved.add(comp[0])
                continue

            comp_set = set(comp)
            reasons = []
            strengths = []
            person_ids = set()
            record_ids = set()
            probe_ids = set()
            roles = set()
            scores = []

            for rid in comp:
                for ev in by_region[rid]:
                    if ev.person_id: person_ids.add(ev.person_id)
                    if ev.record_id: record_ids.add(ev.record_id)
                    if ev.probe_id: probe_ids.add(ev.probe_id)
                    roles.add(ev.role)
                    scores.append(ev.score)

            for (a, b), vals in merge_evidence.items():
                if a in comp_set and b in comp_set:
                    for strength, reason in vals:
                        strengths.append(strength)
                        reasons.append(reason)

            base = sum(scores) / max(1, len(scores))
            locality = sum(strengths) / max(1, len(strengths))
            confidence = min(0.99, 0.55 * base + 0.45 * locality)

            if confidence >= 0.93:
                status = "VERIFIED_INSTANCE_CANDIDATE"
            elif confidence >= 0.85:
                status = "HIGH_CONFIDENCE_INSTANCE"
            else:
                status = "INSTANCE_CANDIDATE"

            instances.append(
                InstanceCandidate(
                    instance_id=_instance_id(
                        object_id, comp,
                        next(iter(person_ids)) if len(person_ids) == 1 else None,
                        next(iter(record_ids)) if len(record_ids) == 1 else None,
                    ),
                    object_id=object_id,
                    object_type=object_type,
                    confidence=confidence,
                    status=status,
                    region_ids=tuple(sorted(comp)),
                    roles=tuple(sorted(roles)),
                    person_id=next(iter(person_ids)) if len(person_ids) == 1 else None,
                    record_id=next(iter(record_ids)) if len(record_ids) == 1 else None,
                    probe_ids=tuple(sorted(probe_ids)),
                    evidence=tuple(sorted(set(reasons))),
                )
            )
            resolved_regions.update(comp)

        unresolved.update(set(region_ids) - resolved_regions)

    instance_tuple = tuple(sorted(instances, key=lambda x: (-x.confidence, x.object_type, x.instance_id)))
    unresolved_tuple = tuple(sorted(unresolved))
    families = len(by_object)
    families_with_instances = len({i.object_id for i in instance_tuple})
    return InstanceSnapshot(
        instances=instance_tuple,
        unresolved_regions=unresolved_tuple,
        resolved_regions=len(resolved_regions),
        unresolved_region_count=len(unresolved_tuple),
        object_families=families,
        families_with_instances=families_with_instances,
        singleton_instances=sum(i.status == "SINGLETON_INSTANCE_CANDIDATE" for i in instance_tuple),
        multi_region_instances=sum(len(i.region_ids) > 1 for i in instance_tuple),
    )


def instance_document(snapshot: InstanceSnapshot) -> dict[str, Any]:
    return {
        "schema": "reunion-companion.object-instance-reconstruction.v1",
        "phase": "Phase 4 - Object Reconstruction",
        "build": 21,
        "canonical_instances_allowed": False,
        "write_semantics_proven": False,
        "summary": {
            "instances": len(snapshot.instances),
            "resolved_regions": snapshot.resolved_regions,
            "unresolved_regions": snapshot.unresolved_region_count,
            "object_families": snapshot.object_families,
            "families_with_instances": snapshot.families_with_instances,
            "singleton_instances": snapshot.singleton_instances,
            "multi_region_instances": snapshot.multi_region_instances,
        },
        "instances": [
            {
                "instance_id": i.instance_id,
                "object_id": i.object_id,
                "object_type": i.object_type,
                "confidence": i.confidence,
                "status": i.status,
                "region_ids": list(i.region_ids),
                "roles": list(i.roles),
                "person_id": i.person_id,
                "record_id": i.record_id,
                "probe_ids": list(i.probe_ids),
                "evidence": list(i.evidence),
            }
            for i in snapshot.instances
        ],
        "unresolved_regions": list(snapshot.unresolved_regions),
    }


def build_from_pipeline(directory: str | Path):
    s16,s17,s18,s19,s20,p16,p17,p18,p19,p20 = load_pipeline(directory)
    snap = reconstruct_instances(s16,s17,s18,s19,s20)
    return snap,p16,p17,p18,p19,p20


def write_stage21(directory: str | Path):
    snap,p16,p17,p18,p19,p20 = build_from_pipeline(directory)
    artifact = make_artifact(
        21,
        "object-instance-reconstruction",
        instance_document(snap),
        {
            "stage16": hash_file(p16),
            "stage17": hash_file(p17),
            "stage18": hash_file(p18),
            "stage19": hash_file(p19),
            "stage20": hash_file(p20),
        },
    )
    target = Path(directory) / "stage-21-object-instances.json"
    return write_artifact(target, artifact), snap
