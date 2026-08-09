from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import json
from .pipeline_artifacts import hash_file, make_artifact, read_artifact, write_artifact

@dataclass(frozen=True,slots=True)
class Node:
    region_id:str; semantic_label:str; probe_id:str; score:float; grade:str
    occurrence_count:int; decoded_support:bool; object_class_support:bool; alignment_support:bool

@dataclass(frozen=True,slots=True)
class Edge:
    edge_id:str; source:str; target:str; relation:str; confidence:float; directed:bool; evidence:tuple[str,...]

@dataclass(frozen=True,slots=True)
class Graph:
    nodes:tuple[Node,...]; edges:tuple[Edge,...]; duplicate_rows_collapsed:int; contradictory_nodes:int

def _unwrap(p):
    d=json.loads(Path(p).read_text(encoding="utf-8"))
    return read_artifact(p).payload if d.get("schema")=="reunion-companion.discovery-artifact.v1" else d

def load_pipeline(directory):
    d=Path(directory).expanduser()
    p16=d/"stage-16-canonical-regions.json"; p17=d/"stage-17-architecture.json"; p18=d/"stage-18-semantic-confidence.json"
    missing=[str(p) for p in (p16,p17,p18) if not p.is_file()]
    if missing: raise FileNotFoundError("Missing pipeline artifact(s): "+", ".join(missing))
    return _unwrap(p16),_unwrap(p17),_unwrap(p18),p16,p17,p18

def _eid(a,b,rel):
    x,y=sorted((a,b)); return "DE-"+sha1(f"{x}|{y}|{rel}".encode()).hexdigest()[:10].upper()

def _rows(stage18):
    if stage18.get("schema")=="reunion-companion.semantic-confidence.v1": return stage18.get("regions",[])
    return stage18.get("payload",{}).get("regions",[])

def build_graph(stage16,stage17,stage18):
    grouped=defaultdict(list)
    for r in _rows(stage18): grouped[r["region_id"]].append(r)
    nodes=[]; collapsed=0
    rank={"VERIFIED_CANDIDATE":5,"HIGH_CONFIDENCE":4,"SUPPORTED":3,"TENTATIVE":2,"LOW":1}
    for rid,g in grouped.items():
        collapsed += len(g)-1
        labels={x.get("semantic_label","") for x in g}; probes={x.get("probe_id","") for x in g}
        label=next(iter(labels)) if len(labels)==1 else "CONTRADICTORY:"+"|".join(sorted(labels))
        probe=next(iter(probes)) if len(probes)==1 else "MULTI:"+"|".join(sorted(probes))
        nodes.append(Node(rid,label,probe,max(float(x.get("score",0)) for x in g),
            max((x.get("grade","LOW") for x in g),key=lambda z:rank.get(z,0)),
            max(int(x.get("occurrence_count",1)) for x in g),
            any(x.get("decoded_support",False) for x in g),
            any(x.get("object_class_support",False) for x in g),
            any(x.get("alignment_support",False) for x in g)))
    byid={n.region_id:n for n in nodes}; bylabel=defaultdict(list); byprobe=defaultdict(list)
    for n in nodes: bylabel[n.semantic_label].append(n); byprobe[n.probe_id].append(n)
    edges={}
    def add(a,b,rel,conf,evidence,directed=False):
        if a==b or a not in byid or b not in byid: return
        key=(a,b,rel) if directed else (*sorted((a,b)),rel)
        e=Edge(_eid(a,b,rel),a,b,rel,max(0,min(.99,conf)),directed,tuple(evidence))
        if key not in edges or e.confidence>edges[key].confidence: edges[key]=e

    # Same semantic component: hub-and-spoke to prevent clique explosion.
    for label,g in bylabel.items():
        if label.startswith("CONTRADICTORY:"): continue
        g=sorted((n for n in g if n.score>=.80),key=lambda n:(-n.score,n.region_id))
        if len(g)>1:
            hub=g[0]
            for n in g[1:]:
                add(hub.region_id,n.region_id,"SAME_SEMANTIC_COMPONENT",min(hub.score,n.score)*.92,[f"semantic-label={label}"])

    # Shared direct support.
    supports=defaultdict(list)
    for n in nodes:
        k=(n.decoded_support,n.object_class_support,n.alignment_support)
        if any(k): supports[k].append(n)
    for k,g in supports.items():
        g=sorted(g,key=lambda n:(-n.score,n.region_id))
        if len(g)>1:
            hub=g[0]; boost=.72+.06*sum(map(int,k))
            for n in g[1:]:
                add(hub.region_id,n.region_id,"SHARED_STRUCTURAL_SUPPORT",min(hub.score,n.score)*boost,[f"support={k}"])

    strongest={p:max(g,key=lambda n:n.score) for p,g in byprobe.items() if g}
    for o in stage16.get("overlaps",[]):
        a=strongest.get(o.get("left_probe")); b=strongest.get(o.get("right_probe"))
        if a and b:
            j=float(o.get("jaccard",0)); add(a.region_id,b.region_id,"CROSS_SEMANTIC_SIGNATURE",min(a.score,b.score)*min(1,.55+j),[f"jaccard={j:.3f}"])

    comp_probe={c.get("component_id"):c.get("probe_id") for c in stage17.get("components",[]) if c.get("component_id")}
    for l in stage17.get("links",[]):
        a=strongest.get(comp_probe.get(l.get("source"))); b=strongest.get(comp_probe.get(l.get("target")))
        if a and b and a.region_id!=b.region_id:
            add(a.region_id,b.region_id,"ARCHITECTURAL_LINK",min(a.score,b.score,float(l.get("confidence",0))),[f"build17-relation={l.get('relation')}"],True)

    return Graph(tuple(sorted(nodes,key=lambda n:(-n.score,n.semantic_label,n.region_id))),
                 tuple(sorted(edges.values(),key=lambda e:(-e.confidence,e.relation,e.source,e.target))),
                 collapsed,sum(n.semantic_label.startswith("CONTRADICTORY:") for n in nodes))

