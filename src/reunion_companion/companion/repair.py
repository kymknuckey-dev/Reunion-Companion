def _name(db,pid): return db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()["display_name"]

def format_notes(db,pid):
    rows=db.execute("""SELECT n.*,COUNT(ns.source_id) source_count FROM notes n LEFT JOIN note_sources ns ON ns.note_id=n.id
                       WHERE n.person_id=? GROUP BY n.id ORDER BY n.id""",(pid,)).fetchall()
    lines=[f"Notes — {_name(db,pid)}","="*(8+len(_name(db,pid)))]
    if not rows:return "\n".join(lines+["  (none)"])
    for n in rows:
        label=n["note_type"] or n["gedcom_tag"] or "Note"; meta=f" [{n['gedcom_tag']}]" if n["gedcom_tag"] else ""
        lines+=["",label+meta,"-"*len(label+meta),n["text"]]
        if n["source_count"]:lines.append(f"[{n['source_count']} source link{'s' if n['source_count']!=1 else ''}]")
    return "\n".join(lines)

def format_note_types(db):
    rows=db.execute("""SELECT note_type,COALESCE(gedcom_tag,'') tag,COUNT(*) notes,COUNT(DISTINCT person_id) people
                       FROM notes GROUP BY note_type,tag ORDER BY notes DESC,note_type""").fetchall()
    lines=["Note Type Inventory","==================="]
    for r in rows:lines.append(f"  {r['note_type']:<24} tag={r['tag'] or '-':<8} notes={r['notes']:<6} people={r['people']}")
    return "\n".join(lines)

def _sources(db,pid):
    return db.execute("""SELECT DISTINCT s.id,s.gedcom_xref,s.display_text,s.source_type,'person' scope FROM sources s JOIN person_sources ps ON ps.source_id=s.id WHERE ps.person_id=?
                        UNION SELECT DISTINCT s.id,s.gedcom_xref,s.display_text,s.source_type,'event' scope FROM sources s JOIN event_sources es ON es.source_id=s.id JOIN events e ON e.id=es.event_id WHERE e.person_id=?
                        UNION SELECT DISTINCT s.id,s.gedcom_xref,s.display_text,s.source_type,'note' scope FROM sources s JOIN note_sources ns ON ns.source_id=s.id JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
                        ORDER BY id,scope""",(pid,pid,pid)).fetchall()

def format_sources(db,pid):
    rows=_sources(db,pid);lines=[f"Sources — {_name(db,pid)}","="*(10+len(_name(db,pid)))]
    if not rows:return "\n".join(lines+["  (none)"])
    for r in rows:
        lines.append(f"  {r['gedcom_xref']} [{r['scope']}] — {r['display_text'] or '(no description)'}")
        if r['source_type']: lines.append(f"       Type: {r['source_type']}")
    return "\n".join(lines)

def format_evidence(db,pid):
    q=lambda sql,args=():db.execute(sql,args).fetchone()[0]
    nm=_name(db,pid);rows=db.execute("SELECT note_type,COALESCE(gedcom_tag,'') tag,COUNT(*) c FROM notes WHERE person_id=? GROUP BY note_type,tag",(pid,)).fetchall()
    lines=[f"Evidence Correlation — {nm}","="*(23+len(nm)),
           f"Events: {q('SELECT COUNT(*) FROM events WHERE person_id=?',(pid,))}",
           f"Typed notes: {q('SELECT COUNT(*) FROM notes WHERE person_id=?',(pid,))}",
           f"Sources: {len({r['id'] for r in _sources(db,pid)})}",
           f"Person source links: {q('SELECT COUNT(*) FROM person_sources WHERE person_id=?',(pid,))}",
           f"Event source links: {q('SELECT COUNT(*) FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?',(pid,))}",
           f"Note source links: {q('SELECT COUNT(*) FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?',(pid,))}",
           f"Citation occurrences: {q('SELECT COUNT(*) FROM citations WHERE person_id=?',(pid,))}",
           "","Note types","----------"]
    lines += [f"  {r['note_type']:<22} {r['tag'] or '-':<8} {r['c']}" for r in rows]
    return "\n".join(lines)

def _source_row(db,token):
    t=str(token).strip()
    if t.startswith('@S') and t.endswith('@'): x=t
    else:
        digits=''.join(ch for ch in t if ch.isdigit())
        x=f"@S{digits}@" if digits else t
    return db.execute("SELECT * FROM sources WHERE gedcom_xref=?",(x,)).fetchone()

