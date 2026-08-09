from __future__ import annotations
from collections import defaultdict
import re
from .beta_ui_service import person_confidence
from .family_publication_model import person_events,person_notes,person_sources,person_media

YEAR_RE=re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")

def _year(text):
    if not text:return None
    m=YEAR_RE.search(str(text))
    return int(m.group(1)) if m else None

def person_timeline_model(db,pid):
    from .timeline_engine import timeline_for_person
    t=timeline_for_person(db,pid)
    if not t:return None
    return {"person":t["person"],"events":[{
        "id":e["id"],"type":e["type"],"date":e["date"],"place":e["place"],
        "value":e["value"],"notes":[e["note"]] if e["note"] else [],
        "source_count":e["source_count"],"media_count":e["media_count"],
        "evidence_status":"supported" if e["evidence_status"]=="supported" else "unsourced",
        "year":e["year"]
    } for e in t["events"]]}

def person_anomalies(db,pid):
    t=person_timeline_model(db,pid)
    if not t:return []
    events=t["events"];out=[]
    birth=next((x for x in events if x["type"]=="Birth"),None)
    death=next((x for x in events if x["type"]=="Death"),None)
    by=birth["year"] if birth else None
    dy=death["year"] if death else None
    for e in events:
        y=e["year"]
        if y is not None and by and e["type"]!="Birth" and y<by:
            out.append({"kind":"chronology","severity":"warning","event_id":e["id"],
                        "message":f"{e['type']} ({y}) occurs before recorded birth ({by})."})
        if y is not None and dy and e["type"] not in ("Death","Burial","Cremation") and y>dy:
            out.append({"kind":"chronology","severity":"warning","event_id":e["id"],
                        "message":f"{e['type']} ({y}) occurs after recorded death ({dy})."})
        if e["evidence_status"]=="unsourced":
            out.append({"kind":"evidence","severity":"info","event_id":e["id"],
                        "message":f"{e['type']} has no directly attached source or media evidence."})
    for n in person_notes(db,pid):
        keys=set(n.keys())
        txt=(n["text"] if "text" in keys else None) or (n["note_text"] if "note_text" in keys else None) or ""
        low=txt.lower()
        if any(k in low for k in ("don't think","dont think","doubt","uncertain","believed","possibly","maybe")):
            out.append({"kind":"research-note","severity":"info","note_id":n["id"],
                        "message":"Research note contains uncertainty language and may need review."})
    return out

def person_research_model(db,pid):
    conf=person_confidence(db,pid)
    return {
        "confidence":conf,
        "anomalies":person_anomalies(db,pid),
        "missing_evidence":[x for x in conf["events"] if x["status"]=="unsourced"] if conf else [],
        "note_count":len(person_notes(db,pid)),
        "source_count":len(person_sources(db,pid)),
        "media_count":len(person_media(db,pid)),
    }

def normalize_place_text(place):
    if not place:return ""
    x=" ".join(str(place).split())
    x=re.sub(r"\bS\.?\s*A\.?\b","South Australia",x)
    x=re.sub(r"\s*,\s*",", ",x)
    x=x.strip(" ,.")
    return x

def place_variants(db,limit=500):
    rows=db.execute("""SELECT place_text,COUNT(*) n FROM events
                       WHERE place_text IS NOT NULL AND trim(place_text)<>''
                       GROUP BY place_text ORDER BY n DESC,place_text LIMIT ?""",(limit,)).fetchall()
    groups=defaultdict(list)
    for r in rows:
        key=normalize_place_text(r["place_text"]).lower()
        groups[key].append({"place":r["place_text"],"count":r["n"]})
    out=[]
    for items in groups.values():
        if len(items)>1:
            items=sorted(items,key=lambda x:(-x["count"],x["place"]))
            out.append({"canonical_suggestion":normalize_place_text(items[0]["place"]),"variants":items})
    out.sort(key=lambda g:-sum(x["count"] for x in g["variants"]))
    return out

def source_explorer(db):
    rows=db.execute("""SELECT s.*,
      (SELECT COUNT(*) FROM person_sources ps WHERE ps.source_id=s.id) person_links,
      (SELECT COUNT(*) FROM event_sources es WHERE es.source_id=s.id) event_links,
      (SELECT COUNT(*) FROM note_sources ns WHERE ns.source_id=s.id) note_links,
      (SELECT COUNT(*) FROM family_sources fs WHERE fs.source_id=s.id) family_links
      FROM sources s ORDER BY s.id""").fetchall()
    out=[]
    for r in rows:
        d=dict(r);d["usage_total"]=d["person_links"]+d["event_links"]+d["note_links"]+d["family_links"];out.append(d)
    return out

def media_explorer(db):
    cats=defaultdict(list)
    for r in db.execute("SELECT * FROM media ORDER BY id").fetchall():
        d=dict(r);path=(d.get("file_path") or "").lower();title=(d.get("title") or "").lower()
        if path.endswith((".pict",".pct",".pic")):cat="Legacy PICT"
        elif not d.get("exists_on_disk"):cat="Missing"
        elif any(x in title for x in ("birth certificate","marriage certificate","death certificate","certificate")):cat="Certificates"
        elif any(x in title for x in ("military","service","army","air force","raaf")):cat="Military"
        elif path.endswith(".pdf"):cat="PDF Documents"
        elif path.endswith((".jpg",".jpeg",".png",".gif",".webp")):cat="Images"
        else:cat="Other"
        cats[cat].append(d)
    return dict(cats)
