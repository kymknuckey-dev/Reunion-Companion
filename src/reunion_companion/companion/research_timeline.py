from __future__ import annotations
import re
MONTHS={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}

def _extract_year(text):
    m=re.search(r"\b(1[5-9]\d{2}|20\d{2})\b",text or "")
    return int(m.group(1)) if m else None

def _date_key(text):
    text=(text or "").upper();m=re.search(r"\b(\d{1,2})\s+([A-Z]{3})\s+(1[5-9]\d{2}|20\d{2})\b",text)
    if m and m.group(2) in MONTHS:return (int(m.group(3)),MONTHS[m.group(2)],int(m.group(1)))
    y=_extract_year(text);return (y,99,99) if y else (9999,99,99)

def research_timeline_rows(db,pid):
    rows=[]
    for e in db.execute("SELECT * FROM events WHERE person_id=? AND event_type<>'Changed' ORDER BY id",(pid,)):
        rows.append({"kind":"EVENT","label":e["event_type"],"date":e["date_text"] or "","text":" — ".join(x for x in (e["place_text"],e["value_text"]) if x and x!="Y")})
    for n in db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)):
        text=" ".join((n["text"] or "").split());years=sorted(set(re.findall(r"\b(?:1[5-9]\d{2}|20\d{2})\b",text)));label=n["note_type"] or n["gedcom_tag"] or "Note"
        for y in years[:12]:
            i=text.find(y);excerpt=text[max(0,i-70):min(len(text),i+150)].strip();rows.append({"kind":"NOTE","label":label,"date":y,"text":excerpt})
    for m in db.execute("""SELECT DISTINCT m.* FROM media m WHERE m.id IN (SELECT media_id FROM person_media WHERE person_id=? UNION SELECT em.media_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE e.person_id=? UNION SELECT fm.media_id FROM family_media fm JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?) ORDER BY m.id""",(pid,pid,pid)):
        title=m["title"] or m["file_path"];y=_extract_year(title)
        if y:rows.append({"kind":"MEDIA","label":"Document/Media","date":str(y),"text":title})
    rows.sort(key=lambda r:(_date_key(r["date"]),r["kind"],r["label"],r["text"]));return rows

def format_research_timeline(db,pid):
    p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone();title=f"Integrated Research Timeline — {p['display_name']}";L=[title,"="*len(title),""];seen=set()
    for r in research_timeline_rows(db,pid):
        k=(r["kind"],r["label"],r["date"],r["text"])
        if k in seen:continue
        seen.add(k);L.append(f"{r['date'] or '(undated)'} — {r['label']} [{r['kind']}]")
        if r["text"]:L.append(f"  {r['text']}")
    if not seen:L.append("No dated material found.")
    L += ["","Note","----","Dates extracted from narrative notes and media titles are discovery cues. They are not promoted to Reunion events automatically."]
    return "\n".join(L)
