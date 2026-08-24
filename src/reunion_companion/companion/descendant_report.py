from __future__ import annotations

from pathlib import Path
import tempfile

from .publishing_v7 import CSS, esc, slug, default_report_dir
from .publication_themes import theme_css, DEFAULT_THEME
from .family_publication_model import (
    person, spouse_families, family_partners, children, life_dates
)
from .publishing_v11 import export_pdf_from_html
from .branding import publishing_mark_uri


REPORT_CSS = r"""
@page {
  size:A4 portrait;
  margin:16mm 15mm 18mm 15mm;
  @bottom-center { content:"Page " counter(page) " of " counter(pages); font-size:8pt; color:#666; }
}
@page:first { @bottom-center { content:none; } }

body { max-width:180mm; margin:0 auto; font-size:10.5pt; line-height:1.42; }
.descendant-report-title {
  min-height:235mm;
  display:flex;
  flex-direction:column;
  justify-content:center;
  text-align:center;
}
.descendant-report-title h1 { font-size:28pt; margin:0 0 3mm; border:0; }
.descendant-report-title .publishing-mark { width:28mm; height:28mm; object-fit:contain; margin:0 auto 6mm; display:block; }
.descendant-report-title h2 { font-size:16pt; margin:0 0 2mm; border:0; }
.descendant-report-title .report-depth { color:#666; }
.descendant-report-body { break-before:page; }
.descendant-report-body>h1 {
  font-size:20pt;
  margin:0 0 7mm;
  border-bottom:2px solid currentColor;
  padding-bottom:2mm;
}
.desc-family {
  margin:0 0 5mm;
  break-inside:auto;
}
.desc-family-header {
  break-inside:avoid;
  border-top:1px solid #888;
  padding-top:2.5mm;
  margin-top:2mm;
}
.desc-family.generation-1>.desc-family-header {
  border-top:2px solid currentColor;
  border-bottom:2px solid currentColor;
  padding:3mm 0;
}
.desc-generation {
  text-transform:uppercase;
  letter-spacing:.08em;
  font-size:8pt;
  color:#666;
  margin-bottom:1mm;
}
.desc-couple { font-size:12pt; line-height:1.35; }
.desc-couple .person-name { font-weight:700; }
.desc-life-dates { color:#666; font-size:9.2pt; }
.desc-marriage { color:#666; font-size:9pt; margin-top:.8mm; }
.desc-children {
  margin:2.5mm 0 0 7mm;
  padding-left:5mm;
  border-left:1px solid #aaa;
}
.desc-child {
  margin:0 0 3.5mm;
  break-inside:auto;
}
.desc-child-line { break-inside:avoid; }
.desc-child-marker {
  display:inline-block;
  width:5mm;
  color:#666;
}
.desc-unmarried { margin-left:5mm; }
.desc-subfamilies { margin:2mm 0 0 5mm; }
.desc-subfamilies>.desc-family { margin-bottom:3mm; }
.desc-generation-heading {
  font-size:9pt;
  font-weight:700;
  color:#555;
  margin:2mm 0 1mm;
}
.desc-empty { color:#666; font-style:italic; }
@media screen {
  body { padding:8mm 5mm 20mm; }
  .descendant-report-title { min-height:70vh; }
}
"""


def _date_text(db, pid):
    if not pid:
        return ""
    d=life_dates(db,pid)
    bits=[]
    if d["birth"]: bits.append("b. "+d["birth"])
    if d["death"]: bits.append("d. "+d["death"])
    return " · ".join(bits)


def _person_html(db, p):
    if not p:
        return ""
    dates=_date_text(db,p["id"])
    out="<span class='person-name'>"+esc(p["display_name"])+"</span>"
    if dates:
        out+=" <span class='desc-life-dates'>— "+esc(dates)+"</span>"
    return out


def _family_title(db, family_id):
    h,w=family_partners(db,family_id)
    names=[p["display_name"] for p in (h,w) if p]
    return " & ".join(names) if names else f"Family {family_id}"


def _choose_family(db, start_pid, family_id=None):
    if family_id is not None:
        fam=db.execute("SELECT * FROM families WHERE id=?",(family_id,)).fetchone()
        if not fam:
            raise ValueError(f"Family {family_id} was not found.")
        member=db.execute("""SELECT 1 FROM family_members
            WHERE family_id=? AND person_id=? AND lower(role) IN ('husband','wife','spouse')""",
            (family_id,start_pid)).fetchone()
        if not member:
            raise ValueError("The selected starting person is not a partner in that family.")
        return fam

    fams=spouse_families(db,start_pid)
    if len(fams)==1:
        return fams[0]
    if not fams:
        raise ValueError("The selected starting person has no recorded spouse family.")
    raise ValueError("The selected starting person belongs to more than one family; choose the starting family.")


