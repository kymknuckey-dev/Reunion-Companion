from __future__ import annotations
import html,re
from pathlib import Path

from .branding import brand_data_uri

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
    for m in sorted(w.get("media",[]),key=lambda x:(-int(x.get("is_preferred") or 0),int(x.get("id") or 0))):
        if m.get("exists_on_disk") and Path(m.get("file_path") or "").suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp",".heic",".tif",".tiff"}: return m
    return None

def _person_portrait(db,pid):
    return db.execute("""SELECT DISTINCT m.* FROM media m JOIN person_media pm ON pm.media_id=m.id
      WHERE pm.person_id=? AND m.exists_on_disk=1 AND (
        lower(m.file_path) LIKE '%.jpg' OR lower(m.file_path) LIKE '%.jpeg' OR
        lower(m.file_path) LIKE '%.png' OR lower(m.file_path) LIKE '%.gif' OR
        lower(m.file_path) LIKE '%.webp' OR lower(m.file_path) LIKE '%.heic' OR
        lower(m.file_path) LIKE '%.tif' OR lower(m.file_path) LIKE '%.tiff'
      ) ORDER BY COALESCE(m.is_preferred,0) DESC,m.id LIMIT 1""",(pid,)).fetchone()

def _person_thumb(db,pid):
    person=db.execute("SELECT sex FROM people WHERE id=?",(pid,)).fetchone()
    portrait=_person_portrait(db,pid)
    if portrait: return f"/media-file/{portrait['id']}"
    sex=(person['sex'] if person else '') or ''
    asset='PersonMale.png' if sex.upper()=='M' else ('PersonFemale.png' if sex.upper()=='F' else 'PersonNeutral.png')
    return brand_data_uri(asset)

def _person_lifespan(db,pid):
    return _lifespan(_events(db,pid))

def person_identity_header(db,w,presentation=True):
    from .person_bookmarks import is_bookmarked
    p=w["person"];events=_events(db,p["id"]);family=_family(db,p["id"]);portrait=_portrait(w)
    bookmarked=is_bookmarked(db,p["id"])
    img=f"<img src='/media-file/{portrait['id']}' alt='{esc(p['display_name'])}'>" if portrait else ""
    context=[]
    parents=[name for _,label,name,_ in family if label in ("Father","Mother","Parent")]
    spouse=next((name for _,label,name,_ in family if label=="Spouse"),None)
    if parents: context.append("Child of "+" and ".join(parents[:2]))
    if spouse: context.append("Spouse: "+spouse)
    context_html=f"<div class='rc-person-context'>{esc(' · '.join(context))}</div>" if context else ""
    xref="" if presentation else f"<div class='small'>{esc(p.get('gedcom_xref'))}</div>"
    bookmark_label="Remove bookmark" if bookmarked else "Bookmark person"
    bookmark_symbol="★" if bookmarked else "☆"
    bookmark=f"<form class='rc-person-bookmark-form' method='post' action='/person/{p['id']}/bookmark'><input type='hidden' name='bookmarked' value='{0 if bookmarked else 1}'><button class='rc-person-bookmark {'active' if bookmarked else ''}' type='submit' title='{bookmark_label}' aria-label='{bookmark_label}'>{bookmark_symbol}<span>{bookmark_label}</span></button></form>"
    return f"<section class='rc-person-strip'>{img}<div class='rc-person-strip-copy'><div class='rc-person-eyebrow'>Current person</div><div class='rc-person-name'>{esc(p['display_name'])}</div><div class='rc-person-life'>{esc(_lifespan(events))}</div>{context_html}{xref}</div>{bookmark}</section>"

