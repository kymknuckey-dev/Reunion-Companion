from __future__ import annotations
from .media_health import media_health_data

def _count(db,sql,args=()):
    return db.execute(sql,args).fetchone()[0]

def research_gap_summary(db):
    media=media_health_data(db)
    return {
        "people":_count(db,"SELECT COUNT(*) FROM people"),
        "missing_birth":_count(db,"SELECT COUNT(*) FROM people p WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.person_id=p.id AND e.event_type='Birth')"),
        "missing_death":_count(db,"SELECT COUNT(*) FROM people p WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.person_id=p.id AND e.event_type='Death')"),
        "without_sources":_count(db,"""SELECT COUNT(*) FROM people p WHERE NOT EXISTS (SELECT 1 FROM person_sources ps WHERE ps.person_id=p.id) AND NOT EXISTS (SELECT 1 FROM events e JOIN event_sources es ON es.event_id=e.id WHERE e.person_id=p.id) AND NOT EXISTS (SELECT 1 FROM notes n JOIN note_sources ns ON ns.note_id=n.id WHERE n.person_id=p.id) AND NOT EXISTS (SELECT 1 FROM family_members fm JOIN family_sources fs ON fs.family_id=fm.family_id WHERE fm.person_id=p.id)"""),
        "events_without_evidence":_count(db,"SELECT COUNT(*) FROM events e WHERE e.event_type<>'Changed' AND NOT EXISTS (SELECT 1 FROM event_sources es WHERE es.event_id=e.id) AND NOT EXISTS (SELECT 1 FROM event_media em WHERE em.event_id=e.id)"),
        "notes_without_sources":_count(db,"SELECT COUNT(*) FROM notes n WHERE NOT EXISTS (SELECT 1 FROM note_sources ns WHERE ns.note_id=n.id)"),
        "unused_sources":_count(db,"SELECT COUNT(*) FROM sources s WHERE NOT EXISTS (SELECT 1 FROM citations c WHERE c.source_id=s.id)"),
        "missing_media":len(media["missing"]),"legacy_media":len(media["legacy"]),"unknown_media":len(media["unknown"])
    }

def _sample_people(db,kind,limit=12):
    if kind=="missing_birth":
        sql="SELECT p.id,p.display_name FROM people p WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.person_id=p.id AND e.event_type='Birth') ORDER BY p.id LIMIT ?"
    elif kind=="missing_death":
        sql="SELECT p.id,p.display_name FROM people p WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.person_id=p.id AND e.event_type='Death') ORDER BY p.id LIMIT ?"
    elif kind=="without_sources":
        sql="""SELECT p.id,p.display_name FROM people p WHERE NOT EXISTS (SELECT 1 FROM person_sources ps WHERE ps.person_id=p.id) AND NOT EXISTS (SELECT 1 FROM events e JOIN event_sources es ON es.event_id=e.id WHERE e.person_id=p.id) AND NOT EXISTS (SELECT 1 FROM notes n JOIN note_sources ns ON ns.note_id=n.id WHERE n.person_id=p.id) AND NOT EXISTS (SELECT 1 FROM family_members fm JOIN family_sources fs ON fs.family_id=fm.family_id WHERE fm.person_id=p.id) ORDER BY p.id LIMIT ?"""
    else:return []
    return db.execute(sql,(limit,)).fetchall()

def format_research_gaps(db):
    d=research_gap_summary(db)
    L=["Database Research Gaps","======================","",f"People                         {d['people']}",f"People without birth event     {d['missing_birth']}",f"People without death event     {d['missing_death']}",f"People with no visible source  {d['without_sources']}",f"Events without source/media    {d['events_without_evidence']}",f"Notes without linked source    {d['notes_without_sources']}",f"Imported sources unused        {d['unused_sources']}",f"Missing media                  {d['missing_media']}",f"Legacy media                   {d['legacy_media']}",f"Unknown media formats          {d['unknown_media']}","","Important","---------","A missing death event is not automatically a research problem: living people and intentionally incomplete branches are included. These counts are discovery prompts, not errors."]
    for key,label in (("missing_birth","Sample people without Birth"),("missing_death","Sample people without Death"),("without_sources","Sample people without visible source support")):
        rows=_sample_people(db,key)
        if rows:
            L += ["",label,"-"*len(label)]
            for r in rows:L.append(f"  {r['id']}: {r['display_name']}")
    return "\n".join(L)
