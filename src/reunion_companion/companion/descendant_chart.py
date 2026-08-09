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

def chart_text(db,husband_id,wife_id,generations=3):
    c=family_context_chart(db,husband_id,wife_id,generations)
    L=["Family Context & Descendants","============================",""]
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
        L.append(prefix+r["name"]+(" — "+" · ".join(dates) if dates else ""))
    return "\n".join(L)

def chart_html(db,husband_id,wife_id,generations=3):
    c=family_context_chart(db,husband_id,wife_id,generations)
    P=["<section class='descendant-chart'><h2>Family Context &amp; Descendants</h2>"]
    P.append("<div class='parent-context'>")
    for label,parents in (("Husband's parents",c["husband_parents"]),("Wife's parents",c["wife_parents"])):
        P.append(f"<div><h3>{esc(label)}</h3>")
        if parents:
            for p in parents:P.append(f"<p>{esc(_person_line(db,p))}</p>")
        else:P.append("<p class='small'>Not recorded</p>")
        P.append("</div>")
    P.append("</div>")
    P.append("<h3>Descendants</h3><div class='tree'>")
    for r in c["descendants"]:
        dates=[]
        if r["birth"]:dates.append("b. "+r["birth"])
        if r["death"]:dates.append("d. "+r["death"])
        P.append(f"<div class='tree-row level-{min(r['level'],8)}'><strong>{esc(r['name'])}</strong>"
                 + (f"<span>{esc(' · '.join(dates))}</span>" if dates else "") + "</div>")
    P.append("</div></section>")
    return "".join(P)
