from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import re
from .publishing_v7 import CSS,esc,slug,default_report_dir
from .publishing_v8 import _embedded_image_uri
from .publication_themes import theme_css,DEFAULT_THEME
from .family_publication_model import (
    family_overview,family_partners,children,life_dates,person_events,
    person_document_groups,person_sources,family_sources,family_media,
    spouse_families,resolve_family_for_people,person_media
)
from .story_engine import story_sections
from .publication_narrative import publication_narrative, preserve_note_layout
from .descendant_chart import chart_html
from .document_renderer import render_pdf,copy_original,pdf_render_capability

PRO_CSS=r"""
@page {
  size:A4 portrait;
  margin:16mm 15mm 18mm 15mm;
  @bottom-center { content:"Page " counter(page) " of " counter(pages); font-size:8pt; color:#666; }
}
@page:first { @bottom-center { content:none; } }

html { scroll-behavior:smooth; }
body { max-width:180mm; margin:0 auto; font-size:10.5pt; line-height:1.45; }
h1 { font-size:24pt; margin:0 0 4mm; padding-bottom:2mm; }
h2 { font-size:15pt; margin:7mm 0 3mm; border-bottom:1px solid #aaa; padding-bottom:1mm; page-break-after:avoid; }
h3 { font-size:11.5pt; margin:4mm 0 1.5mm; page-break-after:avoid; }
p { margin:2.2mm 0; }
a { color:inherit; }
.pagebreak { break-before:page; page-break-before:always; }
.keep { break-inside:avoid; }
.title-page { min-height:245mm; display:flex; flex-direction:column; justify-content:center; text-align:center; }
.title-page h1 { border:0; font-size:30pt; }
.chapter { break-before:page; }
.couple-title { text-align:center; }
.couple-title span { display:block; }
.couple-title .couple-and { font-size:.55em; font-weight:normal; margin:.08em 0; }
.chapter-kicker { text-align:center; text-transform:uppercase; letter-spacing:.12em; font-size:8.5pt; }
.overview-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin:4mm 0; }
.overview-item { border:1px solid #ccc; padding:3mm; }
.overview-item strong { display:block; font-size:13pt; }
.hero { text-align:center; margin:5mm auto 7mm; break-inside:avoid; }
.hero img {
  width:auto;
  height:auto;
  max-width:min(100%, 1100px);
  max-height:70vh;
  object-fit:contain;
}
.media-card {
  border:0;
  padding:0;
  margin:5mm 0 7mm;
  text-align:center;
  break-inside:avoid;
}
.media-card img {
  display:block;
  width:auto;
  height:auto;
  max-width:100%;
  margin:0 auto 2mm;
  object-fit:contain;
}
.media-card.media-landscape img,
.media-card.media-portrait img,
.media-card.media-square img,
.media-card.hero img {
  width:auto;
  max-width:100%;
  height:auto;
  max-height:none;
}
.media-card figcaption { margin-top:2mm; }
.person-summary { border:0; padding:0; margin:3mm 0 5mm; }
.person-topic { margin:0 0 4mm; break-inside:avoid; }
.person-topic:last-child { margin-bottom:0; }
.person-topic h3 { margin:0 0 1mm; font-size:11pt; }
.person-topic p { margin:0; }
.note { white-space:pre-wrap; }
.life-topic {
  margin:0 0 5mm;
  padding:0 0 3mm;
  border-bottom:1px solid #ddd;
}
.life-topic:last-child { border-bottom:0; }
.life-topic h3 {
  margin:0 0 1.5mm;
  font-size:11.5pt;
}
.life-topic .note {
  margin:0;
  white-space:pre-wrap;
}
.document-card { border:0; padding:0; margin:4mm 0; break-inside:avoid; }
.document-card .preview { text-align:center; margin:2mm 0; }
.document-card .preview img {
  width:auto;
  height:auto;
  max-width:100%;
  max-height:75vh;
  object-fit:contain;
}
.document-card .meta { font-size:8.5pt; color:#666; overflow-wrap:anywhere; }
.document-card .open-original { display:inline-block; margin-top:2mm; font-weight:bold; }
.pdf-web-plate {
  margin:4mm 0 7mm;
  padding:0;
  border:0;
  text-align:center;
}
.pdf-web-plate .preview {
  width:100%;
  margin:0 auto 2mm;
}
.pdf-web-plate .preview img {
  display:block;
  width:auto;
  height:auto;
  max-width:100%;
  max-height:82vh;
  margin:0 auto;
  object-fit:contain;
}
.pdf-web-plate .pdf-caption {
  margin:2mm auto 0;
  font-size:9pt;
}
.archive-page {
  display:none;
  break-before:page;
  page-break-before:always;
  height:258mm;
  position:relative;
  text-align:center;
  overflow:hidden;
}
.archive-page .archive-title { position:absolute; top:0; left:0; right:0; font-size:9pt; font-weight:bold; }
.archive-page .archive-caption { position:absolute; bottom:0; left:0; right:0; font-size:8pt; color:#555; }
.archive-page .doc-preview { position:absolute; left:50%; top:50%; object-fit:contain; }
.archive-page.portrait .doc-preview {
  max-width:174mm; max-height:240mm;
  transform:translate(-50%,-50%);
}
.archive-page.landscape .doc-preview {
  width:238mm; max-height:172mm;
  transform:translate(-50%,-50%) rotate(90deg);
}
.parent-context { display:grid; grid-template-columns:1fr 1fr; gap:5mm; }
.tree { margin-top:3mm; }
.tree-row { padding:1mm 0; border-bottom:1px dotted #ddd; }
.tree-row span { margin-left:3mm; color:#555; font-size:9pt; }
.level-1 { padding-left:8mm; } .level-2 { padding-left:16mm; } .level-3 { padding-left:24mm; }
.level-4 { padding-left:32mm; } .level-5 { padding-left:40mm; } .level-6 { padding-left:48mm; }
.level-7 { padding-left:56mm; } .level-8 { padding-left:64mm; }
.source-ref { display:inline-block; min-width:12mm; font-weight:bold; }
.sources li { margin:1.5mm 0; break-inside:avoid; }
.toc ul { list-style:none; padding:0; }
.toc li { margin:1.4mm 0; }
.toc a { text-decoration:none; }
.index-list { columns:2; column-gap:8mm; }
.index-entry { break-inside:avoid; margin:1mm 0; }
.small { font-size:8.5pt; color:#666; }
.web-only { display:block; }
.print-only { display:none; }

@media screen {
  body { padding:8mm 5mm 20mm; }
  .pdf-extra-page { display:none; }
}

@media print {
  a { color:#222; text-decoration:none; }
  .web-only { display:none !important; }
  .print-only { display:block; }
  .archive-page { display:block !important; }
  .pdf-extra-page { display:block !important; }
  .toc a::after {
    content: leader(".") target-counter(attr(href), page);
    float:right;
  }
  .index-entry a::after {
    content:" .... " target-counter(attr(href), page);
  }
}
"""

