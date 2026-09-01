from __future__ import annotations
from pathlib import Path
import html,shutil,re
from .publishing_v7 import CSS,esc,slug,default_report_dir
from .publishing_v8 import _embedded_image_uri
from .publication_themes import theme_css,DEFAULT_THEME
from .family_publication_model import (
    family_overview,family_partners,children,life_dates,person_events,person_notes,
    person_document_groups,person_sources,family_sources,family_media,
    resolve_family_for_people,spouse_families,media_kind
)
from .story_engine import story_sections
from .descendant_chart import chart_html,chart_text

BOOK_CSS="""
@page { size:A4; margin:16mm 15mm 18mm 15mm; }
body { max-width:180mm; margin:0 auto; font-size:10pt; line-height:1.36; }
h1 { font-size:22pt; margin:0 0 3.5mm; padding-bottom:1.8mm; }
h2 { font-size:14pt; margin:5.5mm 0 2.5mm; border-bottom:1px solid #aaa; padding-bottom:.8mm; page-break-after:avoid; }
h3 { font-size:11pt; margin:3.2mm 0 1.2mm; page-break-after:avoid; }
p { margin:2.2mm 0; }
ul { padding-left:6mm; }
li { margin:1mm 0; }
.pagebreak { break-before:page; page-break-before:always; }
.keep { break-inside:avoid; }
.overview-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin:4mm 0; }
.overview-item { border:1px solid #ccc; padding:3mm; }
.overview-item strong { display:block; font-size:13pt; }
.hero { text-align:center; margin:5mm auto 7mm; break-inside:avoid; }
.hero img { max-width:165mm; max-height:125mm; object-fit:contain; }
.document-page { break-before:page; text-align:center; }
.document-page img { max-width:175mm; max-height:245mm; object-fit:contain; }
.document-card { border:1px solid #ccc; padding:4mm; margin:3mm 0; break-inside:avoid; }
.document-card img { max-width:75mm; max-height:80mm; float:right; margin-left:4mm; object-fit:contain; }
.clear { clear:both; }
.person-summary { border:1px solid #bbb; padding:4mm; margin:3mm 0 5mm; }
.person-topic { margin:0 0 4mm; break-inside:avoid; }
.person-topic:last-child { margin-bottom:0; }
.person-topic h3 { margin:0 0 1mm; font-size:11pt; }
.person-topic p { margin:0; }
.note { white-space:pre-wrap; }
.parent-context { display:grid; grid-template-columns:1fr 1fr; gap:5mm; }
.tree { margin-top:3mm; }
.tree-row { padding:1mm 0; border-bottom:1px dotted #ddd; }
.tree-row span { margin-left:3mm; color:#555; font-size:9pt; }
.level-1 { padding-left:8mm; } .level-2 { padding-left:16mm; } .level-3 { padding-left:24mm; }
.level-4 { padding-left:32mm; } .level-5 { padding-left:40mm; } .level-6 { padding-left:48mm; }
.level-7 { padding-left:56mm; } .level-8 { padding-left:64mm; }
.sources li { break-inside:avoid; }
.small { font-size:8.5pt; color:#666; overflow-wrap:anywhere; }
.research-only { display:none; }
@media print { a { color:#222; text-decoration:none; } }
"""

def _safe_asset_name(path,media_id=None):
    p=Path(path)
    name=re.sub(r"[^A-Za-z0-9._ -]+","_",p.name).strip() or f"media_{media_id or 'item'}"
    return f"{media_id}_{name}" if media_id is not None else name

def _copy_document_asset(path,output_html=None,media_id=None):
    p=Path(path).expanduser()
    if output_html is None or not p.is_file():
        return None
    output_html=Path(output_html).expanduser()
    assets=output_html.parent/(output_html.stem+"_assets")
    assets.mkdir(parents=True,exist_ok=True)
    target=assets/_safe_asset_name(p,media_id)
    try:
        if not target.exists() or target.stat().st_size != p.stat().st_size:
            shutil.copy2(p,target)
    except OSError:
        return None
    return f"{assets.name}/{target.name}"

def _file_link(path,output_html=None,media_id=None):
    rel=_copy_document_asset(path,output_html,media_id)
    if rel:
        return rel
    p=Path(path).expanduser()
    try:return p.resolve().as_uri() if p.exists() else None
    except OSError:return None

