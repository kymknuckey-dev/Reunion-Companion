from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import calendar,re
from .discovery import relationship_connections

MONTHS={
    "JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
    "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12
}
QUALIFIERS=("ABT","ABOUT","BEF","BEFORE","AFT","AFTER","EST","CAL","CIRCA","CA")
YEAR_RE=re.compile(r"\b(1[4-9]\d{2}|20\d{2}|21\d{2})\b")
FULL_RE=re.compile(r"\b(\d{1,2})\s+([A-Z]{3})\s+((?:1[4-9]|20|21)\d{2})\b")
MONTH_RE=re.compile(r"\b([A-Z]{3})\s+((?:1[4-9]|20|21)\d{2})\b")

@dataclass(frozen=True)
class ParsedDate:
    original:str
    year:int|None
    month:int|None
    day:int|None
    qualifier:str|None
    precision:str
    sort_key:tuple
    ordinal:int|None

def _ordinal(year,month=None,day=None):
    if not year:return None
    # Midpoint for partial dates gives sensible gap/age estimates without
    # pretending a precision that Reunion does not contain.
    month=month or 7
    day=day or 15
    day=min(day,calendar.monthrange(year,month)[1])
    return date(year,month,day).toordinal()

def parse_genealogy_date(text):
    original=(text or "").strip()
    upper=original.upper()
    qualifier=None
    for q in QUALIFIERS:
        if re.search(rf"\b{re.escape(q)}\b",upper):
            qualifier=q
            break
    m=FULL_RE.search(upper)
    if m and m.group(2) in MONTHS:
        y=int(m.group(3));mo=MONTHS[m.group(2)];d=int(m.group(1))
        return ParsedDate(original,y,mo,d,qualifier,"day",(y,mo,d),_ordinal(y,mo,d))
    m=MONTH_RE.search(upper)
    if m and m.group(1) in MONTHS:
        y=int(m.group(2));mo=MONTHS[m.group(1)]
        return ParsedDate(original,y,mo,None,qualifier,"month",(y,mo,15),_ordinal(y,mo,None))
    m=YEAR_RE.search(upper)
    if m:
        y=int(m.group(1))
        return ParsedDate(original,y,None,None,qualifier,"year",(y,7,15),_ordinal(y,None,None))
    return ParsedDate(original,None,None,None,qualifier,"unknown",(99999,12,31),None)

def source_number(xref):
    m=re.fullmatch(r"@?S(\d+)@?",(xref or "").strip(),re.I)
    return int(m.group(1)) if m else None

def source_label(row):
    n=source_number(row["gedcom_xref"])
    text=row["display_text"] or row["text"] or row["title"] or "(undescribed source)"
    return f"Source {n} — {text}" if n is not None else text

def event_sources(db,event_id):
    return [dict(x) for x in db.execute("""SELECT DISTINCT s.* FROM sources s
      JOIN event_sources es ON es.source_id=s.id
      WHERE es.event_id=? ORDER BY s.id""",(event_id,)).fetchall()]

def event_media(db,event_id):
    return [dict(x) for x in db.execute("""SELECT DISTINCT m.* FROM media m
      JOIN event_media em ON em.media_id=m.id
      WHERE em.event_id=? ORDER BY m.id""",(event_id,)).fetchall()]

def _related_people(db,pid,event_type):
    try:
        con=relationship_connections(db,pid)
    except Exception:
        return []
    if event_type=="Birth":
        rows=con.get("parents",[])
        relation="Parent"
    elif event_type=="Marriage":
        rows=con.get("spouses",[])
        relation="Spouse"
    else:
        return []
    return [{"id":x["id"],"display_name":x["display_name"],"relation":relation} for x in rows]

def _age_text(birth,event):
    if not birth or birth.ordinal is None or event.ordinal is None:return None
    if event.ordinal < birth.ordinal:return None
    days=event.ordinal-birth.ordinal
    if birth.precision=="day" and event.precision=="day":
        # Completed years, as genealogists normally express age at an exact event.
        years=event.year-birth.year
        if (event.month,event.day) < (birth.month,birth.day):years-=1
        return f"{years} years"
    # Partial dates cannot justify day-level precision.  Use the recorded year
    # difference and label it explicitly as approximate.
    if birth.year is not None and event.year is not None:
        delta=event.year-birth.year
        if delta<1:return "under 1 year"
        return f"about {delta} years"
    return None