def source_number(source):
    x=source["gedcom_xref"] or ""
    m=re.fullmatch(r"@S(\d+)@",x,re.I)
    if m:return m.group(1)
    m=re.search(r"(\d+)",x)
    return m.group(1) if m else str(source["id"])

def source_label(source):
    return f"[{source_number(source)}]"

def source_text(source):
    return source["display_text"] or source["text"] or source["title"] or "(undescribed source)"

def media_title(m):
    return m["title"] or Path(m["file_path"]).name

def _clean_document_title(title,person_name=None,family_names=None):
    """Turn filename-like titles into book-friendly captions without inventing facts."""
    t=(title or "").strip()
    t=re.sub(r"\.(pdf|jpe?g|png|gif|webp)$","",t,flags=re.I)
    # Remove repeated subject names from the front when safely identifiable.
    for name in (person_name,family_names):
        if name and t.lower().startswith(name.lower()):
            t=t[len(name):].lstrip(" ,-–—")
            break
    # Prefer familiar document-role wording if already present in title.
    roles=[
        "Marriage Certificate","Wedding Certificate","Birth Certificate",
        "Death Certificate","Death Registration","Crematorium Certificate",
        "Burial Certificate","Military Service","Service Record","Probate","Will"
    ]
    for role in roles:
        if role.lower() in t.lower():
            return role
    return t or "Document"

