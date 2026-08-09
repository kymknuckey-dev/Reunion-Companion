from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
import re
from .noise_suppression import run_corpus_manifest

@dataclass(frozen=True, slots=True)
class CanonicalSpan:
    probe_id:str; semantic_label:str; operation:str; assessment_index:int
    original_category:str; region_category:str; recurrence:float
    specificity:float; confidence:float; signature:str
    before_start:int; before_end:int; after_start:int; after_end:int

@dataclass(frozen=True, slots=True)
class CanonicalRegion:
    region_id:str; probe_id:str; semantic_label:str; operation:str
    status:str; confidence:float; specificity:float
    before_start:int; before_end:int; after_start:int; after_end:int
    span_count:int; span_indices:tuple[int,...]; signatures:tuple[str,...]
    decoded_event_support:bool; object_class_support:bool; alignment_support:bool

@dataclass(frozen=True, slots=True)
class RegionOverlap:
    left_probe:str; right_probe:str; shared_signatures:int
    left_signatures:int; right_signatures:int; jaccard:float

@dataclass(frozen=True, slots=True)
class RegionCorpus:
    results:tuple; build15_patterns:tuple; build15_summary:object
    spans:tuple[CanonicalSpan,...]; regions:tuple[CanonicalRegion,...]
    overlaps:tuple[RegionOverlap,...]; recurrent_unknown_noise:int
    promoted_unknown_semantic:int; residual_unknown:int

_PATH=re.compile(r"/Users/[^\s]+")
_NUM=re.compile(r"\d+")
_WS=re.compile(r"\s+")

