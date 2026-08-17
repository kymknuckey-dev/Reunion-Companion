from __future__ import annotations
import html,re
from pathlib import Path

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
    person=db.execute("SELECT id,sex FROM people WHERE id=?",(pid,)).fetchone()
    if not person: return []
    relationships=[];seen=set()
    def add(label,row,group):
        if not row or row["id"]==pid or row["id"] in seen:return
        seen.add(row["id"]);relationships.append((group,label,row["display_name"],row["id"]))
    own=db.execute("SELECT DISTINCT family_id FROM family_members WHERE person_id=? AND lower(role) IN ('husband','wife','spouse')",(pid,)).fetchall()
    for f in own:
        for r in db.execute("SELECT p.id,p.display_name,p.sex,fm.role FROM family_members fm JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? AND fm.person_id<>? ORDER BY p.id",(f["family_id"],pid)).fetchall():
            role=(r["role"] or "").lower()
            if role in ("husband","wife","spouse"):add("Spouse",r,0)
            elif role=="child":add(_sex_label(r["sex"],"Son","Daughter","Child"),r,0)
    births=db.execute("SELECT DISTINCT family_id FROM family_members WHERE person_id=? AND lower(role)='child'",(pid,)).fetchall()
    for f in births:
        for r in db.execute("SELECT p.id,p.display_name,p.sex,fm.role FROM family_members fm JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? AND fm.person_id<>? ORDER BY p.id",(f["family_id"],pid)).fetchall():
            role=(r["role"] or "").lower()
            if role in ("husband","wife","spouse"):add(_sex_label(r["sex"],"Father","Mother","Parent"),r,0)
            elif role=="child":add(_sex_label(r["sex"],"Brother","Sister","Sibling"),r,1)
    relationships.sort(key=lambda x:(x[0],{"Father":0,"Mother":1,"Parent":2,"Spouse":3,"Son":4,"Daughter":4,"Child":4,"Brother":5,"Sister":5,"Sibling":5}.get(x[1],9),x[2]))
    return relationships

def _portrait(w):
    for m in w.get("media",[]):
        if m.get("exists_on_disk") and Path(m.get("file_path") or "").suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp",".heic",".tif",".tiff"}: return m
    return None

def person_identity_header(db,w,presentation=True):
    p=w["person"];events=_events(db,p["id"]);family=_family(db,p["id"]);portrait=_portrait(w)
    img=f"<img src='/media-file/{portrait['id']}' alt='{esc(p['display_name'])}'>" if portrait else ""
    context=[]
    parents=[name for _,label,name,_ in family if label in ("Father","Mother","Parent")]
    spouse=next((name for _,label,name,_ in family if label=="Spouse"),None)
    if parents: context.append("Child of "+" and ".join(parents[:2]))
    if spouse: context.append("Spouse: "+spouse)
    context_html=f"<div class='rc-person-context'>{esc(' · '.join(context))}</div>" if context else ""
    xref="" if presentation else f"<div class='small'>{esc(p.get('gedcom_xref'))}</div>"
    return f"<section class='rc-person-strip'>{img}<div><div class='rc-person-name'>{esc(p['display_name'])}</div><div class='rc-person-life'>{esc(_lifespan(events))}</div>{context_html}{xref}</div></section>"

