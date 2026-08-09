from __future__ import annotations
from .discovery import relationship_connections
from .evidence_engine import overall_evidence_score
from .research_engine import research_opportunities

def knowledge_card(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    events=db.execute("SELECT COUNT(*) FROM events WHERE person_id=? AND event_type<>'Changed'",(pid,)).fetchone()[0]
    notes=db.execute("SELECT COUNT(*) FROM notes WHERE person_id=?",(pid,)).fetchone()[0]
    media=db.execute("""SELECT COUNT(DISTINCT id) FROM media WHERE id IN (
        SELECT media_id FROM person_media WHERE person_id=?
        UNION SELECT em.media_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE e.person_id=?
        UNION SELECT fm.media_id FROM family_media fm JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?
    )""",(pid,pid,pid)).fetchone()[0]
    sources=db.execute("""SELECT COUNT(DISTINCT id) FROM sources WHERE id IN (
        SELECT source_id FROM person_sources WHERE person_id=?
        UNION SELECT es.source_id FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?
        UNION SELECT ns.source_id FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
        UNION SELECT fs.source_id FROM family_sources fs JOIN family_members fm ON fm.family_id=fs.family_id WHERE fm.person_id=?
    )""",(pid,pid,pid,pid)).fetchone()[0]
    c=relationship_connections(db,pid)
    military=db.execute("SELECT COUNT(*) FROM notes WHERE person_id=? AND (LOWER(note_type) LIKE '%military%' OR gedcom_tag IN ('MILI','_MILS','MILS'))",(pid,)).fetchone()[0]>0
    occupation=db.execute("SELECT value_text FROM events WHERE person_id=? AND event_type='Occupation' AND value_text IS NOT NULL ORDER BY id LIMIT 1",(pid,)).fetchone()
    return dict(person=p,events=events,notes=notes,media=media,sources=sources,
                evidence=overall_evidence_score(db,pid),research_items=len(research_opportunities(db,pid)),
                connections=sum(len(c[k]) for k in ("parents","spouses","children","siblings")),
                military=military,occupation=occupation["value_text"] if occupation else None)

def format_card(db,pid):
    d=knowledge_card(db,pid);p=d["person"];name=p["display_name"]
    title=f"Knowledge Card — {name}";L=[title,"="*len(title),
        f"GEDCOM: {p['gedcom_xref']}  ·  Companion ID: {p['id']}",
        "",
        f"Evidence linkage     {d['evidence']}%",
        f"Research items      {d['research_items']}",
        f"Events              {d['events']}",
        f"Notes               {d['notes']}",
        f"Sources             {d['sources']}",
        f"Media               {d['media']}",
        f"Family connections  {d['connections']}",
        f"Military            {'Yes' if d['military'] else 'No'}"]
    if d["occupation"]:L.append(f"Occupation          {d['occupation']}")
    return "\n".join(L)
