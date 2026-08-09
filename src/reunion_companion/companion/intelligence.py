from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import re

def _src_count_for_event(db,eid):
    return db.execute("SELECT COUNT(DISTINCT source_id) FROM event_sources WHERE event_id=?",(eid,)).fetchone()[0]

def _src_count_for_note(db,nid):
    return db.execute("SELECT COUNT(DISTINCT source_id) FROM note_sources WHERE note_id=?",(nid,)).fetchone()[0]

def _media_count_for_event(db,eid):
    return db.execute("SELECT COUNT(DISTINCT media_id) FROM event_media WHERE event_id=?",(eid,)).fetchone()[0]

def _person_name(db,pid):
    r=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    return r["display_name"] if r else f"Person {pid}"

def person_quality(db,pid):
    events=db.execute("SELECT * FROM events WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()

    evidence=[]
    unsupported=[]
    conflicts=[]
    cautions=[]
    strengths=[]

    # Event evidence quality.
    by_type=defaultdict(list)
    for e in events:
        by_type[e["event_type"]].append(e)
        sc=_src_count_for_event(db,e["id"])
        mc=_media_count_for_event(db,e["id"])
        if sc or mc:
            evidence.append((e["event_type"],e["date_text"],sc,mc))
        elif e["event_type"] not in ("Changed",):
            unsupported.append(("event",e["event_type"],e["date_text"] or e["value_text"] or e["place_text"] or ""))

    # Detect multiple differing values for core events. Multiple occupations etc are normal,
    # so conflicts are restricted to event types expected to be singular-ish.
    for typ in ("Birth","Death","Burial","Cremation"):
        vals=[]
        for e in by_type.get(typ,[]):
            key=(e["date_text"] or "",e["place_text"] or "")
            if key != ("","") and key not in vals:
                vals.append(key)
        if len(vals)>1:
            conflicts.append((typ,vals))

    # Notes can carry assertions; source-linked ones are stronger, unlinked Research/Military
    # notes deserve review rather than being called false.
    for n in notes:
        sc=_src_count_for_note(db,n["id"])
        typ=n["note_type"] or n["gedcom_tag"] or "Note"
        text=" ".join(n["text"].split())
        if sc:
            strengths.append((typ,sc,text[:160]))
        elif typ.lower() in ("research","military service","medical"):
            cautions.append((typ,"No source citation attached",text[:180]))

    # Useful gaps - evidence oriented rather than generic.
    for typ in ("Birth","Death"):
        es=by_type.get(typ,[])
        if es and all(_src_count_for_event(db,e["id"])==0 and _media_count_for_event(db,e["id"])==0 for e in es):
            cautions.append((typ,"Recorded but has no linked source or document",""))
    if not by_type.get("Birth"):
        cautions.append(("Birth","No birth event recorded",""))
    if not by_type.get("Death"):
        cautions.append(("Death","No death event recorded",""))

    return dict(evidence=evidence,unsupported=unsupported,conflicts=conflicts,cautions=cautions,strengths=strengths)

def format_assess(db,pid):
    name=_person_name(db,pid)
    q=person_quality(db,pid)
    title=f"Research Intelligence — {name}"
    L=[title,"="*len(title)]

    L += ["","Evidence-backed events","----------------------"]
    if q["evidence"]:
        for typ,date,sc,mc in q["evidence"]:
            bits=[]
            if sc: bits.append(f"{sc} source(s)")
            if mc: bits.append(f"{mc} document/media")
            L.append(f"  ✓ {typ}" + (f" — {date}" if date else "") + " — " + ", ".join(bits))
    else:
        L.append("  (none detected)")

    L += ["","Review points","-------------"]
    if q["cautions"]:
        for typ,msg,snip in q["cautions"]:
            L.append(f"  ? {typ}: {msg}")
            if snip: L.append(f"      {snip}")
    else:
        L.append("  No obvious review points detected.")

    L += ["","Potentially unsupported event assertions","----------------------------------------"]
    rows=[x for x in q["unsupported"] if x[1] not in ("Occupation","Education","Religion")]
    if rows:
        for _,typ,val in rows[:30]:
            L.append(f"  • {typ}" + (f" — {val}" if val else "") + " — no linked source/document")
    else:
        L.append("  (none detected among the core event assertions)")

    L += ["","Conflicts","---------"]
    if q["conflicts"]:
        for typ,vals in q["conflicts"]:
            L.append(f"  ! {typ}")
            for date,place in vals:
                L.append("      "+(" — ".join(x for x in (date,place) if x) or "(blank)"))
    else:
        L.append("  No obvious conflicting core event values detected.")

    L += ["","Interpretation","--------------",
          "  These are database-quality signals, not historical verdicts. A missing citation means the Companion cannot see supporting evidence in the exported GEDCOM; it does not prove the statement is wrong."]
    return "\n".join(L)

def format_issues(db,pid):
    name=_person_name(db,pid); q=person_quality(db,pid)
    title=f"Research Issues — {name}";L=[title,"="*len(title)]
    n=0
    for typ,msg,snip in q["cautions"]:
        n+=1;L.append(f"  ? {typ}: {msg}")
        if snip:L.append("      "+snip)
    for typ,vals in q["conflicts"]:
        n+=1;L.append(f"  ! conflicting {typ}: "+ " | ".join(" / ".join(x for x in v if x) for v in vals))
    if not n:L.append("  No obvious issues detected.")
    return "\n".join(L)

def format_unsupported(db,pid):
    name=_person_name(db,pid); q=person_quality(db,pid)
    title=f"Unsupported / Unlinked Evidence — {name}";L=[title,"="*len(title)]
    rows=[x for x in q["unsupported"] if x[1]!="Changed"]
    if not rows:
        L.append("  No unlinked event assertions detected.")
    else:
        for _,typ,val in rows:
            L.append(f"  • {typ}" + (f" — {val}" if val else ""))
    L += ["","Note: this means no linked source/document is visible in the exported GEDCOM."]
    return "\n".join(L)

def format_conflicts(db,pid):
    name=_person_name(db,pid); q=person_quality(db,pid)
    title=f"Conflict Check — {name}";L=[title,"="*len(title)]
    if not q["conflicts"]:
        L.append("  No obvious conflicts in Birth, Death, Burial or Cremation values.")
    else:
        for typ,vals in q["conflicts"]:
            L.append(f"  {typ}:")
            for date,place in vals:
                L.append("    • "+" — ".join(x for x in (date,place) if x))
    return "\n".join(L)

def records_for_person(db,pid):
    """
    Everything structurally attached to a person, not literal text mentions of their name.
    This is the semantic fix for questions such as 'what records mention Kym Wayne Knuckey?'.
    """
    name=_person_name(db,pid)
    title=f"Records Connected to — {name}"
    L=[title,"="*len(title)]

    ev=db.execute("SELECT * FROM events WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    L += ["","Events","------"]
    if ev:
        for e in ev:
            b=[e["event_type"]]+[x for x in (e["date_text"],e["place_text"],e["value_text"]) if x and x!="Y"]
            L.append("  • "+" — ".join(b))
    else:L.append("  (none)")

    notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    L += ["","Notes","-----"]
    if notes:
        for n in notes:
            t=" ".join(n["text"].split())
            L.append(f"  • {n['note_type']}: "+(t[:180]+"…" if len(t)>180 else t))
    else:L.append("  (none)")

    media=db.execute("""
      SELECT DISTINCT m.* FROM media m JOIN person_media pm ON pm.media_id=m.id WHERE pm.person_id=?
      UNION
      SELECT DISTINCT m.* FROM media m JOIN event_media em ON em.media_id=m.id JOIN events e ON e.id=em.event_id WHERE e.person_id=?
      UNION
      SELECT DISTINCT m.* FROM media m JOIN family_media fm ON fm.media_id=m.id JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?
      ORDER BY id""",(pid,pid,pid)).fetchall()
    L += ["","Documents & Media","-----------------"]
    if media:
        for m in media:
            L.append(f"  {'✓' if m['exists_on_disk'] else 'MISSING'} {m['title'] or Path(m['file_path']).name}")
    else:L.append("  (none)")

    src=db.execute("""
      SELECT DISTINCT s.gedcom_xref,s.display_text,s.text,s.title FROM sources s WHERE s.id IN (
        SELECT source_id FROM person_sources WHERE person_id=?
        UNION SELECT es.source_id FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?
        UNION SELECT ns.source_id FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
        UNION SELECT fs.source_id FROM family_sources fs JOIN family_members fm ON fm.family_id=fs.family_id WHERE fm.person_id=?
      ) ORDER BY s.id""",(pid,pid,pid,pid)).fetchall()
    L += ["","Sources","-------"]
    if src:
        for s in src:L.append(f"  • {s['gedcom_xref']} — {s['display_text'] or s['text'] or s['title'] or '(undescribed source)'}")
    else:L.append("  (none)")
    return "\n".join(L)