def document(g):
    return {"schema":"reunion-companion.region-dependency-graph.v1","phase":"Phase 3 - Database Architecture Reconstruction","build":19,
      "canonical_edges_allowed":False,"edge_requirement":"replicated structural/semantic evidence across independent probes",
      "summary":{"nodes":len(g.nodes),"edges":len(g.edges),"duplicate_rows_collapsed":g.duplicate_rows_collapsed,"contradictory_nodes":g.contradictory_nodes,
                 "semantic_components":len({n.semantic_label for n in g.nodes if not n.semantic_label.startswith("CONTRADICTORY:")}),
                 "cross_semantic_edges":sum(e.relation=="CROSS_SEMANTIC_SIGNATURE" for e in g.edges),
                 "structural_edges":sum(e.relation=="SHARED_STRUCTURAL_SUPPORT" for e in g.edges),
                 "architecture_edges":sum(e.relation=="ARCHITECTURAL_LINK" for e in g.edges)},
      "nodes":[n.__dict__ if hasattr(n,"__dict__") else {"region_id":n.region_id,"semantic_label":n.semantic_label,"probe_id":n.probe_id,"score":n.score,"grade":n.grade,"occurrence_count":n.occurrence_count,"decoded_support":n.decoded_support,"object_class_support":n.object_class_support,"alignment_support":n.alignment_support} for n in g.nodes],
      "edges":[{"edge_id":e.edge_id,"source":e.source,"target":e.target,"relation":e.relation,"confidence":e.confidence,"directed":e.directed,"evidence":list(e.evidence)} for e in g.edges]}

def build_from_pipeline(directory):
    s16,s17,s18,p16,p17,p18=load_pipeline(directory); return build_graph(s16,s17,s18),p16,p17,p18

def write_stage19(directory):
    g,p16,p17,p18=build_from_pipeline(directory)
    a=make_artifact(19,"region-dependency-graph",document(g),{"stage16":hash_file(p16),"stage17":hash_file(p17),"stage18":hash_file(p18)})
    return write_artifact(Path(directory)/"stage-19-region-dependency-graph.json",a),g