def _elapsed_text(a,b):
    if not a or not b or a.ordinal is None or b.ordinal is None:return None
    days=b.ordinal-a.ordinal
    if days<0:return None
    years=days/365.2425
    if years>=2:return f"{years:.1f} years"
    if years>=1:return f"{years:.1f} year"
    months=days/30.4375
    if months>=2:return f"{months:.0f} months"
    if months>=1:return f"{months:.1f} month"
    return f"{days} days"

def _story_sentence(event):
    typ=event["type"];date_text=event["date"] or "an unknown date"
    place=event["place"];value=event["value"]
    subject=event["person_name"]
    if typ=="Birth":
        s=f"{subject} was born on {date_text}" if event["date"] else f"{subject}'s birth is recorded"
    elif typ=="Death":
        s=f"{subject} died on {date_text}" if event["date"] else f"{subject}'s death is recorded"
    elif typ=="Marriage":
        s=f"{subject} married on {date_text}" if event["date"] else f"A marriage is recorded for {subject}"
    elif typ=="Occupation":
        s=f"{subject}'s occupation"
        if value and value!="Y":s+=f" was recorded as {value}"
        if event["date"]:s+=f" on {date_text}"
    elif typ=="Education":
        s=f"Education was recorded for {subject}"
        if value and value!="Y":s+=f": {value}"
        if event["date"]:s+=f" ({date_text})"
    elif typ=="Residence":
        s=f"{subject} had a residence recorded"
        if event["date"]:s+=f" on {date_text}"
    else:
        s=f"{typ} was recorded for {subject}"
        if event["date"]:s+=f" on {date_text}"
        if value and value!="Y":s+=f": {value}"
    if place:s+=f" at {place}"
    return s.rstrip(".")+"."        

def _quality_observations(event,birth,death,previous_dated,next_dated):
    out=[]
    if not event["date"]:out.append("Date not recorded")
    if not event["place"] and event["type"] in {"Birth","Death","Burial","Cremation","Marriage","Residence","Education","Occupation"}:
        out.append("Place not recorded")
    if event["source_count"]==0:out.append("No directly linked source")
    if event["media_count"]==0:out.append("No directly linked media")
    pd=event["_parsed"]
    if birth and pd.year and birth.year and event["type"]!="Birth" and pd.year<birth.year:
        out.append(f"Occurs before recorded birth year {birth.year}")
    if death and pd.year and death.year and event["type"] not in {"Death","Burial","Cremation"} and pd.year>death.year:
        out.append(f"Occurs after recorded death year {death.year}")
    if previous_dated and pd.ordinal and previous_dated["_parsed"].ordinal:
        gap=(pd.ordinal-previous_dated["_parsed"].ordinal)/365.2425
        if gap>=10:
            out.append(f"Gap of about {round(gap)} years since previous dated event")
    return out

def timeline_for_person(db,pid):
    person=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    if not person:return None
    raw=[dict(x) for x in db.execute("""SELECT * FROM events
      WHERE person_id=? AND event_type<>'Changed' ORDER BY id""",(pid,)).fetchall()]
    for e in raw:e["_parsed"]=parse_genealogy_date(e.get("date_text"))
    raw.sort(key=lambda e:(e["_parsed"].sort_key,e["id"]))

    birth_event=next((e for e in raw if e["event_type"]=="Birth"),None)
    death_event=next((e for e in raw if e["event_type"]=="Death"),None)
    birth=birth_event["_parsed"] if birth_event else None
    death=death_event["_parsed"] if death_event else None

    result=[]
    dated=[e for e in raw if e["_parsed"].ordinal is not None]
    for idx,e in enumerate(raw):
        sources=event_sources(db,e["id"])
        media=event_media(db,e["id"])
        source_link_count=db.execute("SELECT COUNT(*) FROM event_sources WHERE event_id=?",(e["id"],)).fetchone()[0]
        media_link_count=db.execute("SELECT COUNT(*) FROM event_media WHERE event_id=?",(e["id"],)).fetchone()[0]
        parsed=e["_parsed"]
        previous=next((x for x in reversed(raw[:idx]) if x["_parsed"].ordinal is not None),None)
        nxt=next((x for x in raw[idx+1:] if x["_parsed"].ordinal is not None),None)
        item={
          "id":e["id"],"person_id":pid,"person_name":person["display_name"],
          "type":e["event_type"],"gedcom_tag":e.get("gedcom_tag"),
          "date":e["date_text"],"place":e["place_text"],
          "value":None if e["value_text"]=="Y" else e["value_text"],
          "note":e.get("note_text"),"date_precision":parsed.precision,
          "date_qualifier":parsed.qualifier,"year":parsed.year,
          "age":_age_text(birth,parsed),
          "since_previous":_elapsed_text(previous["_parsed"],parsed) if previous else None,
          "until_next":_elapsed_text(parsed,nxt["_parsed"]) if nxt else None,
          "sources":sources,"media":media,
          "source_count":source_link_count,"media_count":media_link_count,
          "evidence_status":"supported" if (source_link_count or media_link_count) else "unlinked",
          "related_people":_related_people(db,pid,e["event_type"]),
          "_parsed":parsed,
        }
        item["story"]=_story_sentence(item)
        item["observations"]=_quality_observations(item,birth,death,previous,nxt)
        result.append(item)

    # Strip private parse objects before returning.
    for x in result:x.pop("_parsed",None)
    return {
      "person":dict(person),
      "events":result,
      "summary":{
        "event_count":len(result),
        "dated_count":sum(1 for x in result if x["year"] is not None),
        "supported_count":sum(1 for x in result if x["evidence_status"]=="supported"),
        "observation_count":sum(len(x["observations"]) for x in result),
      }
    }