def _caption(m,person_name=None,family_names=None,page=None):
    role=_clean_document_title(media_title(m),person_name,family_names)
    subject=family_names or person_name
    bits=[role]
    if subject:
        bits.append(subject)
    if page is not None:
        bits.append(f"Page {page}")
    return " — ".join(bits)

def _image_presentation(path):
    """Return publication orientation/size hints without cropping the source image."""
    try:
        from PIL import Image
        with Image.open(Path(path).expanduser()) as im:
            w,h=im.size
    except Exception:
        return "square", False
    ratio=(w / h) if h else 1.0
    shape="landscape" if ratio>=1.15 else "portrait" if ratio<=0.87 else "square"
    # Roughly one A4 content width at 150 dpi.  Small originals should not be
    # forced to full page width and visibly upscaled.
    small=max(w,h)<900
    return shape, small

def _image_block(m,hero=False,output_html=None):
    uri=_embedded_image_uri(m["file_path"])
    if not uri:return None
    title=media_title(m)
    original=copy_original(m["file_path"],output_html,m["id"]) if output_html else None
    if original:
        image=f"<a href='{esc(original)}'><img src='{esc(uri)}' alt='{esc(title)}'></a>"
        open_link=f"<a class='open-original' href='{esc(original)}'>Open original image</a>"
    else:
        image=f"<img src='{esc(uri)}' alt='{esc(title)}'>"
        open_link=""
    shape,small=_image_presentation(m["file_path"])
    classes=["media-card",f"media-{shape}"]
    if hero: classes.append("hero")
    if small: classes.append("media-small")
    return (
        f"<figure class='{" ".join(classes)}'>"
        f"{image}<figcaption class='caption'>{esc(title)}</figcaption>{open_link}"
        f"</figure>"
    )

def _pdf_block(m,output_html,person_name=None,family_names=None):
    """Screen: first page preview + link. Print: every PDF page, one archive page each."""
    title=media_title(m)
    r=render_pdf(m["file_path"],output_html,m["id"],dpi=150)
    original=r["original"]
    pages=r["pages"]
    if not pages:
        href=original
        link=f"<a class='open-original' href='{esc(href)}'>Open original PDF</a>" if href else ""
        warning=f"<p class='small'>{esc(r['warning'])}</p>" if r["warning"] else ""
        return (
          f"<div class='document-card'><strong>{esc(title)}</strong>"
          f"<p>PDF · {'Available' if m['exists_on_disk'] else 'Missing'}</p>{link}{warning}</div>"
        )

    first=pages[0]
    link=f"<a class='open-original' href='{esc(original)}'>Open original PDF</a>" if original else ""
    caption=_caption(m,person_name,family_names,None)
    screen=[
      "<section class='pdf-web-plate web-only'>",
      f"<h3>{esc(_clean_document_title(title,person_name,family_names))}</h3>",
      f"<div class='preview'><a href='{esc(original)}'>" if original else "<div class='preview'>",
      f"<img src='{esc(first['preview_rel'])}' alt='{esc(caption)} preview'>",
      "</a></div>" if original else "</div>",
      f"<p class='pdf-caption'>{esc(caption)}</p>",
      f"<p class='small'>{len(pages)} PDF page{'s' if len(pages)!=1 else ''}</p>" if len(pages)>1 else "",
      link,
    ]
    if r["warning"]:screen.append(f"<p class='small'>{esc(r['warning'])}</p>")
    screen.append("</section>")

    printed=[]
    for i,p in enumerate(pages):
        extra=" pdf-extra-page" if i else ""
        cap=_caption(m,person_name,family_names,p["page"])
        printed.append(
          f"<section class='archive-page {esc(p['orientation'])}{extra}'>"
          f"<div class='archive-title'>{esc(title)}</div>"
          f"<img class='doc-preview' src='{esc(p['preview_rel'])}' alt='{esc(cap)}'>"
          f"<div class='archive-caption'>{esc(cap)}</div>"
          f"</section>"
        )
    return "".join(screen+printed)

