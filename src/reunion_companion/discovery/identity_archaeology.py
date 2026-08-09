"""Build 22 Identity Archaeology Engine.

Purpose:
Find the missing identity/ownership layer that prevents Build 21 from
reconstructing individual object instances.

Build 22 traces unresolved canonical regions backwards through Stage 16-21,
inventories candidate identity keys, tests consistency and exclusivity, and
produces an explicit verdict:

GO
    A stable identity key is present with strong coverage/exclusivity.
PARTIAL
    Identity signals exist but are incomplete or inconsistent.
STOP
    The accumulated pipeline does not retain enough identity information to
    justify further instance reconstruction without new probes/raw extraction.

Build 22 does not invent IDs. It only scores identifiers/coordinates that are
actually present in prior artifacts.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from .pipeline_artifacts import hash_file, make_artifact, read_artifact, write_artifact


@dataclass(frozen=True, slots=True)
class IdentityKeyEvidence:
    key_name: str
    observations: int
    distinct_values: int
    covered_regions: int
    coverage: float
    exclusivity: float
    collision_rate: float
    multi_region_groups: int
    score: float
    grade: str
    sample_values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RegionIdentity:
    region_id: str
    object_type: str | None
    semantic_label: str | None
    person_ids: tuple[str, ...]
    record_ids: tuple[str, ...]
    probe_ids: tuple[str, ...]
    before_spans: tuple[tuple[int,int], ...]
    after_spans: tuple[tuple[int,int], ...]
    candidate_keys: tuple[str, ...]
    unresolved: bool


@dataclass(frozen=True, slots=True)
class IdentitySnapshot:
    key_evidence: tuple[IdentityKeyEvidence, ...]
    regions: tuple[RegionIdentity, ...]
    total_regions: int
    unresolved_regions: int
    regions_with_any_identity: int
    regions_with_person_id: int
    regions_with_record_id: int
    regions_with_probe_id: int
    verdict: str
    verdict_reason: str


def _unwrap(path: Path) -> dict[str,Any]:
    d=json.loads(path.read_text(encoding="utf-8"))
    if d.get("schema")=="reunion-companion.discovery-artifact.v1":
        return read_artifact(path).payload
    return d


def load_pipeline(directory: str | Path):
    base=Path(directory).expanduser()
    paths=[
        base/"stage-16-canonical-regions.json",
        base/"stage-17-architecture.json",
        base/"stage-18-semantic-confidence.json",
        base/"stage-19-region-dependency-graph.json",
        base/"stage-20-object-reconstruction.json",
        base/"stage-21-object-instances.json",
    ]
    missing=[str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing pipeline artifact(s): "+", ".join(missing))
    payloads=[_unwrap(p) for p in paths]
    return (*payloads,*paths)


def _rows(stage16):
    for key in ("regions","canonical_regions"):
        if isinstance(stage16.get(key),list):
            return stage16[key]
    p=stage16.get("payload")
    if isinstance(p,dict):
        for key in ("regions","canonical_regions"):
            if isinstance(p.get(key),list):
                return p[key]
    return []


def _first(d,*keys):
    for k in keys:
        if d.get(k) is not None:
            return d.get(k)
    return None


def _int(v):
    try:return int(v)
    except (TypeError,ValueError):return None


def _stage20_region_map(stage20):
    out={}
    for obj in stage20.get("objects",[]):
        for m in obj.get("members",[]):
            out[m["region_id"]]=(obj.get("object_type"),m.get("semantic_label"))
    return out


def _key_score(region_values: dict[str,set[str]], total_regions: int):
    covered=sum(1 for v in region_values.values() if v)
    observations=sum(len(v) for v in region_values.values())
    values=defaultdict(set)
    for rid,vals in region_values.items():
        for v in vals: values[v].add(rid)
    distinct=len(values)
    multi=sum(1 for rs in values.values() if len(rs)>1)
    collisions=sum(max(0,len(rs)-1) for rs in values.values())
    coverage=covered/max(1,total_regions)
    # Exclusivity rewards one region -> one value, but we also want values that
    # group multiple related regions. Therefore don't punish multi-region groups
    # harshly; collision_rate is reported separately.
    exclusive_regions=sum(1 for vals in region_values.values() if len(vals)<=1)
    exclusivity=exclusive_regions/max(1,total_regions)
    collision_rate=collisions/max(1,covered)
    grouping_bonus=min(.20,multi/max(1,distinct)*.20)
    score=max(0,min(.99,.50*coverage+.30*exclusivity+.20*(1-min(1,collision_rate))+grouping_bonus))
    if score>=.90 and coverage>=.75: grade="STRONG_IDENTITY_CANDIDATE"
    elif score>=.75 and coverage>=.40: grade="SUPPORTED_IDENTITY_CANDIDATE"
    elif coverage>0: grade="WEAK_IDENTITY_SIGNAL"
    else: grade="ABSENT"
    return observations,distinct,covered,coverage,exclusivity,collision_rate,multi,score,grade,values


def analyse_identity(stage16,stage17,stage18,stage19,stage20,stage21):
    unresolved=set(stage21.get("unresolved_regions",[]))
    region_meta=_stage20_region_map(stage20)

    person=defaultdict(set); record=defaultdict(set); probe=defaultdict(set)
    before=defaultdict(set); after=defaultdict(set)

    # Stage 16 is the primary source for physical identity/locality.
    for r in _rows(stage16):
        rid=r.get("region_id")
        if not rid: continue
        pv=_first(r,"person_id","person","owner_person_id")
        rv=_first(r,"record_id","record","person_record_id")
        qv=_first(r,"probe_id","probe","semantic_probe")
        if pv is not None: person[rid].add(str(pv))
        if rv is not None: record[rid].add(str(rv))
        if qv is not None: probe[rid].add(str(qv))
        bs=_int(_first(r,"before_start","before_offset","left_start"))
        be=_int(_first(r,"before_end","before_stop","left_end"))
        if bs is not None and be is not None: before[rid].add((bs,be))
        astart=_int(_first(r,"after_start","after_offset","right_start"))
        aend=_int(_first(r,"after_end","after_stop","right_end"))
        if astart is not None and aend is not None: after[rid].add((astart,aend))

    # Determine the region universe from Stage 20/21 rather than raw Stage 16,
    # because these are the regions we ultimately need to identify.
    universe=set(region_meta)|set(unresolved)
    for inst in stage21.get("instances",[]):
        universe.update(inst.get("region_ids",[]))
    total=len(universe)

    key_maps={
        "person_id":{rid:set(person.get(rid,set())) for rid in universe},
        "record_id":{rid:set(record.get(rid,set())) for rid in universe},
        "probe_id":{rid:set(probe.get(rid,set())) for rid in universe},
        "before_span":{rid:{f"{a}:{b}" for a,b in before.get(rid,set())} for rid in universe},
        "after_span":{rid:{f"{a}:{b}" for a,b in after.get(rid,set())} for rid in universe},
    }

    key_evidence=[]
    for key_name,m in key_maps.items():
        obs,distinct,covered,cov,exc,col,multi,score,grade,values=_key_score(m,total)
        samples=tuple(sorted(values)[:8])
        key_evidence.append(IdentityKeyEvidence(
            key_name,obs,distinct,covered,cov,exc,col,multi,score,grade,samples
        ))

    regions=[]
    any_identity=0
    for rid in sorted(universe):
        candidates=[]
        if person.get(rid): candidates.append("person_id")
        if record.get(rid): candidates.append("record_id")
        if probe.get(rid): candidates.append("probe_id")
        if before.get(rid): candidates.append("before_span")
        if after.get(rid): candidates.append("after_span")
        if candidates:any_identity+=1
        typ,label=region_meta.get(rid,(None,None))
        regions.append(RegionIdentity(
            region_id=rid,object_type=typ,semantic_label=label,
            person_ids=tuple(sorted(person.get(rid,set()))),
            record_ids=tuple(sorted(record.get(rid,set()))),
            probe_ids=tuple(sorted(probe.get(rid,set()))),
            before_spans=tuple(sorted(before.get(rid,set()))),
            after_spans=tuple(sorted(after.get(rid,set()))),
            candidate_keys=tuple(candidates),
            unresolved=rid in unresolved,
        ))

    # Verdict focuses on ownership keys first, physical coordinates second.
    by_name={k.key_name:k for k in key_evidence}
    strong_owner=max(
        by_name["record_id"].score if by_name["record_id"].coverage else 0,
        by_name["person_id"].score if by_name["person_id"].coverage else 0,
    )
    owner_cov=max(by_name["record_id"].coverage,by_name["person_id"].coverage)
    span_cov=max(by_name["before_span"].coverage,by_name["after_span"].coverage)

    if strong_owner>=.90 and owner_cov>=.75:
        verdict="GO"
        reason="A strong explicit owner/record identity key survives the pipeline with broad coverage."
    elif owner_cov>=.25 or span_cov>=.50:
        verdict="PARTIAL"
        reason="Identity/locality signals survive, but coverage is insufficient for reliable instance reconstruction."
    else:
        verdict="STOP"
        reason="The accumulated pipeline does not retain enough owner/locality evidence to recover object instances reliably."

    return IdentitySnapshot(
        key_evidence=tuple(sorted(key_evidence,key=lambda k:(-k.score,k.key_name))),
        regions=tuple(regions),
        total_regions=total,
        unresolved_regions=len(unresolved),
        regions_with_any_identity=any_identity,
        regions_with_person_id=sum(bool(person.get(r)) for r in universe),
        regions_with_record_id=sum(bool(record.get(r)) for r in universe),
        regions_with_probe_id=sum(bool(probe.get(r)) for r in universe),
        verdict=verdict,
        verdict_reason=reason,
    )


def identity_document(s):
    return {
      "schema":"reunion-companion.identity-archaeology.v1",
      "phase":"Phase 4 - Object Reconstruction",
      "build":22,
      "canonical_identity_allowed":False,
      "write_semantics_proven":False,
      "summary":{
        "total_regions":s.total_regions,
        "unresolved_regions":s.unresolved_regions,
        "regions_with_any_identity":s.regions_with_any_identity,
        "regions_with_person_id":s.regions_with_person_id,
        "regions_with_record_id":s.regions_with_record_id,
        "regions_with_probe_id":s.regions_with_probe_id,
        "verdict":s.verdict,
        "verdict_reason":s.verdict_reason,
      },
      "keys":[{
        "key_name":k.key_name,"observations":k.observations,"distinct_values":k.distinct_values,
        "covered_regions":k.covered_regions,"coverage":k.coverage,"exclusivity":k.exclusivity,
        "collision_rate":k.collision_rate,"multi_region_groups":k.multi_region_groups,
        "score":k.score,"grade":k.grade,"sample_values":list(k.sample_values)
      } for k in s.key_evidence],
      "regions":[{
        "region_id":r.region_id,"object_type":r.object_type,"semantic_label":r.semantic_label,
        "person_ids":list(r.person_ids),"record_ids":list(r.record_ids),"probe_ids":list(r.probe_ids),
        "before_spans":[list(x) for x in r.before_spans],"after_spans":[list(x) for x in r.after_spans],
        "candidate_keys":list(r.candidate_keys),"unresolved":r.unresolved
      } for r in s.regions]
    }


def build_from_pipeline(directory):
    s16,s17,s18,s19,s20,s21,p16,p17,p18,p19,p20,p21=load_pipeline(directory)
    return analyse_identity(s16,s17,s18,s19,s20,s21),p16,p17,p18,p19,p20,p21


def write_stage22(directory):
    s,p16,p17,p18,p19,p20,p21=build_from_pipeline(directory)
    a=make_artifact(22,"identity-archaeology",identity_document(s),{
      "stage16":hash_file(p16),"stage17":hash_file(p17),"stage18":hash_file(p18),
      "stage19":hash_file(p19),"stage20":hash_file(p20),"stage21":hash_file(p21)})
    target=Path(directory)/"stage-22-identity-archaeology.json"
    return write_artifact(target,a),s