def event_detail(db,event_id):
    row=db.execute("SELECT person_id FROM events WHERE id=?",(event_id,)).fetchone()
    if not row:return None
    timeline=timeline_for_person(db,row["person_id"])
    event=next((x for x in timeline["events"] if x["id"]==event_id),None)
    if not event:return None
    index=timeline["events"].index(event)
    return {
      "person":timeline["person"],"event":event,
      "previous_event":timeline["events"][index-1] if index else None,
      "next_event":timeline["events"][index+1] if index+1<len(timeline["events"]) else None,
      "summary":timeline["summary"],
    }

# ------------------------------------------------------------------
# Legacy chapter API retained for Foundation 8-11 publishing engines.
# The UI and new research work use timeline_for_person() above.
# ------------------------------------------------------------------
def _legacy_year(text):
    m=YEAR_RE.search(text or "")
    return int(m.group(1)) if m else None

def chapter_for_event(e):
    typ=e["event_type"]
    val=" ".join(x or "" for x in (e["value_text"],e["place_text"],e["note_text"]))
    low=(typ+" "+val).lower()
    if typ=="Birth":return "Early Life"
    if any(x in low for x in ("military","army","air force","raaf","navy","service")):return "Military Service"
    if typ=="Marriage":return "Marriage & Family"
    if typ in ("Occupation","Education"):return "Education & Working Life"
    if typ in ("Death","Burial","Cremation"):return "Later Life & Memorial"
    if typ=="Residence":return "Residences"
    return "Life Events"

def intelligent_timeline(db,pid):
    events=db.execute("SELECT * FROM events WHERE person_id=? AND event_type<>'Changed' ORDER BY id",(pid,)).fetchall()
    order=["Early Life","Education & Working Life","Military Service","Marriage & Family","Residences","Life Events","Later Life & Memorial"]
    groups={k:[] for k in order}
    for e in events:
        groups.setdefault(chapter_for_event(e),[]).append(e)
    for k in groups:
        groups[k].sort(key=lambda e:(_legacy_year(e["date_text"]) or 99999,e["id"]))
    return [(k,groups[k]) for k in order if groups.get(k)]

def format_timeline_intelligence(db,pid):
    """Legacy chapter formatter retained for CLI/publishing compatibility."""
    person=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
    title=f"Life Chapters — {person['display_name']}"
    lines=[title,"="*len(title)]
    for chapter,events in intelligent_timeline(db,pid):
        lines += ["",chapter,"-"*len(chapter)]
        for e in events:
            bits=[e["event_type"]]+[x for x in (e["date_text"],e["place_text"],e["value_text"]) if x and x!="Y"]
            lines.append("  "+" — ".join(bits))
    return "\\n".join(lines)

def format_event_timeline_intelligence(db,pid):
    """Sprint 1 event-by-event diagnostic formatter."""
    t=timeline_for_person(db,pid)
    if not t:return "Person not found."
    title=f"Timeline Intelligence — {t['person']['display_name']}"
    lines=[title,"="*len(title)]
    for e in t["events"]:
        lines += ["",f"{e['date'] or '(undated)'} — {e['type']}"]
        if e["place"]:lines.append(f"  Place: {e['place']}")
        if e["value"]:lines.append(f"  Detail: {e['value']}")
        if e["age"]:lines.append(f"  Age: {e['age']}")
        lines.append(f"  Evidence: {e['source_count']} source(s), {e['media_count']} media item(s)")
        for source in e["sources"]:lines.append(f"    {source_label(source)}")
        for observation in e["observations"]:lines.append(f"  Review: {observation}")
    return "\\n".join(lines)
