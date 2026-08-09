from __future__ import annotations
from collections import defaultdict

CORE={"Birth","Death","Burial","Cremation","Marriage"}

def _source_label(s):
    return s["display_text"] or s["text"] or s["title"] or s["gedcom_xref"] or "(undescribed source)"

def event_evidence(db,event_id):
    e=db.execute("SELECT * FROM events WHERE id=?",(event_id,)).fetchone()
    sources=db.execute("""SELECT DISTINCT s.* FROM sources s
        JOIN event_sources es ON es.source_id=s.id WHERE es.event_id=? ORDER BY s.id""",(event_id,)).fetchall()
    media=db.execute("""SELECT DISTINCT m.* FROM media m
        JOIN event_media em ON em.media_id=m.id WHERE em.event_id=? ORDER BY m.id""",(event_id,)).fetchall()
    score=min(100,(45 if sources else 0)+(35 if media else 0)+(10 if e and e["date_text"] else 0)+(10 if e and e["place_text"] else 0))
    return {"event":e,"sources":sources,"media":media,"score":score}

def person_evidence_profile(db,pid):
    events=db.execute("SELECT * FROM events WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    rows=[]
    for e in events:
        if e["event_type"]=="Changed":continue
        x=event_evidence(db,e["id"])
        if x["sources"] and x["media"]:level="strong"
        elif x["sources"] or x["media"]:level="supported"
        else:level="unlinked"
        rows.append((e,x,level))
    return rows

def overall_evidence_score(db,pid):
    rows=person_evidence_profile(db,pid)
    core=[x for x in rows if x[0]["event_type"] in CORE]
    use=core or rows
    if not use:return 0
    return round(sum(x[1]["score"] for x in use)/len(use))

def format_evidence_intelligence(db,pid):
    p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    title=f"Evidence Intelligence — {p['display_name']}";L=[title,"="*len(title),""]
    rows=person_evidence_profile(db,pid)
    for e,x,level in rows:
        bits=[e["event_type"]]+[v for v in (e["date_text"],e["place_text"],e["value_text"]) if v and v!="Y"]
        L.append(" — ".join(bits))
        L.append(f"  Evidence: {level.title()} · score {x['score']}%")
        if x["sources"]:
            L.append("  Sources:")
            for s in x["sources"]:L.append(f"    ✓ {_source_label(s)}")
        if x["media"]:
            L.append("  Documents / media:")
            for m in x["media"]:L.append(f"    ✓ {m['title'] or m['file_path']}")
        if not x["sources"] and not x["media"]:
            L.append("    ⚠ No linked source or document visible in the imported GEDCOM.")
        L.append("")
    L.append(f"Overall core-event evidence score: {overall_evidence_score(db,pid)}%")
    L.append("This score describes visible linkage in the Companion, not historical truth.")
    return "\n".join(L)