def descendant_report_model(db,start_pid,generations=3,family_id=None):
    """Build the standalone descendant-report model.

    Generation 1 is the selected starting couple. Their children are Generation 2,
    grandchildren Generation 3, and so on. `generations` is intentionally bounded
    to 1..6 for the first report pass.
    """
    try:
        generations=int(generations)
    except Exception as e:
        raise ValueError("Generations must be a whole number from 1 to 6.") from e
    if not 1 <= generations <= 6:
        raise ValueError("Generations must be between 1 and 6.")

    start=person(db,start_pid)
    if not start:
        raise ValueError(f"Person {start_pid} was not found.")
    fam=_choose_family(db,start_pid,family_id)

    def family_node(fid,generation,path):
        if fid in path:
            return None
        h,w=family_partners(db,fid)
        f=db.execute("SELECT * FROM families WHERE id=?",(fid,)).fetchone()
        node={
            "family_id":fid,
            "generation":generation,
            "husband":h,
            "wife":w,
            "marriage_date":f["marriage_date"] if f else None,
            "marriage_place":f["marriage_place"] if f else None,
            "children":[],
        }
        if generation >= generations:
            return node
        for ch in children(db,fid):
            entry={"person":ch,"families":[]}
            for sf in spouse_families(db,ch["id"]):
                sub=family_node(sf["id"],generation+1,path|{fid})
                if sub:
                    entry["families"].append(sub)
            node["children"].append(entry)
        return node

    tree=family_node(fam["id"],1,set())
    return {
        "start_person":start,
        "start_family":fam,
        "generations":generations,
        "tree":tree,
        "title":_family_title(db,fam["id"]),
    }


def _marriage_html(node):
    bits=[x for x in (node.get("marriage_date"),node.get("marriage_place")) if x]
    return ("<div class='desc-marriage'>Marriage: "+esc(" — ".join(bits))+"</div>") if bits else ""


def _family_node_html(db,node):
    if not node:
        return ""
    gen=node["generation"]
    h,w=node["husband"],node["wife"]
    people=[_person_html(db,p) for p in (h,w) if p]
    couple=" <span class='couple-separator'>&amp;</span> ".join(people) if people else "Family"

    P=[f"<section class='desc-family generation-{gen}'>",
       "<div class='desc-family-header'>",
       f"<div class='desc-generation'>Generation {gen}</div>",
       f"<div class='desc-couple'>{couple}</div>",
       _marriage_html(node),
       "</div>"]

    if node["children"]:
        P.append("<div class='desc-children'>")
        for child in node["children"]:
            p=child["person"]
            P.append("<div class='desc-child'>")
            P.append("<div class='desc-child-line'><span class='desc-child-marker'>└─</span>"+_person_html(db,p)+"</div>")
            if child["families"]:
                P.append("<div class='desc-subfamilies'>")
                for fam in child["families"]:
                    P.append(_family_node_html(db,fam))
                P.append("</div>")
            P.append("</div>")
        P.append("</div>")
    elif gen == 1:
        P.append("<p class='desc-empty'>No children are recorded for this family.</p>")
    P.append("</section>")
    return "".join(P)


def descendant_report_html(db,start_pid,generations=3,family_id=None,theme=DEFAULT_THEME):
    model=descendant_report_model(db,start_pid,generations,family_id)
    title=model["title"]
    depth=model["generations"]
    body=_family_node_html(db,model["tree"])
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{esc(title)} — Descendant Report</title>"
        f"<style>{CSS}{REPORT_CSS}{theme_css(theme)}</style></head><body>"
        "<section class='descendant-report-title'>"
        f"<img class='publishing-mark' src='{publishing_mark_uri()}' alt='Reunion Companion'>"
        "<div class='chapter-kicker'>Reunion Companion</div>"
        "<h1>Descendant Report</h1>"
        f"<h2>{esc(title)}</h2>"
        f"<p class='report-depth'>{depth} generation{'s' if depth != 1 else ''}</p>"
        "</section>"
        "<section class='descendant-report-body'>"
        f"<h1>{esc(title)}</h1>{body}</section>"
        "</body></html>"
    )


def write_descendant_report(db,start_pid,path=None,generations=3,family_id=None,theme=DEFAULT_THEME):
    model=descendant_report_model(db,start_pid,generations,family_id)
    p=Path(path).expanduser() if path else default_report_dir()/(slug(model["title"])+"_Descendant_Report.html")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(descendant_report_html(db,start_pid,generations,family_id,theme),encoding="utf-8")
    return p


def write_descendant_report_pdf(db,start_pid,path=None,generations=3,family_id=None,theme=DEFAULT_THEME):
    model=descendant_report_model(db,start_pid,generations,family_id)
    pdf=Path(path).expanduser() if path else default_report_dir()/(slug(model["title"])+"_Descendant_Report.pdf")
    pdf.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="reunion-companion-descendants-") as td:
        html=Path(td)/(pdf.stem+".html")
        write_descendant_report(db,start_pid,html,generations,family_id,theme)
        export_pdf_from_html(html,pdf)
    return pdf
