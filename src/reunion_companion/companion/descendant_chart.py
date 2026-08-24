from __future__ import annotations
from .publishing_v7 import esc
from .family_publication_model import family_context_chart,life_dates,family_partners


def _person_line(db,p):
    if not p:return ""
    d=life_dates(db,p["id"])
    bits=[p["display_name"]]
    span=[]
    if d["birth"]:span.append("b. "+d["birth"])
    if d["death"]:span.append("d. "+d["death"])
    if span:bits.append(" · ".join(span))
    return " — ".join(bits)


def _person_html(db,p):
    if not p:return ""
    d=life_dates(db,p["id"]); dates=[]
    if d["birth"]:dates.append("b. "+d["birth"])
    if d["death"]:dates.append("d. "+d["death"])
    suffix=(" <span class='person-dates'>— "+esc(" · ".join(dates))+"</span>") if dates else ""
    return "<strong class='person-name'>"+esc(p["display_name"])+"</strong>"+suffix


def _named_person_html(db,name,pid=None,birth=None,death=None):
    dates=[]
    if pid:
        d=life_dates(db,pid)
        if d["birth"]:dates.append("b. "+d["birth"])
        if d["death"]:dates.append("d. "+d["death"])
    else:
        if birth:dates.append("b. "+birth)
        if death:dates.append("d. "+death)
    suffix=(" <span class='person-dates'>— "+esc(" · ".join(dates))+"</span>") if dates else ""
    return "<strong class='person-name'>"+esc(name)+"</strong>"+suffix


def _birth_family(db,pid):
    return db.execute("""SELECT f.* FROM families f JOIN family_members fm ON fm.family_id=f.id
        WHERE fm.person_id=? AND lower(fm.role)='child' ORDER BY f.id LIMIT 1""",(pid,)).fetchone()


def direct_ancestor_couples(db,pid,max_generations=6):
    """Direct parent-couple ancestry above ``pid``'s immediate parents.

    The person's immediate parents are displayed separately by the master chart.
    This returns grandparents and older direct parent couples, oldest first,
    following the recorded father at each generation and never opening collateral
    families.
    """
    if not pid:return []
    immediate=_birth_family(db,pid)
    if not immediate:return []
    father,_=family_partners(db,immediate['id'])
    if not father:return []
    out=[];current=father;seen={pid}
    for _ in range(max_generations):
        if current['id'] in seen:break
        seen.add(current['id'])
        fam=_birth_family(db,current['id'])
        if not fam:break
        h,w=family_partners(db,fam['id'])
        if not h and not w:break
        out.append({'family':fam,'husband':h,'wife':w})
        if not h:break
        current=h
    out.reverse()
    return out


def paternal_ancestor_couples(db,pid,max_generations=6):
    """Compatibility wrapper for the husband's direct ancestral couple line."""
    return direct_ancestor_couples(db,pid,max_generations)


def _couple_html(db,h,w):
    people=[_person_html(db,p) for p in (h,w) if p]
    return " <span class='couple-separator'>&amp;</span> ".join(people)


def chart_text(db,husband_id,wife_id,generations=3):
    c=family_context_chart(db,husband_id,wife_id,generations)
    L=["Family & Descendants","============================",""]
    for label,pid in (("Husband's Descendants",husband_id),("Wife's Descendants",wife_id)):
        ancestors=direct_ancestor_couples(db,pid)
        if ancestors:
            L.append(label)
            for a in ancestors:
                names=[_person_line(db,p) for p in (a['husband'],a['wife']) if p]
                L.append("  " + " & ".join(names))
            L.append("")
    if c["husband_parents"]:
        L.append("Husband's parents")
        for p in c["husband_parents"]:L.append("  "+_person_line(db,p))
        L.append("")
    if c["wife_parents"]:
        L.append("Wife's parents")
        for p in c["wife_parents"]:L.append("  "+_person_line(db,p))
        L.append("")
    if c["husband"] or c["wife"]:
        L.append("Family")
        if c["husband"]:L.append("  "+_person_line(db,c["husband"]))
        if c["wife"]:L.append("  "+_person_line(db,c["wife"]))
        L.append("")
    L.append("Descendants")
    for r in c["descendants"]:
        prefix="  "+"    "*r["level"]+("└─ " if r["level"] else "")
        dates=[]
        if r["birth"]:dates.append("b. "+r["birth"])
        if r["death"]:dates.append("d. "+r["death"])
        sp = " & " + " & ".join(x["name"] for x in r.get("spouses",[])) if r.get("spouses") else ""
        L.append(prefix+r["name"]+sp+(" — "+" · ".join(dates) if dates else ""))
    return "\n".join(L)


def _lineage_html(db,label,pid,css_class,max_generations):
    ancestors=direct_ancestor_couples(db,pid,max_generations)
    P=[f"<div class='lineage-side {css_class} tree'><h3>{esc(label)}</h3>"]
    if ancestors:
        for a in ancestors:
            P.append("<div class='tree-row lineage-couple'>"+_couple_html(db,a['husband'],a['wife'])+"</div>")
    else:
        P.append("<p class='small'>No earlier direct line recorded</p>")
    P.append("</div>")
    return "".join(P)


def chart_html(db,husband_id,wife_id,generations=3,title="Family & Descendants",paternal_generations=6,show_terminal_spouses=True):
    """Master family-chart presentation used for both main and spouse charts."""
    c=family_context_chart(db,husband_id,wife_id,generations)
    P=["<section class='descendant-chart family-descendant-chart'><h2>"+esc(title)+"</h2>"]

    husband_line=_lineage_html(db,"Husband's Descendants",husband_id,"husband-descendants",paternal_generations)
    wife_line=_lineage_html(db,"Wife's Descendants",wife_id,"wife-descendants",paternal_generations)
    P.append("<div class='dual-lineage unified-lineage'>")
    P.append(husband_line)
    P.append(wife_line)
    P.append("</div>")

    P.append("<div class='parent-context unified-parent-context'>")
    for label,parents in (("Husband's parents",c["husband_parents"]),("Wife's parents",c["wife_parents"])):
        P.append(f"<div><h3>{esc(label)}</h3>")
        if parents:
            for parent in parents:P.append("<p class='person-line'>"+_person_html(db,parent)+"</p>")
        else:P.append("<p class='small'>Not recorded</p>")
        P.append("</div>")
    P.append("</div>")
    if c["husband"] or c["wife"]:
        P.append("<div class='family-central-family'><h3>Family</h3>")
        if c["husband"]:P.append("<p class='person-line'><strong>Husband:</strong> "+_person_html(db,c["husband"])+"</p>")
        if c["wife"]:P.append("<p class='person-line'><strong>Wife:</strong> "+_person_html(db,c["wife"])+"</p>")
        P.append("</div>")
    P.append("<div class='family-descendants'><h3>Descendants</h3><div class='tree'>")
    for r in c["descendants"]:
        primary=_named_person_html(db,r["name"],r.get("id"),r.get("birth"),r.get("death"))
        visible_spouses=r.get("spouses",[]) if (show_terminal_spouses or r["level"]<generations) else []
        spouses=[_named_person_html(db,sp["name"],sp.get("id")) for sp in visible_spouses]
        couple=primary + ((" <span class='couple-separator'>&amp;</span> "+" <span class='couple-separator'>&amp;</span> ".join(spouses)) if spouses else "")
        P.append(f"<div class='tree-row level-{min(r['level'],8)}'>{couple}</div>")
    P.append("</div></div></section>")
    return "".join(P)