def _event_icon(kind):
    k=(kind or '').casefold()
    if 'birth' in k: path='<circle cx="12" cy="9" r="3"/><path d="M7 19c1-4 9-4 10 0M5 5h3M6.5 3.5v3"/>'
    elif 'educ' in k: path='<path d="M3 8l9-4 9 4-9 4-9-4zM6 10v5c3 2 9 2 12 0v-5M21 8v6"/>'
    elif 'marri' in k or 'spouse' in k: path='<circle cx="9" cy="12" r="5"/><circle cx="15" cy="12" r="5"/>'
    elif 'resid' in k or 'address' in k: path='<path d="M4 11l8-7 8 7v9H4zM9 20v-6h6v6"/>'
    elif 'occup' in k or 'career' in k or 'work' in k: path='<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V4h8v3M3 12h18M10 12v2h4v-2"/>'
    elif 'milit' in k or 'service' in k: path='<path d="M12 3l2.4 5 5.6.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.6-.8z"/>'
    elif 'relig' in k or 'bapt' in k or 'christ' in k: path='<path d="M12 3v18M7 8h10"/>'
    elif 'death' in k: path='<path d="M12 21s-8-4.7-8-11a4.5 4.5 0 018-2.8A4.5 4.5 0 0120 10c0 6.3-8 11-8 11z"/>'
    elif 'burial' in k or 'cremat' in k: path='<path d="M7 21V9a5 5 0 0110 0v12M4 21h16M9 12h6"/>'
    else: path='<circle cx="12" cy="12" r="7"/><path d="M12 8v5l3 2"/>'
    return f'<span class="ffd-event-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{path}</svg></span>'

def _event_kind(e):
    return ((e["event_type"] or e["gedcom_tag"] or "").casefold()).strip()

def _is_death_event(e):
    return "death" in _event_kind(e)

def _is_disposition_event(e):
    kind=_event_kind(e)
    return any(token in kind for token in ("burial","cremat","interment","ashes","cemetery"))

def _event_sort_key(e):
    year=_year(e["date_text"])
    # One adaptive Life Story: ordinary dated events first in chronology, then
    # useful undated life facts, with death and final disposition terminal.
    # No date is invented for an undated fact.
    if _is_disposition_event(e): return (3, int(year) if year else 9999, e["id"])
    if _is_death_event(e): return (2, int(year) if year else 9999, e["id"])
    if year: return (0, int(year), e["id"])
    undated_order={"christening":1,"baptism":1,"education":2,"marriage":3,"occupation":4,"military":5,"service":5,"residence":6,"religion":7}
    kind=_event_kind(e)
    rank=next((rank for token,rank in undated_order.items() if token in kind),8)
    return (1,rank,e["id"])

