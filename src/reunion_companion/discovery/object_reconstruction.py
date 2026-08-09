from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import json
from .pipeline_artifacts import hash_file, make_artifact, read_artifact, write_artifact

@dataclass(frozen=True, slots=True)
class ObjectMember:
    region_id: str
    semantic_label: str
    score: float
    membership_confidence: float
    role: str
    evidence: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ReconstructedObject:
    object_id: str
    object_type: str
    confidence: float
    completeness: float
    status: str
    members: tuple[ObjectMember, ...]
    evidence: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ObjectRelation:
    relation_id: str
    source_object: str
    target_object: str
    relation: str
    confidence: float
    evidence: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ReconstructionSnapshot:
    objects: tuple[ReconstructedObject, ...]
    relations: tuple[ObjectRelation, ...]
    total_members: int
    shared_members: int
    unknown_members: int
    verified_objects: int
    high_confidence_objects: int
    candidate_objects: int

def _unwrap(path):
    p=Path(path)
    d=json.loads(p.read_text(encoding="utf-8"))
    return read_artifact(p).payload if d.get("schema")=="reunion-companion.discovery-artifact.v1" else d

def load_pipeline(directory):
    d=Path(directory).expanduser()
    p16=d/"stage-16-canonical-regions.json"; p17=d/"stage-17-architecture.json"
    p18=d/"stage-18-semantic-confidence.json"; p19=d/"stage-19-region-dependency-graph.json"
    missing=[str(p) for p in (p16,p17,p18,p19) if not p.is_file()]
    if missing: raise FileNotFoundError("Missing pipeline artifact(s): "+", ".join(missing))
    return _unwrap(p16),_unwrap(p17),_unwrap(p18),_unwrap(p19),p16,p17,p18,p19

def _oid(t): return "RO-"+sha1(t.encode("utf-8")).hexdigest()[:10].upper()
def _rid(a,b,r): return "OR-"+sha1(f"{a}|{b}|{r}".encode("utf-8")).hexdigest()[:10].upper()

def _semantic_object(label):
    m={
      "Birth Date":("Birth Event","FIELD_DATE"),
      "Birth Place":("Birth Event","FIELD_PLACE"),
      "Birth Memo":("Birth Event","FIELD_MEMO"),
      "Marriage":("Marriage Event","EVENT_BODY"),
      "Occupation":("Occupation","VALUE"),
      "Education":("Education","VALUE"),
      "Religion":("Religion","VALUE"),
      "Research Note":("Research Notes","NOTE_BODY"),
      "Misc Note":("Misc Notes","NOTE_BODY"),
    }
    return m.get(label,("UNKNOWN","UNKNOWN"))