def format_source(db,token):
    s=_source_row(db,token)
    if not s:return f"Source not found: {token}"
    lines=[f"Source {s['gedcom_xref']}","="*(7+len(s['gedcom_xref'])),s['display_text'] or '(no description)']
    if s['source_type']:lines += [f"Type: {s['source_type']}"]
    if s['title'] and s['title'] != s['display_text']:lines += [f"Title: {s['title']}"]
    counts=db.execute("""SELECT
      (SELECT COUNT(*) FROM person_sources WHERE source_id=?),
      (SELECT COUNT(*) FROM event_sources WHERE source_id=?),
      (SELECT COUNT(*) FROM note_sources WHERE source_id=?),
      (SELECT COUNT(*) FROM family_sources WHERE source_id=?),
      (SELECT COUNT(*) FROM citations WHERE source_id=?)""",(s['id'],)*5).fetchone()
    lines += ["","Usage","-----",f"Person links: {counts[0]}",f"Event links: {counts[1]}",f"Note links: {counts[2]}",f"Family links: {counts[3]}",f"Citation occurrences: {counts[4]}"]
    return "\n".join(lines)

def format_source_usage(db,token):
    s=_source_row(db,token)
    if not s:return f"Source not found: {token}"
    lines=[f"Source Usage — {s['gedcom_xref']} — {s['display_text'] or '(no description)'}","="*70]
    people=db.execute("""SELECT DISTINCT p.id,p.reunion_person_id,p.display_name FROM citations c JOIN people p ON p.id=c.person_id WHERE c.source_id=? AND c.person_id IS NOT NULL ORDER BY p.id""",(s['id'],)).fetchall()
    fams=db.execute("""SELECT DISTINCT f.id,f.gedcom_xref,f.marriage_date,f.marriage_place FROM family_sources fs JOIN families f ON f.id=fs.family_id WHERE fs.source_id=? ORDER BY f.id""",(s['id'],)).fetchall()
    lines += ["","People","------"] + ([f"  {p['reunion_person_id'] if p['reunion_person_id'] is not None else p['id']}: {p['display_name']}" for p in people] or ["  (none)"])
    lines += ["","Families","--------"] + ([f"  {f['gedcom_xref']} [ID {f['id']}]" + (f" — {f['marriage_date']}" if f['marriage_date'] else "") + (f" — {f['marriage_place']}" if f['marriage_place'] else "") for f in fams] or ["  (none)"])
    return "\n".join(lines)

def format_citation_summary(db):
    q=lambda s:db.execute(s).fetchone()[0]
    rows=db.execute("SELECT owner_scope,COUNT(*) c FROM citations GROUP BY owner_scope ORDER BY owner_scope").fetchall()
    used=q("SELECT COUNT(DISTINCT source_id) FROM citations")
    total=q("SELECT COUNT(*) FROM sources")
    lines=["Citation Summary","================",f"Sources imported: {total}",f"Sources used: {used}",f"Sources unused in imported data: {max(total-used,0)}",f"Citation occurrences: {q('SELECT COUNT(*) FROM citations')}","","By scope","--------"]
    lines += [f"  {r['owner_scope']:<10} {r['c']}" for r in rows]
    lines += ["",f"Unique person-source links: {q('SELECT COUNT(*) FROM person_sources')}",f"Unique event-source links: {q('SELECT COUNT(*) FROM event_sources')}",f"Unique note-source links: {q('SELECT COUNT(*) FROM note_sources')}",f"Unique family-source links: {q('SELECT COUNT(*) FROM family_sources')}"]
    return "\n".join(lines)

def summary(db):
    q=lambda s:db.execute(s).fetchone()[0]
    return "\n".join([f"People {q('SELECT COUNT(*) FROM people'):,}",f"Families {q('SELECT COUNT(*) FROM families'):,}",
                      f"Events {q('SELECT COUNT(*) FROM events'):,}",f"Notes {q('SELECT COUNT(*) FROM notes'):,}",
                      f"Sources {q('SELECT COUNT(*) FROM sources'):,}",f"Person source links {q('SELECT COUNT(*) FROM person_sources'):,}",
                      f"Event source links {q('SELECT COUNT(*) FROM event_sources'):,}",f"Note source links {q('SELECT COUNT(*) FROM note_sources'):,}",
                      f"Family source links {q('SELECT COUNT(*) FROM family_sources'):,}",f"Citation occurrences {q('SELECT COUNT(*) FROM citations'):,}",
                      f"Media {q('SELECT COUNT(*) FROM media'):,}",f"Missing media {q('SELECT COUNT(*) FROM media WHERE exists_on_disk=0'):,}"])
