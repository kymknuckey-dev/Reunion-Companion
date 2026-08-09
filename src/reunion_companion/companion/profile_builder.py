from __future__ import annotations
from .knowledge_card import knowledge_card
from .confidence_engine import overall_confidence
from .research_engine import research_opportunities
from .evidence_summary import build_evidence_summary
from .discovery import relationship_connections

def build_profile(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone();card=knowledge_card(db,pid);evidence=build_evidence_summary(db,pid);connections=relationship_connections(db,pid)
    events=db.execute("SELECT * FROM events WHERE person_id=? AND event_type<>'Changed' ORDER BY id",(pid,)).fetchall();notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall();opp=research_opportunities(db,pid)
    core={}
    for typ in ("Birth","Death","Burial","Cremation","Occupation","Education","Religion"):
        vals=[e for e in events if e["event_type"]==typ]
        if vals:core[typ]=vals
    high=sum(1 for x in opp if x[0]=="High")
    status="Needs Review" if high>=3 else "Review Suggested" if high else "Sparse Evidence" if not evidence["sources"] else "Good"
    return {"person":p,"card":card,"evidence":evidence,"connections":connections,"events":events,"notes":notes,"core":core,"opportunities":opp,"confidence":overall_confidence(db,pid),"status":status}

def _event_line(e):
    return " — ".join([e["event_type"]]+[x for x in (e["date_text"],e["place_text"],e["value_text"]) if x and x!="Y"])

def format_profile(db,pid):
    d=build_profile(db,pid);p=d["person"]
    title=f"Research Profile — {p['display_name']}";L=[title,"="*len(title),"",f"Status                {d['status']}",f"Research confidence   {d['confidence']}%",f"Evidence linkage      {d['card']['evidence']}%",f"Sources               {len(d['evidence']['sources'])}",f"Citations             {d['evidence']['citation_count']}",f"Media                 {d['card']['media']}",f"Research items        {len(d['opportunities'])}",""]
    if d["core"]:
        L += ["Identity & Life","---------------"]
        for rows in d["core"].values():
            for e in rows[:2]:L.append(f"  {_event_line(e)}")
        L.append("")
    L += ["Family","------",f"  Parents   {len(d['connections']['parents'])}",f"  Spouses   {len(d['connections']['spouses'])}",f"  Children  {len(d['connections']['children'])}",f"  Siblings  {len(d['connections']['siblings'])}",""]
    if d["notes"]:
        L += ["Typed Notes","-----------"]
        for n in d["notes"]:
            t=n["note_type"] or n["gedcom_tag"] or "Note";text=" ".join((n["text"] or "").split())
            L.append(f"  {t}: {text[:180]}"+("…" if len(text)>180 else ""))
        L.append("")
    if d["opportunities"]:
        L += ["Highest Priority Research","-------------------------"]
        for priority,area,msg,detail in d["opportunities"][:8]:
            L.append(f"  [{priority}] {area} — {msg}")
            if detail:L.append(f"      {detail}")
    else:L += ["Research Review","---------------","  No obvious improvement opportunities detected from the imported snapshot."]
    return "\n".join(L)
