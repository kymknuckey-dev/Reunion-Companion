from __future__ import annotations
from pathlib import Path
from .evidence_engine import overall_evidence_score

def _source_text(s):
    return s["display_text"] or s["text"] or s["title"] or s["gedcom_xref"] or "(undescribed source)"

def build_evidence_summary(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    sources=db.execute("""SELECT DISTINCT s.* FROM sources s WHERE s.id IN (
        SELECT source_id FROM person_sources WHERE person_id=?
        UNION SELECT es.source_id FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?
        UNION SELECT ns.source_id FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
        UNION SELECT fs.source_id FROM family_sources fs JOIN family_members fm ON fm.family_id=fs.family_id WHERE fm.person_id=?
    ) ORDER BY s.id""",(pid,pid,pid,pid)).fetchall()
    citation_count=db.execute("SELECT COUNT(*) FROM citations WHERE person_id=?",(pid,)).fetchone()[0]
    supported_events=db.execute("""SELECT COUNT(DISTINCT e.id) FROM events e
        LEFT JOIN event_sources es ON es.event_id=e.id
        LEFT JOIN event_media em ON em.event_id=e.id
        WHERE e.person_id=? AND e.event_type<>'Changed' AND (es.source_id IS NOT NULL OR em.media_id IS NOT NULL)""",(pid,)).fetchone()[0]
    total_events=db.execute("SELECT COUNT(*) FROM events WHERE person_id=? AND event_type<>'Changed'",(pid,)).fetchone()[0]
    supported_notes=db.execute("SELECT COUNT(DISTINCT n.id) FROM notes n JOIN note_sources ns ON ns.note_id=n.id WHERE n.person_id=?",(pid,)).fetchone()[0]
    total_notes=db.execute("SELECT COUNT(*) FROM notes WHERE person_id=?",(pid,)).fetchone()[0]
    documents=db.execute("""SELECT DISTINCT m.* FROM media m WHERE m.id IN (
        SELECT media_id FROM person_media WHERE person_id=?
        UNION SELECT em.media_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE e.person_id=?
        UNION SELECT fm.media_id FROM family_media fm JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?
    ) ORDER BY m.id""",(pid,pid,pid)).fetchall()
    return {"person":p,"sources":sources,"citation_count":citation_count,"supported_events":supported_events,"total_events":total_events,"supported_notes":supported_notes,"total_notes":total_notes,"documents":documents,"score":overall_evidence_score(db,pid)}

def format_evidence_summary(db,pid):
    d=build_evidence_summary(db,pid)
    title=f"Evidence Summary — {d['person']['display_name']}"
    L=[title,"="*len(title),"",f"Visible evidence score       {d['score']}%",f"Sources                      {len(d['sources'])}",f"Citation occurrences         {d['citation_count']}",f"Supported events             {d['supported_events']} / {d['total_events']}",f"Supported notes              {d['supported_notes']} / {d['total_notes']}",f"Documents & media            {len(d['documents'])}",""]
    if d["sources"]:
        L += ["Sources","-------"]
        for s in d["sources"]: L.append(f"  {s['gedcom_xref']} — {_source_text(s)}")
        L.append("")
    if d["documents"]:
        L += ["Documents & Media","-----------------"]
        for m in d["documents"]:
            status="✓" if m["exists_on_disk"] else "MISSING"
            L.append(f"  {status} {m['title'] or Path(m['file_path']).name}")
    return "\n".join(L)
