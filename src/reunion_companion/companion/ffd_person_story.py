from __future__ import annotations
import html,re
from pathlib import Path
from .person_navigation import nav_html, action_cards
def esc(v): return html.escape("" if v is None else str(v))
def _year(v):
    m=re.search(r"\b(1[5-9]\d{2}|20\d{2}|2100)\b",v or "")
    return m.group(1) if m else ""
def _events(db,pid):
    return db.execute("SELECT id,event_type,date_text,place_text,value_text,note_text,gedcom_tag FROM events WHERE person_id=? ORDER BY id",(pid,)).fetchall()
def _lifespan(events):
    b=d=""
    for e in events:
        t=(e["event_type"] or "").lower()
        if t=="birth" and not b: b=_year(e["date_text"])
        if t=="death" and not d: d=_year(e["date_text"])
    return f"{b}–{d}" if b and d else (f"Born {b}" if b else (f"Died {d}" if d else ""))
def _sex_label(sex,male,female,generic):
    value=(sex or "").upper()
    if value=="M": return male
    if value=="F": return female
    return generic

def _family(db,pid):
    """Resolve relationships from the perspective of the person being viewed."""
    person=db.execute("SELECT id,sex FROM people WHERE id=?",(pid,)).fetchone()
    if not person:
        return []

    relationships=[]
    seen=set()

    def add(label,row,group):
        if not row or row["id"]==pid or row["id"] in seen:
            return
        seen.add(row["id"])
        relationships.append((group,label,row["display_name"],row["id"]))

    # Families where this person is a spouse/parent.
    own_families=db.execute(
        """SELECT DISTINCT family_id FROM family_members
           WHERE person_id=? AND lower(role) IN ('husband','wife','spouse')""",(pid,)
    ).fetchall()

    for f in own_families:
        fid=f["family_id"]
        others=db.execute(
            """SELECT p.id,p.display_name,p.sex,fm.role
               FROM family_members fm JOIN people p ON p.id=fm.person_id
               WHERE fm.family_id=? AND fm.person_id<>?
               ORDER BY p.id""",(fid,pid)
        ).fetchall()
        for r in others:
            role=(r["role"] or "").lower()
            if role in ("husband","wife","spouse"):
                add("Spouse",r,0)
            elif role=="child":
                add(_sex_label(r["sex"],"Son","Daughter","Child"),r,0)

    # Families where this person is a child: other spouses are parents;
    # other children are siblings.
    birth_families=db.execute(
        """SELECT DISTINCT family_id FROM family_members
           WHERE person_id=? AND lower(role)='child'""",(pid,)
    ).fetchall()

    for f in birth_families:
        fid=f["family_id"]
        members=db.execute(
            """SELECT p.id,p.display_name,p.sex,fm.role
               FROM family_members fm JOIN people p ON p.id=fm.person_id
               WHERE fm.family_id=? AND fm.person_id<>?
               ORDER BY p.id""",(fid,pid)
        ).fetchall()
        for r in members:
            role=(r["role"] or "").lower()
            if role in ("husband","wife","spouse"):
                add(_sex_label(r["sex"],"Father","Mother","Parent"),r,0)
            elif role=="child":
                add(_sex_label(r["sex"],"Brother","Sister","Sibling"),r,1)

    relationships.sort(key=lambda x:(x[0],{"Father":0,"Mother":1,"Parent":2,"Spouse":3,
                                           "Son":4,"Daughter":4,"Child":4,
                                           "Brother":5,"Sister":5,"Sibling":5}.get(x[1],9),x[2]))
    return relationships

