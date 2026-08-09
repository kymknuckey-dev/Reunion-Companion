from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from .evidence_engine import event_evidence

@dataclass
class ConfidenceItem:
    area: str
    score: int
    level: str
    reason: str

CORE_TYPES=("Birth","Death","Burial","Cremation","Marriage")

def _level(score):
    if score >= 85: return "Very High"
    if score >= 70: return "High"
    if score >= 50: return "Moderate"
    if score >= 25: return "Low"
    return "Very Low"

def _stars(score):
    n=max(1,min(5,round(score/20)))
    return "★"*n+"☆"*(5-n)

def _event_items(db,pid):
    rows=[]
    events=db.execute("SELECT * FROM events WHERE person_id=? AND event_type<>'Changed' ORDER BY id",(pid,)).fetchall()
    grouped=defaultdict(list)
    for e in events: grouped[e["event_type"]].append(e)
    for typ,items in grouped.items():
        evid=[event_evidence(db,e["id"]) for e in items]
        score=max((x["score"] for x in evid),default=0)
        values={(e["date_text"] or "",e["place_text"] or "",e["value_text"] or "") for e in items}
        meaningful={v for v in values if any(v)}
        conflict=len(meaningful)>1 and typ in CORE_TYPES
        if conflict: score=max(0,score-25)
        source_count=max((len(x["sources"]) for x in evid),default=0)
        media_count=max((len(x["media"]) for x in evid),default=0)
        reason=[]
        if source_count: reason.append(f"{source_count} linked source{'s' if source_count!=1 else ''}")
        if media_count: reason.append(f"{media_count} linked document/media item{'s' if media_count!=1 else ''}")
        if conflict: reason.append("conflicting recorded values")
        if not reason: reason.append("no linked source or document visible")
        rows.append(ConfidenceItem(typ,score,_level(score),"; ".join(reason)))
    return rows

def _note_topic_items(db,pid):
    rows=[]
    notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    for n in notes:
        label=n["note_type"] or n["gedcom_tag"] or "Note"
        links=db.execute("SELECT COUNT(*) FROM note_sources WHERE note_id=?",(n["id"],)).fetchone()[0]
        score=65 if links else 35
        if label.lower()=="research": score=min(score,55)
        reason=(f"{links} linked source{'s' if links!=1 else ''}" if links else "authored note with no linked source")
        rows.append(ConfidenceItem(label,score,_level(score),reason))
    return rows

def confidence_profile(db,pid):
    items=_event_items(db,pid)+_note_topic_items(db,pid)
    best={}
    for x in items:
        if x.area not in best or x.score>best[x.area].score: best[x.area]=x
    return sorted(best.values(),key=lambda x:(x.area.lower(),-x.score))

def overall_confidence(db,pid):
    items=confidence_profile(db,pid)
    core=[x for x in items if x.area in CORE_TYPES]
    use=core or items
    return round(sum(x.score for x in use)/len(use)) if use else 0

def format_confidence(db,pid):
    p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    title=f"Research Confidence — {p['display_name']}"
    L=[title,"="*len(title),""]
    items=confidence_profile(db,pid)
    if not items: L.append("No confidence-bearing material found.")
    else:
        for x in items:
            L.append(f"{x.area:<24} {_stars(x.score)}  {x.score:>3}%  {x.level}")
            L.append(f"  {x.reason}")
    L += ["",f"Overall visible confidence: {overall_confidence(db,pid)}%","","Interpretation","--------------","Scores measure visible support and consistency in the imported Reunion snapshot. They are not a declaration that a historical claim is true or false."]
    return "\n".join(L)
