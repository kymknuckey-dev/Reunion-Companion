from __future__ import annotations
import re
from .timeline_engine import intelligent_timeline

def clean_text(s):
    return re.sub(r"\s+"," ",s or "").strip()

def preserve_note_text(s):
    return (s or "").replace("\r\n","\n").replace("\r","\n").strip()

def story_sections(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    events=db.execute("SELECT * FROM events WHERE person_id=? AND event_type<>'Changed' ORDER BY id",(pid,)).fetchall()
    notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    sections=[]

    # Lead with factual event summary.
    lead=[]
    for typ in ("Birth","Death"):
        for e in events:
            if e["event_type"]==typ:
                bits=[]
                if e["date_text"]:bits.append(e["date_text"])
                if e["place_text"]:bits.append(e["place_text"])
                if typ=="Birth":
                    lead.append(f"{p['display_name']} was born"+(" on "+bits[0] if bits else "")+
                                ((" at " if len(bits)>1 else " in ")+bits[-1] if e["place_text"] else "")+".")
                else:
                    lead.append(f"{p['display_name']} died"+(" on "+bits[0] if bits else "")+
                                ((" at " if len(bits)>1 else " in ")+bits[-1] if e["place_text"] else "")+".")
                break
    if lead:sections.append(("Life Summary"," ".join(lead)))

    # Deterministic event chapters.
    for chapter,rows in intelligent_timeline(db,pid):
        if chapter in ("Early Life","Later Life & Memorial"):continue
        sentences=[]
        for e in rows:
            if e["event_type"] in ("Occupation","Education","Religion"):
                if e["value_text"]:sentences.append(f"{e['event_type']}: {clean_text(e['value_text'])}.")
            elif e["date_text"] or e["place_text"]:
                b=[e["event_type"]]+[x for x in (e["date_text"],e["place_text"],e["value_text"]) if x and x!="Y"]
                sentences.append(" — ".join(clean_text(x) for x in b)+".")
        if sentences:sections.append((chapter,("\n" if chapter=="Education & Working Life" else " ").join(sentences)))

    # Typed notes are retained as authored source material, not rewritten.
    for n in notes:
        txt=preserve_note_text(n["text"])
        if not txt:continue
        label=n["note_type"] or n["gedcom_tag"] or "Note"
        sections.append((label,txt))
    return sections

def format_story(db,pid):
    p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    title=f"Life Story — {p['display_name']}";L=[title,"="*len(title)]
    sections=story_sections(db,pid)
    if not sections:return "\n".join(L+["","No narrative material found."])
    for h,txt in sections:
        L += ["",h,"-"*len(h),txt]
    L += ["","Provenance","----------",
          "This story is assembled deterministically from imported Reunion events and notes. Typed note text is preserved rather than invented or silently corrected."]
    return "\n".join(L)
