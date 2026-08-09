from __future__ import annotations
from .discovery import relationship_connections
from .family_publication_model import (
    life_dates,person_events,person_notes,person_sources,person_media,
    spouse_families,family_partners,children,family_overview
)

def _dicts(rows): return [dict(x) for x in rows]

def search_people(db,text,limit=40):
    q=(text or "").strip()
    if not q:
        rows=db.execute("SELECT id,display_name,sex,gedcom_xref FROM people ORDER BY display_name LIMIT ?",(limit,)).fetchall()
    else:
        rows=db.execute("""SELECT id,display_name,sex,gedcom_xref FROM people
                           WHERE lower(display_name) LIKE ?
                           ORDER BY CASE WHEN lower(display_name)=? THEN 0 ELSE 1 END,display_name
                           LIMIT ?""",(f"%{q.lower()}%",q.lower(),limit)).fetchall()
    return _dicts(rows)

def person_confidence(db,pid):
    p=db.execute("SELECT id FROM people WHERE id=?",(pid,)).fetchone()
    if not p:return None
    events=person_events(db,pid)
    rows=[]; total=supported=0
    for e in events:
        if e["event_type"]=="Changed": continue
        total+=1
        sc=db.execute("SELECT COUNT(*) FROM event_sources WHERE event_id=?",(e["id"],)).fetchone()[0]
        mc=db.execute("SELECT COUNT(*) FROM event_media WHERE event_id=?",(e["id"],)).fetchone()[0]
        ok=bool(sc or mc)
        if ok:supported+=1
        rows.append({
            "id":e["id"],"type":e["event_type"],"date":e["date_text"],
            "place":e["place_text"],"value":e["value_text"],
            "source_count":sc,"media_count":mc,
            "status":"supported" if ok else "unsourced"
        })
    try:
        sources=person_sources(db,pid)
    except Exception:
        sources=[]
    try:
        media=person_media(db,pid)
    except Exception:
        media=[]
    return {
        "summary":{
            "event_count":total,
            "supported_events":supported,
            "unsupported_events":max(0,total-supported),
            "support_percent":round((supported/total)*100) if total else None,
            "source_count":len(sources),"media_count":len(media),
        },
        "events":rows,
    }

def person_workspace(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    if not p:return None
    con=relationship_connections(db,pid)
    return {
        "person":dict(p),"life":life_dates(db,pid),
        "events":_dicts(person_events(db,pid)),
        "notes":_dicts(person_notes(db,pid)),
        "sources":_dicts(person_sources(db,pid)),
        "media":_dicts(person_media(db,pid)),
        "connections":{
            "parents":_dicts(con["parents"]),"spouses":_dicts(con["spouses"]),
            "children":_dicts(con["children"]),"siblings":_dicts(con["siblings"]),
        },
        "confidence":person_confidence(db,pid)
    }

def family_choices_for_person(db,pid):
    out=[]
    for f in spouse_families(db,pid):
        h,w=family_partners(db,f["id"])
        out.append({"id":f["id"],
                    "husband":h["display_name"] if h else None,
                    "wife":w["display_name"] if w else None,
                    "marriage_date":f["marriage_date"],"marriage_place":f["marriage_place"]})
    return out

def family_workspace(db,fid):
    f=db.execute("SELECT * FROM families WHERE id=?",(fid,)).fetchone()
    if not f:return None
    h,w=family_partners(db,fid);o=family_overview(db,fid)
    return {
        "family":dict(f),
        "husband":dict(h) if h else None,
        "wife":dict(w) if w else None,
        "children":_dicts(children(db,fid)),
        "overview":{"children_count":o["children_count"],"known_descendants":o["known_descendants"],
                    "media_count":o["media_count"],"source_count":o["source_count"],
                    "wedding_photo_count":len(o["wedding_photos"]),
                    "marriage_document_count":len(o["marriage_documents"])}
    }