def _media_block(m,output_html,hero=False,person_name=None,family_names=None):
    ext=Path(m["file_path"]).suffix.lower()
    if ext==".pdf":
        return _pdf_block(m,output_html,person_name,family_names)
    image=_image_block(m,hero=hero,output_html=output_html)
    if image:return image

    original=copy_original(m["file_path"],output_html,m["id"]) if output_html else None
    link=f"<a class='open-original' href='{esc(original)}'>Open original document</a>" if original else ""
    return (
      f"<div class='document-card'><strong>{esc(media_title(m))}</strong>"
      f"<p>{esc(ext.upper().lstrip('.') or 'FILE')} · {'Available' if m['exists_on_disk'] else 'Missing'}</p>"
      f"{link}</div>"
    )

def _person_summary_html(db,pid,anchor=None):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    dates=life_dates(db,pid);events=person_events(db,pid)
    vals={}
    for typ in ("Occupation","Education","Religion"):
        vals[typ]=next((e["value_text"] for e in events if e["event_type"]==typ and e["value_text"]),None)
    rows=[
      ("Birth"," — ".join(x for x in (dates["birth"],dates["birth_place"]) if x)),
      ("Death"," — ".join(x for x in (dates["death"],dates["death_place"]) if x)),
      ("Occupation",vals["Occupation"]),("Education",vals["Education"]),("Religion",vals["Religion"])
    ]
    aid=f" id='{esc(anchor)}'" if anchor else ""
    P=[f"<section class='person-summary'{aid}><h2>{esc(p['display_name'])}</h2>"]
    for label,val in rows:
        if val:P.append(f"<div class='person-topic'><h3>{esc(label)}</h3><p>{esc(val)}</p></div>")
    P.append("</section>")
    return "".join(P)

