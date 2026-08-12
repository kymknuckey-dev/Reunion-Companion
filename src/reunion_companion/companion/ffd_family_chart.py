from __future__ import annotations
import html,re
from collections import deque
WINDOW_SIZE=4

def esc(v): return html.escape("" if v is None else str(v))
def _year(v):
    m=re.search(r"\b(1[5-9]\d{2}|20\d{2}|2100)\b",v or "")
    return m.group(1) if m else ""
def _person(db,pid):
    r=db.execute("SELECT id,display_name,sex,gedcom_xref FROM people WHERE id=?",(pid,)).fetchone()
    return dict(r) if r else None
def _life_dates(db,pid):
    rows=db.execute("SELECT event_type,date_text FROM events WHERE person_id=? AND lower(event_type) IN ('birth','death') ORDER BY id",(pid,)).fetchall()
    birth=death=""
    for r in rows:
        t=(r["event_type"] or "").lower()
        if t=="birth" and not birth:birth=r["date_text"] or ""
        elif t=="death" and not death:death=r["date_text"] or ""
    by,dy=_year(birth),_year(death)
    return {"birth":birth,"death":death,"lifespan":f"{by}–{dy}" if by and dy else (f"b. {by}" if by else (f"d. {dy}" if dy else ""))}
def _families_as_child(db,pid):
    return [r["family_id"] for r in db.execute("SELECT family_id FROM family_members WHERE person_id=? AND lower(role)='child' ORDER BY family_id",(pid,)).fetchall()]
def _families_as_spouse(db,pid):
    return [r["family_id"] for r in db.execute("SELECT family_id FROM family_members WHERE person_id=? AND lower(role) IN ('husband','wife','spouse') ORDER BY family_id",(pid,)).fetchall()]
def _family_members(db,fid):
    return [dict(r) for r in db.execute("""SELECT p.id,p.display_name,p.sex,p.gedcom_xref,fm.role FROM family_members fm
    JOIN people p ON p.id=fm.person_id WHERE fm.family_id=? ORDER BY CASE lower(fm.role)
    WHEN 'husband' THEN 0 WHEN 'wife' THEN 1 WHEN 'spouse' THEN 2 WHEN 'child' THEN 3 ELSE 4 END,p.id""",(fid,)).fetchall()]
def _spouses_in_family(db,fid):return [p for p in _family_members(db,fid) if (p["role"] or "").lower() in ("husband","wife","spouse")]
def _children_in_family(db,fid):return [p for p in _family_members(db,fid) if (p["role"] or "").lower()=="child"]
def _parents(db,pid):
    out=[];seen=set()
    for fid in _families_as_child(db,pid):
        for p in _spouses_in_family(db,fid):
            if p["id"] not in seen:seen.add(p["id"]);out.append(p)
    return out
def _children(db,pid):
    out=[];seen=set()
    for fid in _families_as_spouse(db,pid):
        for p in _children_in_family(db,fid):
            if p["id"] not in seen:seen.add(p["id"]);out.append(p)
    return out
def _sex_word(sex,male,female,generic):
    s=(sex or "").upper();return male if s=="M" else female if s=="F" else generic
def _ancestor_relationship(sex,g):
    if g==1:return _sex_word(sex,"Father","Mother","Parent")
    if g==2:return _sex_word(sex,"Grandfather","Grandmother","Grandparent")
    if g==3:return _sex_word(sex,"Great-grandfather","Great-grandmother","Great-grandparent")
    return _sex_word(sex,f"{g-2}× Great-grandfather",f"{g-2}× Great-grandmother",f"{g-2}× Great-grandparent")
def _descendant_relationship(sex,g):
    if g==1:return _sex_word(sex,"Son","Daughter","Child")
    if g==2:return _sex_word(sex,"Grandson","Granddaughter","Grandchild")
    if g==3:return _sex_word(sex,"Great-grandson","Great-granddaughter","Great-grandchild")
    return _sex_word(sex,f"{g-2}× Great-grandson",f"{g-2}× Great-granddaughter",f"{g-2}× Great-grandchild")