def normalized_span_signature(a):
    text=f"{a.span.before_ascii}\n{a.span.after_ascii}"
    text=_WS.sub(" ", _NUM.sub("#", _PATH.sub("<PATH>", text))).strip()
    markers=("[[pt:","BD&M","Certificate","reference","Test Probe",
             "NSMutableDictionary","NSDictionary","NSMutableArray","NSArray",
             "NSString","NSNumber","NSValue","LucidaGrande","tfField",
             "tfType","tfTitle","tfWrap","pPict",".familyfile14",
             "familyfile.familydata","Reunion Files")
    hits=sorted({m for m in markers if m.casefold() in text.casefold()})
    if hits:
        return a.category+":markers="+"|".join(hits)
    size=max(a.span.before_length,a.span.after_length)
    bucket=min(8192,((size+15)//16)*16)
    digest=sha1(text.encode("utf-8","replace")).hexdigest()[:10]
    return f"{a.category}:size={bucket}:content={digest}"

def extract_canonical_spans(results):
    bysig=defaultdict(set)
    for r in results:
        for a in r.differential.assessments:
            bysig[normalized_span_signature(a)].add(r.spec.probe_id)
    pop=len(results)
    recurrence={s:len(p)/pop for s,p in bysig.items()}
    out=[]
    for r in results:
        for a in r.differential.assessments:
            sig=normalized_span_signature(a); rec=recurrence[sig]; spec=1-rec
            if a.category in {"DOCUMENT_PATH","UI_ARCHIVE","CACHE_INDEX","DERIVED_BINARY"}:
                cat="KNOWN_SAVE_NOISE"; conf=max(a.confidence,.90)
            elif a.category in {"DECODED_EVENT","STRUCTURAL_SEMANTIC","TEXT_SEMANTIC_CANDIDATE"}:
                cat="SUPPORTED_SEMANTIC"; conf=max(a.confidence,.72+.20*spec)
            elif rec>=.55:
                cat="RECURRENT_SAVE_NOISE"; conf=min(.95,.65+.30*rec)
            elif rec<=.22:
                cat="PROBE_SPECIFIC_SEMANTIC"; conf=min(.90,.72+(.22-rec)*.60)
            else:
                cat="RESIDUAL_UNKNOWN"; conf=.45
            out.append(CanonicalSpan(
                r.spec.probe_id,r.spec.semantic_label,r.spec.operation,a.index,
                a.category,cat,rec,spec,conf,sig,
                a.span.before_start,a.span.before_end,a.span.after_start,a.span.after_end
            ))
    return out,recurrence

def _rid(probe,sigs):
    return "CR-"+sha1((probe+"\n"+"\n".join(sorted(sigs))).encode()).hexdigest()[:10].upper()

def build_regions(results,spans,merge_gap=48):
    byprobe=defaultdict(list); source={r.spec.probe_id:r for r in results}
    for s in spans:
        if s.region_category in {"SUPPORTED_SEMANTIC","PROBE_SPECIFIC_SEMANTIC"}:
            byprobe[s.probe_id].append(s)
    regions=[]
    for probe,items in byprobe.items():
        items.sort(key=lambda x:(x.before_start,x.after_start,x.assessment_index))
        groups=[]
        for s in items:
            if not groups:
                groups.append([s]); continue
            p=groups[-1][-1]
            if max(0,s.before_start-p.before_end)<=merge_gap and max(0,s.after_start-p.after_end)<=merge_gap:
                groups[-1].append(s)
            else:
                groups.append([s])
        raw=source[probe].differential.result
        for g in groups:
            sigs=tuple(sorted({x.signature for x in g}))
            spec=sum(x.specificity for x in g)/len(g)
            conf=sum(x.confidence for x in g)/len(g)
            conf=min(.99,conf+(.08 if raw.decoded_event_deltas else 0)+(.06 if raw.class_deltas else 0)+(.06 if raw.edge_deltas else 0)+min(.06,.01*(len(g)-1)))
            status="STRONG_CANDIDATE" if conf>=.90 and spec>=.70 else "CANDIDATE"
            regions.append(CanonicalRegion(
                _rid(probe,sigs),probe,source[probe].spec.semantic_label,source[probe].spec.operation,
                status,conf,spec,min(x.before_start for x in g),max(x.before_end for x in g),
                min(x.after_start for x in g),max(x.after_end for x in g),len(g),
                tuple(x.assessment_index for x in g),sigs,bool(raw.decoded_event_deltas),
                bool(raw.class_deltas),bool(raw.edge_deltas)
            ))
    return sorted(regions,key=lambda r:(-r.confidence,-r.specificity,r.probe_id,r.before_start))

def region_overlaps(regions):
    m=defaultdict(set)
    for r in regions: m[r.probe_id].update(r.signatures)
    probes=sorted(m); out=[]
    for i,a in enumerate(probes):
        for b in probes[i+1:]:
            shared=m[a]&m[b]
            if shared:
                union=m[a]|m[b]
                out.append(RegionOverlap(a,b,len(shared),len(m[a]),len(m[b]),len(shared)/len(union)))
    return sorted(out,key=lambda x:(-x.jaccard,-x.shared_signatures,x.left_probe,x.right_probe))

def extract_region_corpus(manifest_path):
    results,patterns,summary=run_corpus_manifest(manifest_path)
    spans,_=extract_canonical_spans(results)
    regions=build_regions(results,spans)
    return RegionCorpus(tuple(results),tuple(patterns),summary,tuple(spans),tuple(regions),
        tuple(region_overlaps(regions)),
        sum(s.region_category=="RECURRENT_SAVE_NOISE" for s in spans),
        sum(s.region_category=="PROBE_SPECIFIC_SEMANTIC" for s in spans),
        sum(s.region_category=="RESIDUAL_UNKNOWN" for s in spans))

def region_document(c):
    return {
      "schema":"reunion-companion.canonical-regions.v1","build":16,
      "canonical_claims_allowed":False,
      "canonical_requirement":"replicated same-semantic controlled probes",
      "summary":{
        "probes":c.build15_summary.probes,
        "build15_unknown_spans":c.build15_summary.unknown_spans,
        "recurrent_unknown_reclassified_as_noise":c.recurrent_unknown_noise,
        "unknown_promoted_to_probe_specific_semantic":c.promoted_unknown_semantic,
        "residual_unknown":c.residual_unknown,
        "region_candidates":len(c.regions),
        "strong_candidates":sum(r.status=="STRONG_CANDIDATE" for r in c.regions),
        "overlap_pairs":len(c.overlaps)},
      "regions":[r.__dict__ if hasattr(r,"__dict__") else {
        "region_id":r.region_id,"probe_id":r.probe_id,"semantic_label":r.semantic_label,
        "operation":r.operation,"status":r.status,"confidence":r.confidence,
        "specificity":r.specificity,"before":[r.before_start,r.before_end],
        "after":[r.after_start,r.after_end],"span_count":r.span_count,
        "span_indices":list(r.span_indices),"signatures":list(r.signatures),
        "decoded_event_support":r.decoded_event_support,
        "object_class_support":r.object_class_support,
        "alignment_support":r.alignment_support} for r in c.regions],
      "overlaps":[{"left_probe":o.left_probe,"right_probe":o.right_probe,
        "shared_signatures":o.shared_signatures,"jaccard":o.jaccard} for o in c.overlaps]
    }