def _source_text(s):
    return s["display_text"] or s["text"] or s["title"] or "(undescribed source)"

def _media_title(m):
    return m["title"] or Path(m["file_path"]).name

def _media_figure(m,hero=False,document_page=False,output_html=None):
    title=_media_title(m);uri=_embedded_image_uri(m["file_path"])
    if uri:
        cls="document-page" if document_page else "hero" if hero else "document-card"
        return f"<div class='{cls}'><img src='{esc(uri)}' alt='{esc(title)}'><p><strong>{esc(title)}</strong></p></div>"
    href=_file_link(m["file_path"],output_html,m["id"])
    status="Available" if m["exists_on_disk"] else "Missing"
    ext=Path(m["file_path"]).suffix.upper().lstrip(".") or "FILE"
    link=f" <a href='{esc(href)}'>Open {esc(ext)}</a>" if href else ""
    return (f"<div class='document-card'><strong>{esc(title)}</strong>"
            f"<p>{esc(ext)} · {esc(status)}{link}</p>"
            f"<div class='small'>{esc(m['file_path'])}</div></div>")

def _person_summary_html(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    dates=life_dates(db,pid)
    events=person_events(db,pid)
    occ=next((e["value_text"] for e in events if e["event_type"]=="Occupation" and e["value_text"]),None)
    edu=next((e["value_text"] for e in events if e["event_type"]=="Education" and e["value_text"]),None)
    rel=next((e["value_text"] for e in events if e["event_type"]=="Religion" and e["value_text"]),None)
    rows=[
      ("Born"," — ".join(x for x in (dates["birth"],dates["birth_place"]) if x)),
      ("Died"," — ".join(x for x in (dates["death"],dates["death_place"]) if x)),
      ("Occupation",occ),("Education",edu),("Religion",rel)
    ]
    P=[f"<section class='person-summary'><h2>{esc(p['display_name'])}</h2>"]
    for label,val in rows:
        if val:
            P.append(f"<div class='person-topic'><h3>{esc(label)}</h3><p>{esc(val)}</p></div>")
    P.append("</section>")
    return "".join(P)

def _person_page_html(db,pid,output_html=None):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    groups=person_document_groups(db,pid)
    P=["<div class='pagebreak'></div>",_person_summary_html(db,pid)]

    # Portrait before narrative if one exists.
    if groups["portrait"]:
        P.append(_media_figure(groups["portrait"][0],hero=True,output_html=output_html))

    P.append("<h2>Life &amp; Notes</h2>")
    story=story_sections(db,pid)
    if story:
        for heading,text in story:
            P.append(f"<h3>{esc(heading)}</h3><p class='note'>{esc(text)}</p>")
    else:
        P.append("<p>No narrative notes are recorded.</p>")

    # Documents deliberately follow the person's main page, matching the established book pattern.
    ordered=(("birth","Birth Documents"),("death","Death & Burial Documents"),
             ("military","Military Documents"),("other-documents","Other Documents"))
    for key,label in ordered:
        if groups[key]:
            P.append(f"<h2>{esc(label)}</h2>")
            for m in groups[key]:
                # Image certificates can occupy most of a page. PDFs appear as document cards/links.
                P.append(_media_figure(m,document_page=(Path(m["file_path"]).suffix.lower() in (".jpg",".jpeg",".png",".gif",".webp")),output_html=output_html))
    if groups["other-photos"]:
        P.append("<h2>Other Photographs</h2>")
        for m in groups["other-photos"]:P.append(_media_figure(m,output_html=output_html))
    if groups["legacy"]:
        P.append("<h2>Legacy Media</h2>")
        for m in groups["legacy"]:
            P.append(_media_figure(m,output_html=output_html))
            P.append("<p class='small'>Legacy media identified for later conversion; original not modified by Companion.</p>")
    return "".join(P)

def _family_intro(db,family_id):
    o=family_overview(db,family_id);f=o["family"];h=o["husband"];w=o["wife"]
    names=" and ".join(x["display_name"] for x in (h,w) if x)
    P=[f"<div class='chapter-kicker'>Family Chapter</div><h1>{esc(names or f['gedcom_xref'] or 'Family')}</h1>",
       "<section class='overview'><h2>Family Overview</h2><div class='overview-grid'>"]
    stats=[
      ("Marriage",f["marriage_date"] or "Not recorded"),
      ("Children",o["children_count"]),
      ("Known descendants",o["known_descendants"]),
      ("Media",o["media_count"]),
      ("Sources",o["source_count"]),
      ("Family ID",f["gedcom_xref"] or f["id"]),
    ]
    for label,val in stats:
        P.append(f"<div class='overview-item'><span>{esc(label)}</span><strong>{esc(val)}</strong></div>")
    P.append("</div>")
    if f["marriage_place"]:P.append(f"<p><strong>Marriage place:</strong> {esc(f['marriage_place'])}</p>")
    P.append("</section>")

    # Conservative deterministic introduction.
    if h and w:
        intro=f"{h['display_name']} and {w['display_name']}"
        if f["marriage_date"]:intro+=f" were married on {f['marriage_date']}"
        else:intro+=" are recorded as a family"
        if f["marriage_place"]:intro+=f" at {f['marriage_place']}"
        intro+="."
        if o["children_count"]:
            intro+=f" The imported Reunion family records {o['children_count']} child{'ren' if o['children_count']!=1 else ''}."
        P.append(f"<h2>About This Family</h2><p>{esc(intro)}</p>")
    return "".join(P)

def family_chapter_html(db,family_id,theme=DEFAULT_THEME,descendant_generations=4,include_research=False,output_html=None):
    o=family_overview(db,family_id);h=o["husband"];w=o["wife"];f=o["family"]
    title=" and ".join(x["display_name"] for x in (h,w) if x) or (f["gedcom_xref"] or f"Family {family_id}")
    P=["<!doctype html><html><head><meta charset='utf-8'>",
       f"<title>{esc(title)} — Family Chapter</title>",
       f"<style>{CSS}{BOOK_CSS}{theme_css(theme)}</style></head><body>",
       _family_intro(db,family_id)]

    # Dad-style marriage section: wedding image then marriage certificate/document.
    if o["wedding_photos"] or o["marriage_documents"] or f["marriage_date"] or f["marriage_place"]:
        P.append("<h2>Marriage</h2>")
        if f["marriage_date"] or f["marriage_place"]:
            P.append("<p>"+" — ".join(esc(x) for x in (f["marriage_date"],f["marriage_place"]) if x)+"</p>")
        for m in o["wedding_photos"]:
            P.append(_media_figure(m,hero=True,output_html=output_html))
        for m in o["marriage_documents"]:
            P.append(_media_figure(m,document_page=Path(m["file_path"]).suffix.lower() in (".jpg",".jpeg",".png",".gif",".webp"),output_html=output_html))

    if h:P.append(_person_page_html(db,h["id"],output_html))
    if w:P.append(_person_page_html(db,w["id"],output_html))

    # Family-only media not already surfaced as wedding/marriage.
    surfaced={m["id"] for m in o["wedding_photos"]+o["marriage_documents"]}
    fm=[m for m in family_media(db,family_id) if m["id"] not in surfaced]
    if fm:
        P.append("<div class='pagebreak'></div><h2>Family Documents &amp; Media</h2>")
        for m in fm:P.append(_media_figure(m,output_html=output_html))

    P.append(chart_html(db,h["id"] if h else None,w["id"] if w else None,descendant_generations))

    if include_research:
        P.append("<section class='research-only'><h2>Research Edition Notes</h2>")
        P.append("<p>Research confidence, gaps and audit material are available from Foundation 9's profile, confidence and audit commands. This family-book template keeps them separate from the main narrative unless Research Edition is selected.</p></section>")

    P.append("<p class='small'>Generated from the current Reunion Companion snapshot. The chapter composition is deterministic; authored Reunion notes are preserved and no unsupported family-history facts are invented.</p>")
    P.append("</body></html>")
    return "".join(P)

def write_family_chapter(db,family_id,path=None,theme=DEFAULT_THEME,descendant_generations=4):
    o=family_overview(db,family_id);h=o["husband"];w=o["wife"]
    name="_and_".join(slug(x["display_name"]) for x in (h,w) if x) or f"Family_{family_id}"
    p=Path(path).expanduser() if path else default_report_dir()/(name+"_Family_Chapter.html")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(family_chapter_html(db,family_id,theme,descendant_generations,theme=="Research Edition",p),encoding="utf-8")
    return p

def preview_family(db,family_id):
    o=family_overview(db,family_id);h=o["husband"];w=o["wife"];f=o["family"]
    title="Family Chapter Preview";L=[title,"="*len(title),""]
    L.append("Couple: "+" and ".join(x["display_name"] for x in (h,w) if x))
    L.append(f"Marriage: {f['marriage_date'] or 'not recorded'}"+(f" — {f['marriage_place']}" if f["marriage_place"] else ""))
    L.append(f"Children: {o['children_count']}")
    L.append(f"Known descendants: {o['known_descendants']}")
    L.append(f"Wedding photographs selected: {len(o['wedding_photos'])}")
    L.append(f"Marriage documents selected: {len(o['marriage_documents'])}")
    if h:
        g=person_document_groups(db,h["id"])
        L.append(f"{h['display_name']}: {sum(len(v) for v in g.values())} person media items")
    if w:
        g=person_document_groups(db,w["id"])
        L.append(f"{w['display_name']}: {sum(len(v) for v in g.values())} person media items")
    L += ["","Chapter order","-------------",
          "1. Family introduction / overview",
          "2. Wedding photograph(s), when identified",
          "3. Marriage certificate/document(s), when identified",
          "4. Husband person page + individual documents",
          "5. Wife person page + individual documents",
          "6. Other family documents/media",
          "7. Children",
          "8. Family context & descendant chart",
          "9. Consolidated chapter sources"]
    return "\n".join(L)

def descendant_chart_html_document(db,husband_id,wife_id,path=None,generations=4,theme=DEFAULT_THEME):
    h=db.execute("SELECT display_name FROM people WHERE id=?",(husband_id,)).fetchone() if husband_id else None
    w=db.execute("SELECT display_name FROM people WHERE id=?",(wife_id,)).fetchone() if wife_id else None
    title=" & ".join(x["display_name"] for x in (h,w) if x) or "Family"
    body=f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(title)} Descendant Chart</title><style>{CSS}{BOOK_CSS}{theme_css(theme)}</style></head><body>{chart_html(db,husband_id,wife_id,generations)}</body></html>"
    p=Path(path).expanduser() if path else default_report_dir()/(slug(title)+"_Descendant_Chart.html")
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body,encoding="utf-8");return p