def _person_section(db,pid,output_html,anchor=None):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    groups=person_document_groups(db,pid)
    P=["<div class='pagebreak'></div>",_person_summary_html(db,pid,anchor)]
    if groups["portrait"]:
        P.append(_media_block(groups["portrait"][0],output_html,hero=True,person_name=p["display_name"]))

    P.append("<h2>Life &amp; Notes</h2>")
    sections=story_sections(db,pid)
    note_meta=db.execute("SELECT note_type,gedcom_tag FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    note_labels={(n["note_type"] or n["gedcom_tag"] or "Note") for n in note_meta}
    structured=[(h,t) for h,t in sections if h not in note_labels]
    for heading,text in structured:
        P.append(f"<section class='life-topic keep'><h3>{esc(heading)}</h3><div class='note'>{esc(text)}</div></section>")
    note_rows=db.execute("SELECT text FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    notes=[preserve_note_layout(n["text"]) for n in note_rows if preserve_note_layout(n["text"])]
    facts=[]
    for e in person_events(db,pid):
        bits=[e["event_type"],e["date_text"],e["place_text"],e["value_text"]]
        fact=" — ".join(str(x) for x in bits if x and x!="Y")
        if fact:facts.append(fact)
    narrative=publication_narrative(p["display_name"],notes,facts) if notes else ""
    if narrative:
        P.append(f"<section class='life-topic publication-narrative'><h3>Publication Narrative</h3><div class='note'>{esc(narrative)}</div></section>")
    elif not structured:
        P.append("<p>No narrative notes are recorded.</p>")

    ordered=(("birth","Birth Documents"),("death","Death & Burial Documents"),
             ("military","Military Documents"),("other-documents","Other Documents"))
    for key,label in ordered:
        if groups[key]:
            P.append(f"<h2>{esc(label)}</h2>")
            for m in groups[key]:
                P.append(_media_block(m,output_html,person_name=p["display_name"]))
    if groups["other-photos"]:
        P.append("<h2>Other Photographs</h2>")
        for m in groups["other-photos"]:
            P.append(_media_block(m,output_html,person_name=p["display_name"]))
    if groups["legacy"]:
        P.append("<h2>Legacy Media</h2>")
        for m in groups["legacy"]:
            P.append(_media_block(m,output_html,person_name=p["display_name"]))
            P.append("<p class='small'>Legacy media identified for later conversion; original not modified.</p>")
    return "".join(P)

def _family_title(db,family_id):
    h,w=family_partners(db,family_id)
    return " and ".join(x["display_name"] for x in (h,w) if x) or f"Family {family_id}"

def _family_title_html(db,family_id):
    h,w=family_partners(db,family_id)
    if h and w:
        return f"<span class='couple-name'>{esc(h['display_name'])}</span><span class='couple-and'>and</span><span class='couple-name'>{esc(w['display_name'])}</span>"
    return esc(_family_title(db,family_id))

def _family_intro(db,family_id,anchor=None):
    o=family_overview(db,family_id);f=o["family"];h=o["husband"];w=o["wife"]
    aid=f" id='{esc(anchor)}'" if anchor else ""
    P=[f"<section{aid}><div class='chapter-kicker'>Family Chapter</div><h1 class='couple-title'>{_family_title_html(db,family_id)}</h1>"]
    if h and w:
        intro=f"{h['display_name']} and {w['display_name']}"
        if f["marriage_date"]:intro+=f" were married on {f['marriage_date']}"
        else:intro+=" are recorded as a family"
        if f["marriage_place"]:intro+=f" at {f['marriage_place']}"
        intro+="."
        if o["children_count"]:
            intro+=f" They had {o['children_count']} child{'ren' if o['children_count']!=1 else ''}."
        P.append(f"<h2>About the Family</h2><p>{esc(intro)}</p>")
    P.append("</section>")
    return "".join(P)


def _chapter_sources(db,family_id,h,w):
    src={}
    for s in family_sources(db,family_id):src[s["id"]]=s
    for p in (h,w):
        if p:
            for s in person_sources(db,p["id"]):src[s["id"]]=s
    return sorted(src.values(),key=lambda s:int(source_number(s)) if source_number(s).isdigit() else 10**9)

def family_chapter_body(db,family_id,output_html,theme=DEFAULT_THEME,descendant_generations=4,
                        chapter_anchor=None,person_anchors=None):
    o=family_overview(db,family_id);h=o["husband"];w=o["wife"];f=o["family"]
    family_names=_family_title(db,family_id)
    person_anchors=person_anchors or {}
    P=[_family_intro(db,family_id,chapter_anchor)]

    # Established book order: introduction -> wedding photo -> marriage certificate.
    if o["wedding_photos"] or o["marriage_documents"] or f["marriage_date"] or f["marriage_place"]:
        P.append("<h2>Marriage</h2>")
        if f["marriage_date"] or f["marriage_place"]:
            P.append("<p>"+" — ".join(esc(x) for x in (f["marriage_date"],f["marriage_place"]) if x)+"</p>")
        for m in o["wedding_photos"]:
            P.append(_media_block(m,output_html,hero=True,family_names=family_names))
        for m in o["marriage_documents"]:
            P.append(_media_block(m,output_html,family_names=family_names))

    if h:P.append(_person_section(db,h["id"],output_html,person_anchors.get(h["id"])))
    if w:P.append(_person_section(db,w["id"],output_html,person_anchors.get(w["id"])))

    surfaced={m["id"] for m in o["wedding_photos"]+o["marriage_documents"]}
    extra=[m for m in family_media(db,family_id) if m["id"] not in surfaced]
    if extra:
        P.append("<div class='pagebreak'></div><h2>Family Documents &amp; Media</h2>")
        for m in extra:P.append(_media_block(m,output_html,family_names=family_names))

    P.append("<div class='pagebreak'></div><h2>Children</h2>")
    kids=children(db,family_id)
    if kids:
        P.append("<ul>")
        for ch in kids:
            d=life_dates(db,ch["id"]);bits=[ch["display_name"]]
            if d["birth"]:bits.append("b. "+d["birth"])
            if d["death"]:bits.append("d. "+d["death"])
            P.append("<li>"+esc(" — ".join(bits))+"</li>")
        P.append("</ul>")
    else:P.append("<p>No children are recorded for this family.</p>")

    P.append(chart_html(db,h["id"] if h else None,w["id"] if w else None,descendant_generations))

    sources=_chapter_sources(db,family_id,h,w)
    if sources:
        P.append("<div class='pagebreak'></div><h2>Sources Used in This Chapter</h2><ol class='sources'>")
        for s in sources:
            # Reader-facing number; GEDCOM @Sxx@ never leaks into the book.
            P.append(f"<li><span class='source-ref'>{esc(source_label(s))}</span> {esc(source_text(s))}</li>")
        P.append("</ol>")
    return "".join(P)

def family_chapter_html(db,family_id,output_html=None,theme=DEFAULT_THEME,descendant_generations=4):
    title=_family_title(db,family_id)
    return (
      "<!doctype html><html><head><meta charset='utf-8'>"
      f"<title>{esc(title)} — Family Chapter</title>"
      f"<style>{CSS}{PRO_CSS}{theme_css(theme)}</style></head><body>"
      +family_chapter_body(db,family_id,output_html,theme,descendant_generations,"family-1",{})
      +"</body></html>"
    )

def write_family_chapter(db,family_id,path=None,theme=DEFAULT_THEME,descendant_generations=4):
    h,w=family_partners(db,family_id)
    name="_and_".join(slug(x["display_name"]) for x in (h,w) if x) or f"Family_{family_id}"
    p=Path(path).expanduser() if path else default_report_dir()/(name+"_Professional_Family_Chapter.html")
    p.parent.mkdir(parents=True,exist_ok=True)
    # Standalone chapter anchors both partners for browser navigation.
    anchors={}
    if h:anchors[h["id"]]=f"person-{h['id']}"
    if w:anchors[w["id"]]=f"person-{w['id']}"
    title=_family_title(db,family_id)
    body=family_chapter_body(db,family_id,p,theme,descendant_generations,"family-1",anchors)
    html=(
      "<!doctype html><html><head><meta charset='utf-8'>"
      f"<title>{esc(title)} — Professional Family Chapter</title>"
      f"<style>{CSS}{PRO_CSS}{theme_css(theme)}</style></head><body>{body}</body></html>"
    )
    p.write_text(html,encoding="utf-8")
    return p

def book_family_ids(db,start_pid,generations=4):
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

def _book_maps(db,fam_ids):
    chapter_anchor={fid:f"chapter-{i+1}" for i,fid in enumerate(fam_ids)}
    person_anchor={}
    person_chapter={}
    all_sources={}
    places=defaultdict(list)
    for fid in fam_ids:
        h,w=family_partners(db,fid)
        for p in (h,w):
            if p and p["id"] not in person_anchor:
                person_anchor[p["id"]]=f"person-{p['id']}"
                person_chapter[p["id"]]=chapter_anchor[fid]
            if p:
                for e in person_events(db,p["id"]):
                    if e["place_text"]:
                        places[e["place_text"]].append(chapter_anchor[fid])
                for s in person_sources(db,p["id"]):all_sources[s["id"]]=s
        for s in family_sources(db,fid):all_sources[s["id"]]=s
    return chapter_anchor,person_anchor,person_chapter,all_sources,places

def _toc(db,fam_ids,chapter_anchor):
    P=["<section class='toc pagebreak'><h1>Contents</h1><ul>"]
    for i,fid in enumerate(fam_ids,1):
        P.append(f"<li><a href='#{esc(chapter_anchor[fid])}'>Chapter {i} — {esc(_family_title(db,fid))}</a></li>")
    P.append("</ul></section>")
    return "".join(P)

def _person_index(db,person_anchor,person_chapter):
    rows=[]
    for pid,anchor in person_anchor.items():
        p=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
        if p:rows.append((p["display_name"],anchor))
    rows.sort(key=lambda x:x[0].lower())
    P=["<section class='pagebreak'><h1>Person Index</h1><div class='index-list'>"]
    for name,anchor in rows:
        P.append(f"<div class='index-entry'><a href='#{esc(anchor)}'>{esc(name)}</a></div>")
    P.append("</div></section>")
    return "".join(P)

def _place_index(places):
    P=["<section class='pagebreak'><h1>Place Index</h1><div class='index-list'>"]
    for place,anchors in sorted(places.items(),key=lambda x:x[0].lower()):
        if not anchors:continue
        anchor=anchors[0]
        P.append(f"<div class='index-entry'><a href='#{esc(anchor)}'>{esc(place)}</a></div>")
    P.append("</div></section>")
    return "".join(P)

def _source_index(sources):
    P=["<section class='pagebreak'><h1>Source Index</h1><ol class='sources'>"]
    for s in sorted(sources.values(),key=lambda s:int(source_number(s)) if source_number(s).isdigit() else 10**9):
        P.append(f"<li><span class='source-ref'>{esc(source_label(s))}</span> {esc(source_text(s))}</li>")
    P.append("</ol></section>")
    return "".join(P)

def book_html(db,start_pid,output_html, generations=4,theme=DEFAULT_THEME):
    start=db.execute("SELECT * FROM people WHERE id=?",(start_pid,)).fetchone()
    fam_ids=book_family_ids(db,start_pid,generations)
    chapter_anchor,person_anchor,person_chapter,sources,places=_book_maps(db,fam_ids)

    P=["<!doctype html><html><head><meta charset='utf-8'>",
       f"<title>{esc(start['display_name'])} — Family History</title>",
       f"<style>{CSS}{PRO_CSS}{theme_css(theme)}</style></head><body>",
       "<section class='title-page'><div class='chapter-kicker'>Reunion Companion</div>",
       "<h1>Family History</h1>",
       f"<h2>{esc(start['display_name'])} and Descendants</h2>",
       f"<p>{len(fam_ids)} family chapter{'s' if len(fam_ids)!=1 else ''}</p>",
       "</section>",
       _toc(db,fam_ids,chapter_anchor)]

    # Every person gets one canonical anchor on their first published spouse page.
    anchored=set()
    for i,fid in enumerate(fam_ids,1):
        h,w=family_partners(db,fid)
        local={}
        for p in (h,w):
            if p and p["id"] not in anchored:
                local[p["id"]]=person_anchor[p["id"]]
                anchored.add(p["id"])
        P.append(f"<section class='chapter'><div class='chapter-kicker'>Chapter {i}</div>")
        P.append(family_chapter_body(db,fid,output_html,theme,generations,chapter_anchor[fid],local))
        P.append("</section>")

    P.append(_person_index(db,person_anchor,person_chapter))
    P.append(_place_index(places))
    P.append(_source_index(sources))
    P.append("</body></html>")
    return "".join(P)

def write_book(db,start_pid,path=None,generations=4,theme=DEFAULT_THEME):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(start_pid,)).fetchone()["display_name"]
    p=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Professional_Family_History.html")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(book_html(db,start_pid,p,generations,theme),encoding="utf-8")
    return p

def export_pdf_from_html(html_path,pdf_path=None):
    html_path=Path(html_path).expanduser()
    if not html_path.exists():
        raise FileNotFoundError(html_path)
    pdf_path=Path(pdf_path).expanduser() if pdf_path else html_path.with_suffix(".pdf")
    try:
        from weasyprint import HTML
    except Exception as e:
        raise RuntimeError(
            "WeasyPrint is not installed. Install it in the Companion virtual environment to enable direct PDF export."
        ) from e
    HTML(filename=str(html_path),base_url=str(html_path.parent)).write_pdf(str(pdf_path))
    return pdf_path

def write_book_pdf(db,start_pid,path=None,generations=4,theme=DEFAULT_THEME):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(start_pid,)).fetchone()["display_name"]
    pdf=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Professional_Family_History.pdf")
    html=pdf.with_suffix(".html")
    write_book(db,start_pid,html,generations,theme)
    return export_pdf_from_html(html,pdf)

def format_publish_capabilities():
    pdf=pdf_render_capability()
    try:
        import weasyprint
        pdf_export="Available (WeasyPrint)"
    except Exception:
        pdf_export="Unavailable until WeasyPrint is installed"
    return "\n".join([
      "Professional Publishing Capabilities",
      "====================================",
      "",
      f"PDF document preview renderer: {pdf['renderer']}",
      f"All PDF pages for print: {'yes' if pdf['all_pages'] else 'no'}",
      f"Direct book PDF export: {pdf_export}",
      "",
      "Print document rule:",
      "  Portrait PDF page  -> normal portrait archive page",
      "  Landscape PDF page -> rotated 90° on an A4 portrait book page",
      "  Multi-page PDF     -> consecutive archive pages",
      "",
      "Web document rule:",
      "  First page preview in natural orientation",
      "  Link to copied original PDF",
      "  Additional PDF pages hidden on screen but included when printing",
    ])
