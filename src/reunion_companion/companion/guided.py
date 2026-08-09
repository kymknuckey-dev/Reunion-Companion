from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

STOP = {
    "a","an","and","are","as","at","be","by","did","do","does","for","from","has",
    "have","how","i","in","is","it","me","of","on","or","our","show","that","the",
    "their","there","these","this","to","us","was","we","what","when","where",
    "which","who","why","with","family","person","people","records","record"
}

def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def _tokens(s):
    return [x for x in _norm(s).split() if x and x not in STOP]

def _excerpt(text, term=None, width=260):
    text = " ".join((text or "").split())
    if not text:
        return ""
    if term:
        low=text.lower(); pos=low.find(term.lower())
        if pos >= 0:
            start=max(0,pos-width//3); end=min(len(text),start+width)
            s=text[start:end]
            if start: s="…"+s
            if end<len(text): s+="…"
            return s
    return text if len(text)<=width else text[:width-1]+"…"

def _person_row(db,pid):
    return db.execute("""SELECT p.*,
        MAX(CASE WHEN e.event_type='Birth' THEN e.date_text END) birth,
        MAX(CASE WHEN e.event_type='Death' THEN e.date_text END) death
        FROM people p LEFT JOIN events e ON e.person_id=p.id
        WHERE p.id=? GROUP BY p.id""",(pid,)).fetchone()

def person_candidates_from_question(db, question, limit=8):
    """
    Rank person names mentioned inside an ordinary question.
    Exact full-name substring wins; otherwise score overlapping meaningful name tokens.
    """
    qn=_norm(question); qt=set(_tokens(question))
    scored=[]
    for p in db.execute("SELECT id,display_name,gedcom_xref FROM people"):
        nn=_norm(p["display_name"])
        nt=[x for x in nn.split() if x]
        if not nt:
            continue
        exact = bool(nn and nn in qn)
        overlap=len(set(nt)&qt)
        # A useful partial name normally needs two components, except a unique one-token name.
        if not exact and overlap < min(2, len(set(nt))):
            continue
        ratio=overlap/max(1,len(set(nt)))
        score=(1000 if exact else 0) + overlap*20 + ratio*10
        scored.append((score,p["id"]))
    scored.sort(reverse=True)
    return [pid for _,pid in scored[:limit]]

def _source_rows_for(db, scope, object_id):
    if scope=="person":
        return db.execute("""SELECT DISTINCT s.* FROM sources s
            JOIN person_sources x ON x.source_id=s.id WHERE x.person_id=? ORDER BY s.id""",(object_id,)).fetchall()
    if scope=="event":
        return db.execute("""SELECT DISTINCT s.* FROM sources s
            JOIN event_sources x ON x.source_id=s.id WHERE x.event_id=? ORDER BY s.id""",(object_id,)).fetchall()
    if scope=="note":
        return db.execute("""SELECT DISTINCT s.* FROM sources s
            JOIN note_sources x ON x.source_id=s.id WHERE x.note_id=? ORDER BY s.id""",(object_id,)).fetchall()
    if scope=="family":
        return db.execute("""SELECT DISTINCT s.* FROM sources s
            JOIN family_sources x ON x.source_id=s.id WHERE x.family_id=? ORDER BY s.id""",(object_id,)).fetchall()
    return []

def evidence_items(db, pid, term=None, limit=80):
    """
    Build a readable evidence bundle for a person.  Evidence is kept in its GEDCOM
    context instead of flattening events, notes, media and sources into one blob.
    """
    like=f"%{term}%" if term else None
    out=[]

    # Person-level source citations.
    for s in _source_rows_for(db,"person",pid):
        blob=" ".join(x for x in (s["display_text"],s["source_type"],s["text"],s["title"]) if x)
        if not term or term.lower() in blob.lower():
            out.append(dict(kind="SOURCE", label=s["gedcom_xref"], text=s["display_text"] or s["text"] or s["title"] or "",
                            sources=[], scope="person"))

    sql="SELECT * FROM events WHERE person_id=?"
    args=[pid]
    if term:
        sql += " AND (COALESCE(event_type,'') LIKE ? OR COALESCE(date_text,'') LIKE ? OR COALESCE(place_text,'') LIKE ? OR COALESCE(value_text,'') LIKE ? OR COALESCE(note_text,'') LIKE ?)"
        args += [like]*5
    sql += " ORDER BY id"
    for e in db.execute(sql,args):
        bits=[e["event_type"]]
        bits += [x for x in (e["date_text"],e["place_text"],e["value_text"],e["note_text"]) if x and x!="Y"]
        out.append(dict(kind="EVENT",label=e["event_type"],text=" — ".join(bits),
                        sources=_source_rows_for(db,"event",e["id"]),scope="event"))

    sql="SELECT * FROM notes WHERE person_id=?"
    args=[pid]
    if term:
        sql += " AND (COALESCE(note_type,'') LIKE ? OR COALESCE(gedcom_tag,'') LIKE ? OR COALESCE(text,'') LIKE ?)"
        args += [like]*3
    sql += " ORDER BY id"
    for n in db.execute(sql,args):
        out.append(dict(kind="NOTE",label=n["note_type"] or n["gedcom_tag"] or "Note",text=n["text"],
                        sources=_source_rows_for(db,"note",n["id"]),scope="note"))

    # Media from person, event and families in which the person participates.
    media=db.execute("""
        SELECT DISTINCT m.*,'person' attach_scope FROM media m
        JOIN person_media pm ON pm.media_id=m.id WHERE pm.person_id=?
        UNION
        SELECT DISTINCT m.*,'event' attach_scope FROM media m
        JOIN event_media em ON em.media_id=m.id JOIN events e ON e.id=em.event_id WHERE e.person_id=?
        UNION
        SELECT DISTINCT m.*,'family' attach_scope FROM media m
        JOIN family_media fm ON fm.media_id=m.id
        JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?
        ORDER BY id
    """,(pid,pid,pid)).fetchall()
    for m in media:
        blob=" ".join(x for x in (m["title"],m["file_path"],m["media_type"],m["attachment_label"]) if x)
        if not term or term.lower() in blob.lower():
            out.append(dict(kind="MEDIA",label=m["title"] or Path(m["file_path"]).name,
                            text=m["file_path"],sources=[],scope=m["attach_scope"]))
    return out[:limit]

def format_case(db,pid,term=None):
    p=_person_row(db,pid); name=p["display_name"]
    title=f"Evidence Case — {name}" + (f" — {term}" if term else "")
    L=[title,"="*len(title)]
    items=evidence_items(db,pid,term)
    if not items:
        return "\n".join(L+["","No matching evidence was found in the imported GEDCOM."])
    grouped=defaultdict(list)
    for x in items: grouped[x["kind"]].append(x)
    for kind in ("EVENT","NOTE","MEDIA","SOURCE"):
        if not grouped[kind]: continue
        L += ["",kind.title()+"s","-"*(len(kind)+1)]
        for x in grouped[kind]:
            L.append(f"  • {x['label']}: {_excerpt(x['text'],term)}")
            for s in x["sources"]:
                desc=s["display_text"] or s["text"] or s["title"] or "(undescribed source)"
                L.append(f"      ↳ {s['gedcom_xref']} — {desc}")
    L += ["","Interpretation","--------------",
          "  This is the evidence present in the imported Reunion GEDCOM. It does not by itself prove that every statement is correct."]
    return "\n".join(L)

def topic_people(db,term,limit=100):
    """
    Return distinct people for whom the term appears in an event, note, media or
    a source cited by that person/event/note/family.
    """
    q=f"%{term}%"
    rows=db.execute("""
      WITH hits(person_id,kind,detail) AS (
        SELECT e.person_id,'event',e.event_type||' — '||COALESCE(e.place_text,e.value_text,e.note_text,'')
          FROM events e
          WHERE COALESCE(e.event_type,'') LIKE :q OR COALESCE(e.place_text,'') LIKE :q OR COALESCE(e.value_text,'') LIKE :q OR COALESCE(e.note_text,'') LIKE :q
        UNION ALL
        SELECT n.person_id,'note',n.note_type||' — '||substr(n.text,1,180)
          FROM notes n WHERE COALESCE(n.note_type,'') LIKE :q OR COALESCE(n.text,'') LIKE :q
        UNION ALL
        SELECT pm.person_id,'media',COALESCE(m.title,m.file_path)
          FROM person_media pm JOIN media m ON m.id=pm.media_id
          WHERE COALESCE(m.title,'') LIKE :q OR COALESCE(m.file_path,'') LIKE :q
        UNION ALL
        SELECT e.person_id,'media',COALESCE(m.title,m.file_path)
          FROM event_media em JOIN events e ON e.id=em.event_id JOIN media m ON m.id=em.media_id
          WHERE COALESCE(m.title,'') LIKE :q OR COALESCE(m.file_path,'') LIKE :q
        UNION ALL
        SELECT ps.person_id,'source',COALESCE(s.display_text,s.text,s.title,'')
          FROM person_sources ps JOIN sources s ON s.id=ps.source_id
          WHERE COALESCE(s.display_text,'') LIKE :q OR COALESCE(s.text,'') LIKE :q OR COALESCE(s.source_type,'') LIKE :q
        UNION ALL
        SELECT e.person_id,'source',COALESCE(s.display_text,s.text,s.title,'')
          FROM event_sources es JOIN events e ON e.id=es.event_id JOIN sources s ON s.id=es.source_id
          WHERE COALESCE(s.display_text,'') LIKE :q OR COALESCE(s.text,'') LIKE :q OR COALESCE(s.source_type,'') LIKE :q
        UNION ALL
        SELECT n.person_id,'source',COALESCE(s.display_text,s.text,s.title,'')
          FROM note_sources ns JOIN notes n ON n.id=ns.note_id JOIN sources s ON s.id=ns.source_id
          WHERE COALESCE(s.display_text,'') LIKE :q OR COALESCE(s.text,'') LIKE :q OR COALESCE(s.source_type,'') LIKE :q
        UNION ALL
        SELECT fmemb.person_id,'source',COALESCE(s.display_text,s.text,s.title,'')
          FROM family_sources fs JOIN family_members fmemb ON fmemb.family_id=fs.family_id JOIN sources s ON s.id=fs.source_id
          WHERE COALESCE(s.display_text,'') LIKE :q OR COALESCE(s.text,'') LIKE :q OR COALESCE(s.source_type,'') LIKE :q
      )
      SELECT p.id,p.display_name,
             MAX(CASE WHEN e.event_type='Birth' THEN e.date_text END) birth,
             MAX(CASE WHEN e.event_type='Death' THEN e.date_text END) death,
             COUNT(*) hit_count,
             GROUP_CONCAT(DISTINCT hits.kind) hit_kinds,
             MIN(hits.detail) sample
      FROM hits JOIN people p ON p.id=hits.person_id
      LEFT JOIN events e ON e.person_id=p.id
      GROUP BY p.id,p.display_name
      ORDER BY hit_count DESC,p.display_name
      LIMIT :lim
    """,{"q":q,"lim":limit}).fetchall()
    return rows

def format_topic(db,term,limit=100):
    rows=topic_people(db,term,limit)
    L=[f"Topic Explorer — {term}","="*(17+len(term))]
    if not rows:return "\n".join(L+["  (no people matched this topic)"])
    L += ["","People","------"]
    for r in rows:
        dates="; ".join(x for x in (("b. "+r["birth"]) if r["birth"] else None,("d. "+r["death"]) if r["death"] else None) if x)
        suffix=f" ({dates})" if dates else ""
        L.append(f"  {r['id']}: {r['display_name']}{suffix} — {r['hit_count']} hit(s): {r['hit_kinds']}")
        if r["sample"]: L.append("      "+_excerpt(r["sample"],term,180))
    return "\n".join(L)

def format_military(db,term=None,limit=100):
    sql="""SELECT p.id,p.display_name,n.note_type,n.text
           FROM notes n JOIN people p ON p.id=n.person_id
           WHERE (lower(COALESCE(n.note_type,'')) LIKE '%military%'
                  OR lower(COALESCE(n.gedcom_tag,'')) IN ('mili','mils','_mils'))"""
    args=[]
    if term:
        sql += " AND lower(n.text) LIKE ?";args.append("%"+term.lower()+"%")
    sql += " ORDER BY p.display_name LIMIT ?";args.append(limit)
    rows=db.execute(sql,args).fetchall()
    title="Military Service Explorer"+(f" — {term}" if term else "")
    L=[title,"="*len(title)]
    for r in rows:
        L.append(f"  {r['id']}: {r['display_name']} — {_excerpt(r['text'],term,190)}")
    if len(L)==2:L.append("  (no matching military-service notes)")
    return "\n".join(L)

def format_documents(db,term=None,limit=100):
    q=f"%{term}%" if term else "%"
    rows=db.execute("""SELECT DISTINCT m.id,m.title,m.file_path,m.media_type,m.exists_on_disk,
                       COALESCE(p1.id,p2.id,p3.id) person_id,COALESCE(p1.display_name,p2.display_name,p3.display_name) display_name
                       FROM media m
                       LEFT JOIN person_media pm ON pm.media_id=m.id LEFT JOIN people p1 ON p1.id=pm.person_id
                       LEFT JOIN event_media em ON em.media_id=m.id LEFT JOIN events e ON e.id=em.event_id LEFT JOIN people p2 ON p2.id=e.person_id
                       LEFT JOIN family_media fm ON fm.media_id=m.id
                       LEFT JOIN family_members fmem ON fmem.family_id=fm.family_id LEFT JOIN people p3 ON p3.id=fmem.person_id
                       WHERE COALESCE(m.title,'') LIKE ? OR COALESCE(m.file_path,'') LIKE ?
                       ORDER BY m.title LIMIT ?""",(q,q,limit)).fetchall()
    title="Document & Media Explorer"+(f" — {term}" if term else "")
    L=[title,"="*len(title)]
    for r in rows:
        owner=f" — {r['display_name']} [ID {r['person_id']}]" if r["display_name"] else ""
        status="✓" if r["exists_on_disk"] else "MISSING"
        L.append(f"  {status} {r['title'] or Path(r['file_path']).name}{owner}")
    if len(L)==2:L.append("  (no matching media)")
    return "\n".join(L)

def format_guided(db,pid):
    p=_person_row(db,pid); name=p["display_name"]
    ev=db.execute("SELECT COUNT(*) FROM events WHERE person_id=?",(pid,)).fetchone()[0]
    notes=db.execute("SELECT COUNT(*) FROM notes WHERE person_id=?",(pid,)).fetchone()[0]
    media=len(evidence_items(db,pid))
    src=db.execute("""SELECT COUNT(DISTINCT source_id) FROM (
        SELECT source_id FROM person_sources WHERE person_id=?
        UNION SELECT es.source_id FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?
        UNION SELECT ns.source_id FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
    )""",(pid,pid,pid)).fetchone()[0]
    title=f"Guided Discovery — {name}"
    return "\n".join([
        title,"="*len(title),"",
        f"Person ID: {pid}"+(f" — born {p['birth']}" if p["birth"] else ""),
        f"Events: {ev}   Notes: {notes}   Sources: {src}","",
        "Good next questions",
        "-------------------",
        f'  ask "What do we know about {name}?"',
        f'  ask "What evidence do we have for {name}?"',
        f'  ask "Why do we think {name} <topic>?"',
        f'  case {pid} [TOPIC]',
        f'  sources {pid}',
        f'  connections {pid}',
        f'  ancestors {pid} 4',
        f'  descendants {pid} 4',
    ])

def _extract_topic(question, person_name=None):
    q=question
    if person_name:
        # Remove individual name tokens so the remaining terms are more likely to be the subject.
        for t in person_name.split():
            q=re.sub(rf"\b{re.escape(t)}\b"," ",q,flags=re.I)
    toks=_tokens(q)
    # remove generic intent words not useful as search terms
    generic={"know","think","evidence","support","conclusion","about","associated","mention","mentions","known"}
    toks=[t for t in toks if t not in generic]
    return " ".join(toks[:6]).strip()

def answer_question(db,question):
    """
    Foundation 6 entity-first router.

    Resolve the subject before deciding whether the user wants an overview,
    connected records, evidence, relationships, a topic search or research
    quality analysis.
    """
    from .entities import resolve_entities
    from .intelligence import (
        records_for_person,format_assess,format_issues,format_unsupported,format_conflicts
    )
    q=question.strip()
    ql=q.lower()
    entities=resolve_entities(db,q)
    persons=[e for e in entities if e.kind=="person"]

    # Foundation 7 relationship reasoning: two resolved people + connection language.
    if len(persons)>=2 and any(x in ql for x in ("how is","how are","related to","relationship between","connected to","connection between")):
        from .relationship_engine import format_relationship
        return "Intent: relationship path\nIntent: relationship intelligence\n\n"+format_relationship(db,persons[0].object_id,persons[1].object_id)

    # Foundation 7 knowledge-graph questions.
    if persons and any(x in ql for x in ("knowledge graph","relationship graph","graph around","connections around")):
        from .knowledge_graph import format_evidence_graph
        return "Intent: knowledge graph\n\n"+format_evidence_graph(db,persons[0].object_id)

    # Person-connected records must beat the older generic 'records mention' topic route.
    if persons and any(x in ql for x in (
        "what records","which records","records mention","records connected",
        "show records","what documents","which documents"
    )):
        return "Intent: person-connected records\n\n"+records_for_person(db,persons[0].object_id)

    # Research intelligence intents.
    if persons and any(x in ql for x in ("weak evidence","evidence quality","assess","how well sourced","well sourced")):
        return "Intent: research intelligence\n\n"+format_assess(db,persons[0].object_id)
    if persons and any(x in ql for x in ("research issues","what issues","problems with","needs research")):
        return "Intent: research issues\n\n"+format_issues(db,persons[0].object_id)
    if persons and any(x in ql for x in ("unsupported","no evidence","without evidence","uncited")):
        return "Intent: unsupported evidence\n\n"+format_unsupported(db,persons[0].object_id)
    if persons and any(x in ql for x in ("conflict","conflicting","contradict","contradiction")):
        return "Intent: conflict check\n\n"+format_conflicts(db,persons[0].object_id)

    # Foundation 9 integrated research intents.
    if persons and any(x in ql for x in ("research profile","how complete","research status")):
        from .profile_builder import format_profile
        return "Intent: research profile\n\n"+format_profile(db,persons[0].object_id)
    if persons and any(x in ql for x in ("how confident","confidence in","confidence for")):
        from .confidence_engine import format_confidence
        return "Intent: research confidence\n\n"+format_confidence(db,persons[0].object_id)
    if persons and any(x in ql for x in ("evidence summary","summarise evidence","summarize evidence")):
        from .evidence_summary import format_evidence_summary
        return "Intent: evidence summary\n\n"+format_evidence_summary(db,persons[0].object_id)
    if persons and any(x in ql for x in ("research timeline","dated notes","timeline including notes")):
        from .research_timeline import format_research_timeline
        return "Intent: integrated research timeline\n\n"+format_research_timeline(db,persons[0].object_id)

    # Foundation 8 genealogical intelligence intents.
    if persons and any(x in ql for x in ("life story","story of","biography of")):
        from .story_engine import format_story
        return "Intent: life story\n\n"+format_story(db,persons[0].object_id)
    if persons and any(x in ql for x in ("what should i research","research next","improve this","improve ")) :
        from .research_engine import format_improve
        return "Intent: research assistant\n\n"+format_improve(db,persons[0].object_id)
    if persons and any(x in ql for x in ("audit ","check consistency","consistency check")):
        from .audit_engine import format_audit
        return "Intent: genealogy audit\n\n"+format_audit(db,persons[0].object_id)
    if persons and any(x in ql for x in ("knowledge card","dashboard")):
        from .knowledge_card import format_card
        return "Intent: knowledge card\n\n"+format_card(db,persons[0].object_id)
    if persons and any(x in ql for x in ("evidence for","evidence profile","what supports")):
        from .evidence_engine import format_evidence_intelligence
        return "Intent: evidence intelligence\n\n"+format_evidence_intelligence(db,persons[0].object_id)

    # Existing Foundation 5 person overview.
    if persons and any(x in ql for x in ("what do we know","tell me about","everything about","about ")):
        from .discovery_report import format_tell
        return "Intent: person overview\n\n"+format_tell(db,persons[0].object_id)

    # Why/evidence.
    if persons and any(x in ql for x in ("why ","evidence","support","prove","basis")):
        p=_person_row(db,persons[0].object_id)
        term=_extract_topic(q,p["display_name"])
        return "Intent: evidence question\n\n"+format_case(db,persons[0].object_id,term or None)

    # Relationships.
    if persons and any(x in ql for x in ("parents","children","siblings","spouse","wife","husband","related","connection")):
        from .discovery_report import format_connections
        return "Intent: relationship question\n\n"+format_connections(db,persons[0].object_id)

    # An identifier is a search term, not a person.
    identifiers=[e for e in entities if e.kind=="identifier"]
    if identifiers:
        from .discovery_report import format_find
        return "Intent: identifier discovery\n\n"+format_find(db,identifiers[0].value)

    # Explicit military-service discovery.
    if "military" in ql or "served" in ql or "service" in ql:
        term=_extract_topic(q)
        term=" ".join(t for t in term.split() if t not in {"military","service","served"})
        return "Intent: military-service discovery\n\n"+format_military(db,term or None)

    # Documents/certificates/photos without a person.
    if any(x in ql for x in ("document","certificate","photo","photograph","media")):
        term=_extract_topic(q)
        term=" ".join(t for t in term.split() if t not in {"document","documents","certificate","certificates","photo","photograph","media"})
        return "Intent: document/media discovery\n\n"+format_documents(db,term or None)

    # Person resolved but no explicit action -> guided landing page.
    if persons:
        return "Intent: guided person discovery\n\n"+format_guided(db,persons[0].object_id)

    # Topic discovery.
    topics=[e for e in entities if e.kind=="topic"]
    term=(topics[0].value if topics else _extract_topic(q))
    if term:
        return "Intent: topic discovery\n\n"+format_topic(db,term)

    return """I couldn't determine the subject of that question from the imported data.

Try:
  ask "What records mention Kym Wayne Knuckey?"
  ask "What do we know about Lionel George Waight?"
  ask "Why do we think Lionel George Waight was adopted?"
  ask "Does Lionel George Waight have weak evidence?"
  ask "Who served in Borneo?"
"""