def person_story_body(db,w,presentation=True):
    p=w["person"];pid=p["id"];events=_events(db,pid);family=_family(db,pid)
    portrait=None
    for m in w.get("media",[]):
        if m.get("exists_on_disk") and Path(m.get("file_path") or "").suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp",".heic",".tif",".tiff"}:
            portrait=m;break
    portrait_html=f"<img class='person-portrait' src='/media-file/{portrait['id']}' alt='{esc(p['display_name'])}'>" if portrait else ""
    pref={"birth":0,"baptism":1,"christening":1,"marriage":2,"military":3,"occupation":4,"residence":5,"immigration":5,"emigration":5,"death":8,"burial":9}
    milestones=sorted(events,key=lambda e:(pref.get((e["event_type"] or "").lower(),6),e["id"]))[:7]
    tabs=nav_html(pid,presentation,"overview")
    mh=""
    # CHAN/Changed is GEDCOM record metadata, not a life event.
    milestones=[e for e in milestones if (e["event_type"] or "").casefold() not in ("changed","change") and (e["gedcom_tag"] or "").upper()!="CHAN"]
    for e in milestones:
        detail=" · ".join(esc(x) for x in (e["date_text"],e["place_text"]) if x)
        note=e["note_text"] or e["value_text"] or ""
        mh+=f"""<div class='ffd-milestone'>
<div class='ffd-milestone-type'>{esc(e['event_type'])}</div>
<div class='ffd-milestone-title'>{detail or 'Recorded event'}</div>
{f"<p>{esc(note)}</p>" if note else ""}
</div>"""
    if not mh:mh="<p class='meta'>No dated milestones are currently available.</p>"
    immediate=[r for r in family if r[0]==0]
    close=[r for r in family if r[0]==1]
    def family_rows(rows):
        return "".join(
            f"<div class='ffd-story-relation'><span class='meta'>{esc(label)}</span>"
            f"<strong>{esc(name)}</strong><a class='ffd-inline-link' href='/person/{i}'>View person →</a></div>"
            for _,label,name,i in rows
        )
    fh=family_rows(immediate) or "<p class='meta'>No immediate family relationships are available.</p>"
    ch=family_rows(close)
    return f"""{tabs}
<section class='ffd-person-hero'><div class='person-heading'><div><div class='ffd-eyebrow'>A life in the family history</div><h1>{esc(p["display_name"])}</h1>
<div class='ffd-lifespan'>{esc(_lifespan(events))}</div></div>{portrait_html}</div>
<p class='ffd-person-intro'>Explore the recorded events, family relationships, biography, media and evidence that make up this life story.</p>
<div class='ffd-story-actions'>{action_cards(pid,presentation)}</div></section>
<div class='ffd-story-grid'><section><h2 class='ffd-section'>Life at a Glance</h2><div class='card'><div class='ffd-story-kpis'><div><strong>{len(events)}</strong><span>recorded events</span></div><div><strong>{len(family)}</strong><span>family links</span></div><div><strong>1</strong><span>connected life story</span></div></div></div>
<h2 class='ffd-section'>Key Life Events</h2><div class='card'>{mh}</div></section><aside>
<h2 class='ffd-section'>Family</h2><div class='card'><h3>Immediate Family</h3>{fh}{f"<h3 class='ffd-close-family'>Close Family</h3>{ch}" if ch else ""}</div>
<h2 class='ffd-section'>Media & Documents</h2><div class='card'><p>Explore photographs and documents through the existing Companion media workspace.</p><p><a class='ffd-inline-link' href='/person/{pid}?tab=media'>Explore media →</a></p></div>
<h2 class='ffd-section'>Explore Further</h2><div class='card ffd-deeper'>
<a class='ffd-secondary-link' href='/person/{pid}?tab=timeline&view=story'><span>Life Story</span><small>Read the event-driven timeline</small></a>
<a class='ffd-secondary-link' href='/person/{pid}?tab=biography'><span>Biography</span><small>Read the recorded narrative</small></a>
<a class='ffd-secondary-link' href='/person/{pid}?tab=family'><span>Family</span><small>Explore connected people</small></a>
<a class='ffd-secondary-link' href='/person/{pid}?tab=sources'><span>Sources</span><small>Review supporting evidence</small></a>
<a class='ffd-secondary-link' href='/person/{pid}?tab=publish'><span>Publishing</span><small>Create a report or chapter</small></a>
</div></aside></div>"""