def _node(db,p,relationship,generation,direction):
    return {"id":p["id"],"display_name":p["display_name"],"sex":p.get("sex"),"relationship":relationship,"generation":generation,"direction":direction,**_life_dates(db,p["id"])}
def ancestors(db,pid):
    result=[];q=deque([(pid,0)]);visited={pid}
    while q:
        cur,g=q.popleft()
        for p in _parents(db,cur):
            if p["id"] in visited:continue
            visited.add(p["id"]);ng=g+1;result.append(_node(db,p,_ancestor_relationship(p.get("sex"),ng),ng,"ancestor"));q.append((p["id"],ng))
    return result
def descendants(db,pid):
    result=[];q=deque([(pid,0)]);visited={pid}
    while q:
        cur,g=q.popleft()
        for p in _children(db,cur):
            if p["id"] in visited:continue
            visited.add(p["id"]);ng=g+1;result.append(_node(db,p,_descendant_relationship(p.get("sex"),ng),ng,"descendant"));q.append((p["id"],ng))
    return result
def _family_unit(db,fid,selected_id=None,generation=0,direction="descendant"):
    spouses=[_node(db,p,"Selected Person" if p["id"]==selected_id else "Spouse",generation,direction) for p in _spouses_in_family(db,fid)]
    children=[_node(db,p,"Child",generation+1 if direction=="descendant" else max(0,generation-1),direction) for p in _children_in_family(db,fid)]
    return {"family_id":fid,"spouses":spouses,"children":children}
def selected_family_units(db,pid):
    units=[_family_unit(db,fid,pid,0,"descendant") for fid in _families_as_spouse(db,pid)]
    if units:return units
    p=_person(db,pid);return [{"family_id":None,"spouses":[_node(db,p,"Selected Person",0,"selected")],"children":[]}]
def descendant_family_units(db,pid):
    all_desc=descendants(db,pid);gen={n["id"]:n["generation"] for n in all_desc};gen[pid]=0
    units=[];seen=set();q=deque([pid]);visited=set()
    while q:
        person_id=q.popleft()
        if person_id in visited:continue
        visited.add(person_id);g=gen.get(person_id,0)
        for fid in _families_as_spouse(db,person_id):
            if fid in seen:continue
            seen.add(fid);u=_family_unit(db,fid,pid,g,"descendant")
            for sp in u["spouses"]:
                sp["relationship"]="Selected Person" if sp["id"]==pid else (_descendant_relationship(sp.get("sex"),gen[sp["id"]]) if sp["id"] in gen else "Spouse")
            for ch in u["children"]:
                cg=g+1;ch["generation"]=cg;ch["relationship"]=_descendant_relationship(ch.get("sex"),cg);gen.setdefault(ch["id"],cg);q.append(ch["id"])
            units.append(u)
    return units
def ancestor_family_units(db,pid):
    all_anc=ancestors(db,pid);gen={n["id"]:n["generation"] for n in all_anc};ancestor_ids=set(gen);line_ids=ancestor_ids|{pid}
    units=[];seen=set()
    for aid,g in sorted(gen.items(),key=lambda x:x[1]):
        for fid in _families_as_spouse(db,aid):
            if fid in seen:continue
            if not any(c["id"] in line_ids for c in _children_in_family(db,fid)):continue
            seen.add(fid);u=_family_unit(db,fid,pid,g,"ancestor")
            for sp in u["spouses"]:
                sg=gen.get(sp["id"],g);sp["generation"]=sg;sp["relationship"]=_ancestor_relationship(sp.get("sex"),sg)
            for ch in u["children"]:
                if ch["id"]==pid:ch["relationship"]="Selected Person";ch["generation"]=0
                elif ch["id"] in gen:ch["relationship"]=_ancestor_relationship(ch.get("sex"),gen[ch["id"]]);ch["generation"]=gen[ch["id"]]
                else:ch["relationship"]="Child";ch["generation"]=max(0,g-1)
            units.append(u)
    return units
def family_chart(db,pid):
    p=_person(db,pid)
    if not p:return None
    return {"selected":_node(db,p,"Selected Person",0,"selected"),"ancestors":ancestors(db,pid),"descendants":descendants(db,pid),
            "ancestor_units":ancestor_family_units(db,pid),"selected_units":selected_family_units(db,pid),"descendant_units":descendant_family_units(db,pid)}