def person_story_body(db,w,presentation=True):
    p=w["person"];pid=p["id"];events=_events(db,pid);family=_family(db,pid);portrait=_portrait(w)
    portrait_html=f"<img class='person-portrait ffd-hero-portrait' src='/media-file/{portrait['id']}' alt='{esc(p['display_name'])}'>" if portrait else ""
    clean=[e for e in events if (e["event_type"] or "").casefold() not in ("changed","change") and (e["gedcom_tag"] or "").upper()!="CHAN"]
    pref={"birth":0,"baptism":1,"christening":1,"marriage":2,"military":3,"education":4,"occupation":5,"residence":6,"immigration":6,"emigration":6,"religion":7,"death":8,"burial":9}
    milestones=sorted(clean,key=lambda e:(pref.get((e["event_type"] or "").lower(),7),e["id"]))[:8]
    mh=""
    for e in milestones:
        detail=" · ".join(esc(x) for x in (e["date_text"],e["place_text"]) if x);note=e["note_text"] or e["value_text"] or "";yr=_year(e["date_text"])
        mh+=f"<div class='ffd-milestone'><div class='ffd-milestone-type'>{esc(yr or e['event_type'])}</div><div class='ffd-milestone-title'>{esc(e['event_type'])}{' — '+detail if detail else ''}</div>{f'<p>{esc(note)}</p>' if note else ''}</div>"
    if not mh: mh="<p class='meta'>No life events are currently available.</p>"
    immediate=[r for r in family if r[0]==0];close=[r for r in family if r[0]==1]
    def rows(items):
        return "".join(f"<div class='ffd-story-relation'><span class='meta'>{esc(label)}</span><a class='ffd-person-link' href='/person/{i}'><strong>{esc(name)}</strong></a><a class='ffd-inline-link' href='/person/{i}'>View person →</a></div>" for _,label,name,i in items)
    birth=next((e for e in clean if (e["event_type"] or "").casefold()=="birth"),None)
    spouse=next((name for _,label,name,_ in family if label=="Spouse"),None)
    children=sum(1 for _,label,_,_ in family if label in ("Son","Daughter","Child"))
    occupation=next((e["value_text"] or e["note_text"] for e in clean if (e["event_type"] or "").casefold()=="occupation" and (e["value_text"] or e["note_text"])),None)
    glance=[]
    if birth and _year(birth["date_text"]): glance.append((_year(birth["date_text"]),"Born"))
    if spouse: glance.append((spouse,"Spouse"))
    if children: glance.append((str(children),"Children"))
    if occupation: glance.append((occupation,"Occupation"))
    while len(glance)<3: glance.append((str(len(clean)),"Recorded life events"))
    gh="".join(f"<div><strong>{esc(v)}</strong><span>{esc(l)}</span></div>" for v,l in glance[:4])
    media=[m for m in w.get("media",[]) if m.get("exists_on_disk")][:4]
    media_html="".join(f"<a href='/media-item/{m['id']}'><img class='ffd-media-preview' src='/media-file/{m['id']}' alt='{esc(m.get('title') or '')}'></a>" for m in media if Path(m.get("file_path") or "").suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp",".heic",".tif",".tiff"})
    birth_context=""
    if birth:
        birth_context=" · ".join(esc(x) for x in (birth["date_text"],birth["place_text"]) if x)
    intro=[]
    if birth_context: intro.append("Born "+birth_context)
    if spouse: intro.append("Married to "+esc(spouse))
    return f"""<section class='ffd-person-hero ffd-person-editorial'><div><div class='ffd-eyebrow'>A life in the family history</div><h1>{esc(p['display_name'])}</h1><div class='ffd-lifespan'>{esc(_lifespan(events))}</div>{f"<p class='ffd-person-intro'>{' · '.join(intro)}</p>" if intro else ''}</div>{portrait_html}</section>
<div class='ffd-story-grid'><section><h2 class='ffd-section'>Life at a Glance</h2><div class='card'><div class='ffd-story-kpis ffd-human-kpis'>{gh}</div></div><h2 class='ffd-section'>Key Life Events</h2><div class='card ffd-life-sequence'>{mh}</div></section><aside><h2 class='ffd-section'>Family</h2><div class='card'><h3>Immediate Family</h3>{rows(immediate) or "<p class='meta'>No immediate family relationships are available.</p>"}{f"<h3 class='ffd-close-family'>Close Family</h3>{rows(close)}" if close else ''}</div><h2 class='ffd-section'>Media & Documents</h2><div class='card'>{f"<div class='ffd-media-strip'>{media_html}</div>" if media_html else "<p class='meta'>No image previews are currently available.</p>"}<p><a class='ffd-inline-link' href='/person/{pid}?tab=media'>View all media →</a></p></div></aside></div>"""