def person_story_body(db,w,presentation=True):
    p=w["person"];pid=p["id"];events=_events(db,pid);family=_family(db,pid);portrait=_portrait(w)
    portrait_html=f"<img class='person-portrait ffd-hero-portrait' src='/media-file/{portrait['id']}' alt='{esc(p['display_name'])}'>" if portrait else ""
    clean=[e for e in events if (e["event_type"] or "").casefold() not in ("changed","change") and (e["gedcom_tag"] or "").upper()!="CHAN"]
    ordered=sorted(clean,key=_event_sort_key)[:10]

    def milestone_html(e):
        kind=e["event_type"] or e["gedcom_tag"] or "Life event"
        year=_year(e["date_text"])
        details=[]
        if e["date_text"]: details.append(esc(e["date_text"]))
        if e["place_text"]: details.append(esc(e["place_text"]))
        value=e["value_text"] or ""
        note=e["note_text"] or ""
        if value and value not in note: details.append(esc(value))
        detail_html=f"<div class='ffd-milestone-detail'>{' · '.join(details)}</div>" if details else ""
        note_html=f"<p>{esc(note)}</p>" if note else ""
        chronology=f"<div class='ffd-chronology'><span class='ffd-chronology-dot' aria-hidden='true'></span></div>"
        dated_class=" ffd-milestone-dated" if year else " ffd-milestone-undated"
        return f"<div class='ffd-milestone{dated_class}'><div class='ffd-milestone-date'>{esc(year)}</div>{chronology}{_event_icon(kind)}<div class='ffd-milestone-copy'><div class='ffd-milestone-title'>{esc(kind)}</div>{detail_html}{note_html}</div></div>"

    mh="<div class='ffd-life-timeline'>"+"".join(milestone_html(e) for e in ordered)+"</div>" if ordered else "<p class='meta'>No life events are currently available.</p>"

    immediate=[r for r in family if r[0]==0];close=[r for r in family if r[0]==1]
    def rows(items):
        out=[]
        for _,label,name,i in items:
            life=_person_lifespan(db,i)
            life_html=f"<span class='ffd-relation-life'>{esc(life)}</span>" if life else ""
            out.append(f"<a class='ffd-story-relation ffd-person-link' href='/person/{i}'><img class='ffd-family-thumb' src='{_person_thumb(db,i)}' alt=''><span class='ffd-relation-copy'><span class='meta'>{esc(label)}</span><strong>{esc(name)}</strong>{life_html}</span><span class='ffd-relation-arrow'>→</span></a>")
        return "".join(out)

    birth=next((e for e in clean if (e["event_type"] or "").casefold()=="birth"),None)
    spouse=next((name for _,label,name,_ in family if label=="Spouse"),None)
    parents=[name for _,label,name,_ in family if label in ("Father","Mother","Parent")]
    occupation_event=next((e for e in clean if (e["event_type"] or "").casefold()=="occupation" and (e["value_text"] or e["note_text"])),None)
    occupation=(occupation_event["value_text"] or occupation_event["note_text"]) if occupation_event else None

    images=[m for m in w.get("media",[]) if m.get("exists_on_disk") and Path(m.get("file_path") or "").suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp",".heic",".tif",".tiff"}]
    media_html="".join(f"<a href='/media-item/{m['id']}'><img class='ffd-media-preview' src='/media-file/{m['id']}' alt='{esc(m.get('title') or '')}'></a>" for m in images[:4])

    context=[]
    if parents: context.append(f"<div><span>Parents</span><strong>{esc(' · '.join(parents[:2]))}</strong></div>")
    if spouse: context.append(f"<div><span>Spouse</span><strong>{esc(spouse)}</strong></div>")
    context_html=f"<div class='ffd-hero-context'>{''.join(context)}</div>" if context else ""

    intro=[]
    if birth:
        birth_bits=[x for x in (birth["date_text"],birth["place_text"]) if x]
        if birth_bits: intro.append("Born "+" · ".join(esc(x) for x in birth_bits))
    if occupation: intro.append(esc(occupation))
    intro_html=f"<p class='ffd-person-intro'>{' · '.join(intro)}</p>" if intro else ""

    family_html=rows(immediate) or "<p class='meta'>No immediate family relationships are available.</p>"
    if close: family_html+=f"<h3 class='ffd-close-family'>Close Family</h3>{rows(close)}"
    media_section=f"<h2 class='ffd-section'>Media & Documents</h2><div class='card'><div class='ffd-media-strip'>{media_html}</div><p><a class='ffd-inline-link' href='/person/{pid}?tab=media'>View all media →</a></p></div>" if media_html else ""

    hero_state='ffd-hero-has-photo' if portrait else 'ffd-hero-no-photo'
    return f"""<section class='ffd-person-hero ffd-person-editorial {hero_state}'><div class='ffd-eyebrow'>A life in the family history</div><div class='ffd-hero-layout'>{portrait_html}<div class='ffd-hero-copy'><h1>{esc(p['display_name'])}</h1><div class='ffd-lifespan'>{esc(_lifespan(events))}</div>{intro_html}{context_html}</div></div></section>
<div class='ffd-story-grid'><section><h2 class='ffd-section'>Life Story</h2><div class='card ffd-life-sequence'>{mh}</div></section><aside><h2 class='ffd-section'>Family</h2><div class='card'><h3>Immediate Family</h3>{family_html}</div>{media_section}</aside></div>"""
