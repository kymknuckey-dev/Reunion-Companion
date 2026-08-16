from __future__ import annotations
from .publishing_v7 import esc
from .family_publication_model import family_context_chart,life_dates

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

def chart_text(db,husband_id,wife_id,generations=3):
    c=family_context_chart(db,husband_id,wife_id,generations)
    L=["Family & Descendants","============================",""]
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

def chart_html(db,husband_id,wife_id,generations=3):
    c=family_context_chart(db,husband_id,wife_id,generations)
    P=["<section class='descendant-chart'><h2>Family &amp; Descendants</h2>","<div class='parent-context'>"]
    for label,parents in (("Husband's parents",c["husband_parents"]),("Wife's parents",c["wife_parents"])):
        P.append(f"<div><h3>{esc(label)}</h3>")
        if parents:
            for parent in parents:P.append("<p class='person-line'>"+_person_html(db,parent)+"</p>")
        else:P.append("<p class='small'>Not recorded</p>")
        P.append("</div>")
    P.append("</div>")
    if c["husband"] or c["wife"]:
        P.append("<h3>Family</h3>")
        if c["husband"]:P.append("<p class='person-line'><strong>Husband:</strong> "+_person_html(db,c["husband"])+"</p>")
        if c["wife"]:P.append("<p class='person-line'><strong>Wife:</strong> "+_person_html(db,c["wife"])+"</p>")
    P.append("<h3>Descendants</h3><div class='tree'>")
    for r in c["descendants"]:
        primary=_named_person_html(db,r["name"],r.get("id"),r.get("birth"),r.get("death"))
        spouses=[_named_person_html(db,sp["name"],sp.get("id")) for sp in r.get("spouses",[])]
        couple=primary + ((" <span class='couple-separator'>&amp;</span> "+" <span class='couple-separator'>&amp;</span> ".join(spouses)) if spouses else "")
        P.append(f"<div class='tree-row level-{min(r['level'],8)}'>{couple}</div>")
    P.append("</div></section>")
    return "".join(P)