def book_family_ids(db,start_pid,generations=4):
    """Choose spouse families descending from a start person, de-duplicated by family ID."""
    out=[];seen_people=set();seen_fam=set()
    def walk(pid,level):
        if level>generations or pid in seen_people:return
        seen_people.add(pid)
        for f in spouse_families(db,pid):
            if f["id"] not in seen_fam:
                seen_fam.add(f["id"]);out.append(f["id"])
            for ch in children(db,f["id"]):
                walk(ch["id"],level+1)
    walk(start_pid,0)
    return out

def book_html(db,start_pid,generations=4,theme=DEFAULT_THEME,output_html=None):
    start=db.execute("SELECT * FROM people WHERE id=?",(start_pid,)).fetchone()
    fam_ids=book_family_ids(db,start_pid,generations)
    P=["<!doctype html><html><head><meta charset='utf-8'>",
       f"<title>{esc(start['display_name'])} — Family History</title>",
       f"<style>{CSS}{BOOK_CSS}{theme_css(theme)} .book-chapter{{break-before:page}}</style></head><body>",
       "<section class='title-page'><h1>Family History</h1>",
       f"<h2>{esc(start['display_name'])} and Descendants</h2>",
       f"<p>{len(fam_ids)} family chapter{'s' if len(fam_ids)!=1 else ''} assembled.</p></section>"]
    for i,fid in enumerate(fam_ids,1):
        chapter=family_chapter_html(db,fid,theme,generations,theme=="Research Edition",output_html)
        # extract body only for composition.
        if "<body>" in chapter:
            chapter=chapter.split("<body>",1)[1].rsplit("</body>",1)[0]
        P.append(f"<section class='book-chapter'><div class='chapter-kicker'>Chapter {i}</div>{chapter}</section>")
    P.append("</body></html>")
    return "".join(P)

def write_book(db,start_pid,path=None,generations=4,theme=DEFAULT_THEME):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(start_pid,)).fetchone()["display_name"]
    p=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Family_History_Book.html")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(book_html(db,start_pid,generations,theme,p),encoding="utf-8")
    return p