def reconstruct_objects(stage16,stage17,stage18,stage19):
    nodes=stage19.get("nodes",[]); edges=stage19.get("edges",[])
    edge_by_region=defaultdict(list)
    for e in edges:
        edge_by_region[e["source"]].append(e); edge_by_region[e["target"]].append(e)

    grouped=defaultdict(list)
    for n in nodes:
        t,role=_semantic_object(n.get("semantic_label",""))
        grouped[t].append((n,role))

    expected={
      "Birth Event":{"FIELD_DATE","FIELD_PLACE","FIELD_MEMO"},
      "Marriage Event":{"EVENT_BODY"},
      "Occupation":{"VALUE"},"Education":{"VALUE"},"Religion":{"VALUE"},
      "Research Notes":{"NOTE_BODY"},"Misc Notes":{"NOTE_BODY"},"UNKNOWN":{"UNKNOWN"},
    }

    objects=[]; member_owner={}; shared=0; unknown=0
    for typ,rows in sorted(grouped.items()):
        members=[]; roles=set(); mscores=[]
        for n,role in rows:
            roles.add(role)
            es=edge_by_region.get(n["region_id"],[])
            same=[e for e in es if e.get("relation")=="SAME_SEMANTIC_COMPONENT"]
            struct=[e for e in es if e.get("relation")=="SHARED_STRUCTURAL_SUPPORT"]
            cross=[e for e in es if e.get("relation")=="CROSS_SEMANTIC_SIGNATURE"]
            base=float(n.get("score",0))
            mc=max(0,min(.99,base+min(.06,.01*len(same))+min(.04,.01*len(struct))-min(.05,.01*len(cross))))
            if typ=="UNKNOWN": unknown+=1
            members.append(ObjectMember(n["region_id"],n.get("semantic_label",""),base,mc,role,(
                f"Build18 semantic-confidence={base:.3f}",
                f"same-semantic-edges={len(same)}",
                f"structural-support-edges={len(struct)}",
                f"cross-semantic-edges={len(cross)}",
            )))
            mscores.append(mc)

        completeness=len(roles & expected[typ])/max(1,len(expected[typ]))
        mean=sum(mscores)/max(1,len(mscores))
        density_penalty=min(.08,max(0,len(members)-12)*.001)
        conf=max(0,min(.99,mean-density_penalty))
        if typ=="UNKNOWN": status="UNKNOWN"
        elif conf>=.94 and completeness>=.66: status="VERIFIED_OBJECT_CANDIDATE"
        elif conf>=.85: status="HIGH_CONFIDENCE_OBJECT"
        else: status="OBJECT_CANDIDATE"

        obj=ReconstructedObject(_oid(typ),typ,conf,completeness,status,
            tuple(sorted(members,key=lambda m:(-m.membership_confidence,m.region_id))),
            (f"semantic grouping={typ}",f"region-count={len(rows)}"))
        objects.append(obj)
        for m in obj.members:
            if m.region_id in member_owner and member_owner[m.region_id]!=obj.object_id: shared+=1
            member_owner[m.region_id]=obj.object_id

    rels={}
    for e in edges:
        if e.get("relation") not in {"CROSS_SEMANTIC_SIGNATURE","ARCHITECTURAL_LINK"}: continue
        so=member_owner.get(e["source"]); to=member_owner.get(e["target"])
        if not so or not to or so==to: continue
        rel="SEMANTIC_ASSOCIATION" if e["relation"]=="CROSS_SEMANTIC_SIGNATURE" else "ARCHITECTURAL_ASSOCIATION"
        key=(so,to,rel); conf=float(e.get("confidence",0))
        cand=ObjectRelation(_rid(so,to,rel),so,to,rel,conf,(f"Build19 edge={e.get('edge_id')}",))
        if key not in rels or conf>rels[key].confidence: rels[key]=cand

    objs=tuple(sorted(objects,key=lambda o:(-o.confidence,o.object_type)))
    rls=tuple(sorted(rels.values(),key=lambda r:(-r.confidence,r.relation,r.source_object,r.target_object)))
    return ReconstructionSnapshot(
        objs,rls,sum(len(o.members) for o in objs),shared,unknown,
        sum(o.status=="VERIFIED_OBJECT_CANDIDATE" for o in objs),
        sum(o.status=="HIGH_CONFIDENCE_OBJECT" for o in objs),
        sum(o.status=="OBJECT_CANDIDATE" for o in objs),
    )

def reconstruction_document(s):
    return {
      "schema":"reunion-companion.object-reconstruction.v1",
      "phase":"Phase 4 - Object Reconstruction","build":20,
      "canonical_objects_allowed":False,"write_semantics_proven":False,
      "summary":{"objects":len(s.objects),"relations":len(s.relations),"total_members":s.total_members,
                 "shared_members":s.shared_members,"unknown_members":s.unknown_members,
                 "verified_object_candidates":s.verified_objects,
                 "high_confidence_objects":s.high_confidence_objects,
                 "object_candidates":s.candidate_objects},
      "objects":[{"object_id":o.object_id,"object_type":o.object_type,"confidence":o.confidence,
                  "completeness":o.completeness,"status":o.status,"evidence":list(o.evidence),
                  "members":[{"region_id":m.region_id,"semantic_label":m.semantic_label,"score":m.score,
                              "membership_confidence":m.membership_confidence,"role":m.role,
                              "evidence":list(m.evidence)} for m in o.members]} for o in s.objects],
      "relations":[{"relation_id":r.relation_id,"source_object":r.source_object,"target_object":r.target_object,
                    "relation":r.relation,"confidence":r.confidence,"evidence":list(r.evidence)} for r in s.relations]
    }

def build_from_pipeline(directory):
    s16,s17,s18,s19,p16,p17,p18,p19=load_pipeline(directory)
    return reconstruct_objects(s16,s17,s18,s19),p16,p17,p18,p19

def write_stage20(directory):
    s,p16,p17,p18,p19=build_from_pipeline(directory)
    a=make_artifact(20,"object-reconstruction",reconstruction_document(s),
        {"stage16":hash_file(p16),"stage17":hash_file(p17),"stage18":hash_file(p18),"stage19":hash_file(p19)})
    return write_artifact(Path(directory)/"stage-20-object-reconstruction.json",a),s