def _generation_title(direction,g):
    if direction=="ancestor":
        if g==1:return "Parents"
        if g==2:return "Grandparents"
        if g==3:return "Great-grandparents"
        return f"{g-2}× Great-grandparents"
    if g==0:return "Selected Family"
    if g==1:return "Children & their families"
    if g==2:return "Grandchildren & their families"
    if g==3:return "Great-grandchildren & their families"
    return f"{g-2}× Great-grandchildren & their families"
def _person_card(n,compact=False):
    cls="unit-person compact" if compact else "unit-person"
    return f"<a class='{cls}' href='/person/{n['id']}'><span class='unit-role'>{esc(n['relationship'])}</span><strong>{esc(n['display_name'])}</strong><span class='unit-dates'>{esc(n['lifespan'] or 'Dates not recorded')}</span></a>"
def _unit_card(unit):
    couple="".join(_person_card(p) for p in unit["spouses"])
    children=unit["children"]
    child_html=("<div class='unit-children-label'>Children</div><div class='unit-children'>"+"".join(_person_card(c,True) for c in children)+"</div>") if children else ""
    return f"<div class='family-unit-card'><div class='unit-couple'>{couple}</div>{child_html}</div>"
def _bounds(data):
    return -max([n["generation"] for n in data["ancestors"]],default=0),max([n["generation"] for n in data["descendants"]],default=0)
def _window(data,offset):
    lo_all,hi_all=_bounds(data);offset=max(lo_all,min(hi_all,offset));low=offset-1;high=low+WINDOW_SIZE-1
    if low<lo_all:high+=lo_all-low;low=lo_all
    if high>hi_all:low-=high-hi_all;high=hi_all
    return offset,max(lo_all,low),high,lo_all,hi_all
def _units_for_generation(data,g):
    if g<0:
        target=-g;return [u for u in data["ancestor_units"] if any(sp["generation"]==target for sp in u["spouses"])]
    if g==0:return data["selected_units"]
    return [u for u in data["descendant_units"] if any(sp["generation"]==g for sp in u["spouses"])]
def family_chart_body(db,pid,offset=0):
    data=family_chart(db,pid)
    if not data:return "<div class='card'><p>Person not found.</p></div>"
    try:offset=int(offset)
    except Exception:offset=0
    offset,low,high,lo_all,hi_all=_window(data,offset)
    sections=[]
    for g in range(low,high+1):
        units=_units_for_generation(data,g)
        if not units:continue
        title=_generation_title("ancestor" if g<0 else "descendant",abs(g) if g<0 else g)
        sections.append(f"<section class='unit-generation'><div class='unit-generation-title'>{esc(title)}</div><div class='unit-family-grid'>{''.join(_unit_card(u) for u in units)}</div></section>")
    prev_disabled=low<=lo_all;next_disabled=high>=hi_all
    nav=f"""<div class='chart-window-nav'>
    <a class='ffd-back-link {"disabled" if prev_disabled else ""}' href='/person/{pid}?tab=family-chart&offset={offset-WINDOW_SIZE}'>← Previous Generations</a>
    <span class='chart-window-status'>Showing generations {low:+d} to {high:+d}</span>
    <a class='ffd-back-link {"disabled" if next_disabled else ""}' href='/person/{pid}?tab=family-chart&offset={offset+WINDOW_SIZE}'>Later Generations →</a></div>"""
    return f"""<div class='live-chart-heading'><div class='ffd-eyebrow'>Live family chart</div><h1>{esc(data["selected"]["display_name"])}</h1>
    <p>Family units centred on the selected person. Navigate earlier or later generations without loading the entire tree at once.</p></div>
    <div class='live-chart-direction'>Earlier generations ← &nbsp;&nbsp; Selected family &nbsp;&nbsp; → Later generations</div>
    {nav}<div class='family-unit-chart'>{''.join(sections)}</div>{nav}
    <div class='card live-chart-note'><strong>Family units</strong><p>Partners stay associated with the family they formed, and children remain beneath that family. Select any person to open their Person Story.</p></div>"""
