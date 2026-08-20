from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import re
import tempfile
from .publishing_v7 import CSS,esc,slug,default_report_dir
from .publishing_v8 import _embedded_image_uri
from .publication_themes import theme_css,DEFAULT_THEME
from .family_publication_model import (
    family_overview,family_partners,children,life_dates,person_events,
    person_document_groups,person_sources,family_sources,family_media,
    spouse_families,resolve_family_for_people,person_media
)
from .story_engine import story_sections
from .publication_narrative import preserve_note_layout
from .person_narrative import cached_person_narrative,person_narrative,source_fingerprint,NARRATIVE_VERSION
from .descendant_chart import chart_html
from .document_renderer import render_pdf,copy_original,pdf_render_capability
from .branding import publishing_mark_uri

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
.publishing-mark { width:38mm; height:38mm; object-fit:contain; margin:0 auto 7mm; display:block; }
.title-page .chapter-kicker { color:#60743a; }
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
.media-card { break-inside:avoid; page-break-inside:avoid; }

.photo-grid { display:block; }
.photo-page { break-inside:avoid; page-break-inside:avoid; margin:0 0 6mm; }
.photo-page.photo-pair { break-after:page; page-break-after:always; height:231mm; display:grid; grid-template-rows:113mm 113mm; gap:5mm; transform:translateY(8mm); }
.photo-page.photo-pair.single-tail { grid-template-rows:113mm; height:113mm; }
/* Each half-page is a real image+caption slot.  The caption owns its row, so
   enlarging a photograph can never clip or cover its description. */
.photo-page .media-card { margin:0; width:100%; box-sizing:border-box; height:113mm; break-inside:avoid; page-break-inside:avoid; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; min-height:0; overflow:visible; }
.photo-page .media-card img { display:block; width:auto; height:auto; max-width:100%; max-height:106mm; object-fit:contain; margin:0 auto 1mm; flex:0 1 auto; }
.photo-page .media-card.media-landscape img { max-height:91mm; }
.photo-page .media-card figcaption { margin:0; flex:0 0 auto; break-inside:avoid; page-break-inside:avoid; text-align:center; line-height:1.2; width:100%; max-width:100%; overflow:visible; }
@media screen {
  .photo-page.photo-pair { break-after:auto; page-break-after:auto; min-height:0; }
}
.person-name { font-weight:700; font-size:1em; }
.person-dates { font-weight:400; font-size:0.84em; color:#555; white-space:nowrap; }
.person-line { margin:1.2mm 0; }
.citation-ref { font-weight:bold; white-space:nowrap; }
.fact-line { margin:1.2mm 0; }
.person-summary { border:0; padding:0; margin:0 0 6mm; }
.person-summary h2 { margin:1mm 0 4mm; }
.person-summary-layout { display:grid; grid-template-columns:minmax(0,1fr) 48mm; gap:7mm; align-items:start; }
.person-summary-layout.no-portrait { grid-template-columns:1fr; }
.person-summary-grid { display:grid; grid-template-columns:30mm 1fr; column-gap:4mm; row-gap:1.1mm; font-size:9.5pt; }
.person-summary-grid .summary-label { font-weight:bold; color:#555; }
.person-summary-grid .summary-group-start { margin-top:3mm; }
.person-summary-portrait img { display:block; width:48mm; max-height:72mm; object-fit:contain; margin:0 auto; }
.person-biography { margin-top:4mm; }
.person-biography h3, .person-sources h3 { font-size:11.5pt; margin:0 0 2mm; }
.person-sources { margin-top:5mm; }
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
.birth-documents-section { margin:0; padding:0; }
.document-fitted-page { display:none; break-before:page; page-break-before:always; height:258mm; position:relative; text-align:center; overflow:hidden; }
.document-fitted-page .document-fitted-heading { position:absolute; top:0; left:0; right:0; margin:0; padding:0 0 1mm; border-bottom:1px solid #aaa; text-align:left; font-size:15pt; line-height:1.15; }
.document-fitted-page .document-fitted-title { position:absolute; top:12mm; left:0; right:0; font-size:9pt; font-weight:bold; }
.document-fitted-page .document-fitted-preview { position:absolute; left:50%; object-fit:contain; }
.document-fitted-page.portrait .document-fitted-preview { top:23mm; max-width:170mm; max-height:207mm; transform:translateX(-50%); }
.document-fitted-page.landscape .document-fitted-preview { top:50%; width:210mm; max-height:150mm; transform:translate(-50%,-47%) rotate(90deg); }
.document-fitted-page .document-fitted-caption { position:absolute; bottom:7mm; left:0; right:0; font-size:8pt; color:#555; }

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

/* RC1.0.3 true structural Birth Documents page.
   This is a separate print renderer, not an archive-page override. */
.birth-document-page {
  display:none;
  break-before:page;
  page-break-before:always;
  height:258mm;
  position:relative;
  text-align:center;
  overflow:hidden;
}
.birth-document-page .birth-document-heading {
  position:absolute;
  top:0;
  left:0;
  right:0;
  margin:0;
  padding:0 0 1mm;
  border-bottom:1px solid #aaa;
  text-align:left;
  font-size:15pt;
  line-height:1.15;
}
.birth-document-page .birth-document-title {
  position:absolute;
  top:12mm;
  left:0;
  right:0;
  font-size:9pt;
  font-weight:bold;
}
.birth-document-page .birth-document-preview {
  position:absolute;
  left:50%;
  object-fit:contain;
}
.birth-document-page.portrait .birth-document-preview {
  top:23mm;
  max-width:170mm;
  max-height:207mm;
  transform:translateX(-50%);
}
.birth-document-page.landscape .birth-document-preview {
  top:50%;
  width:210mm;
  max-height:150mm;
  transform:translate(-50%,-47%) rotate(90deg);
}
.birth-document-page .birth-document-caption {
  position:absolute;
  bottom:7mm;
  left:0;
  right:0;
  font-size:8pt;
  color:#555;
}
.birth-document-page .birth-document-original {
  position:absolute;
  bottom:0;
  left:0;
  right:0;
  font-size:8pt;
  font-weight:bold;
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
  figure.media-card.media-portrait { break-inside:avoid !important; page-break-inside:avoid !important; }
  figure.media-card.media-portrait img { max-height:198mm !important; width:auto !important; max-width:100% !important; object-fit:contain; }
  figure.media-card.media-square { break-inside:avoid !important; page-break-inside:avoid !important; }
  figure.media-card.media-square img { max-height:198mm !important; width:auto !important; max-width:100% !important; object-fit:contain; }
  /* Photo-pair pages are deliberately two vertically stacked best-fit slots.
     This print-specific rule must override the older single-photo 198mm rule
     above; otherwise portrait images overflow the 108mm slot and are clipped
     into a landscape-shaped viewport. */
  .photo-page figure.media-card.media-portrait img,
  .photo-page figure.media-card.media-square img {
    width:auto !important;
    height:auto !important;
    max-width:100% !important;
    max-height:106mm !important;
    object-fit:contain !important;
  }
  /* Landscape sizing was already visually successful in Pass 4. */
  .photo-page figure.media-card.media-landscape img {
    width:auto !important;
    height:auto !important;
    max-width:100% !important;
    max-height:91mm !important;
    object-fit:contain !important;
  }
  .web-only { display:none !important; }
  .print-only { display:block; }
  .archive-page { display:block !important; }
  .birth-document-page { display:block !important; }
  .document-fitted-page { display:block !important; }
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

def event_source_labels(db,event_id):
    rows=db.execute("""SELECT s.* FROM sources s JOIN event_sources es ON es.source_id=s.id
                       WHERE es.event_id=? ORDER BY s.id""",(event_id,)).fetchall()
    return [source_label(x) for x in rows]

def media_source_labels(db,media_id):
    """Sources deterministically associated through the media attachment context."""
    rows=db.execute("""SELECT DISTINCT s.* FROM sources s WHERE s.id IN (
      SELECT es.source_id FROM event_sources es JOIN event_media em ON em.event_id=es.event_id WHERE em.media_id=?
      UNION SELECT fs.source_id FROM family_sources fs JOIN family_media fm ON fm.family_id=fs.family_id WHERE fm.media_id=?
    ) ORDER BY s.id""",(media_id,media_id)).fetchall()
    return [source_label(x) for x in rows]

def citation_suffix(labels):
    return " ".join(labels)

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

def _image_block(m,hero=False,output_html=None,citation=""):
    uri=_embedded_image_uri(m["file_path"])
    if not uri:return None
    title=media_title(m)
    image=f"<img src='{esc(uri)}' alt='{esc(title)}'>"
    shape,small=_image_presentation(m["file_path"])
    classes=["media-card",f"media-{shape}"]
    if hero: classes.append("hero")
    if small: classes.append("media-small")
    caption=esc(title)+(f" <span class='citation-ref'>{esc(citation)}</span>" if citation else "")
    return f"<figure class='{' '.join(classes)}'>{image}<figcaption class='caption'>{caption}</figcaption></figure>"

def _pdf_block(m,output_html,person_name=None,family_names=None,citation=""):
    """Screen: first page preview + link. Print: every PDF page, one archive page each."""
    title=media_title(m)
    r=render_pdf(m["file_path"],output_html,m["id"],dpi=150)
    original=r["original"]; pages=r["pages"]
    cite=f" {citation}" if citation else ""
    if not pages:
        link=""
        warning=f"<p class='small'>{esc(r['warning'])}</p>" if r["warning"] else ""
        return f"<div class='document-card'><strong>{esc(_clean_document_title(title,person_name,family_names))}{esc(cite)}</strong><p>PDF · {'Available' if m['exists_on_disk'] else 'Missing'}</p>{link}{warning}</div>"
    first=pages[0]; link=""
    caption=_caption(m,person_name,family_names,None)+cite
    screen=["<section class='pdf-web-plate web-only'>",
      f"<h3>{esc(_clean_document_title(title,person_name,family_names))}{f' <span class=\"citation-ref\">{esc(citation)}</span>' if citation else ''}</h3>",
      "<div class='preview'>",
      f"<img src='{esc(first['preview_rel'])}' alt='{esc(caption)} preview'>",
      "</div>",
      f"<p class='pdf-caption'>{esc(caption)}</p>",
      f"<p class='small'>{len(pages)} PDF page{'s' if len(pages)!=1 else ''}</p>" if len(pages)>1 else "",link]
    if r["warning"]:screen.append(f"<p class='small'>{esc(r['warning'])}</p>")
    screen.append("</section>")
    printed=[]
    for i,page in enumerate(pages):
        extra=" pdf-extra-page" if i else ""
        cap=_caption(m,person_name,family_names,page["page"])+cite
        printed.append(f"<section class='archive-page {esc(page['orientation'])}{extra}'><div class='archive-title'>{esc(_clean_document_title(title,person_name,family_names))}{esc(cite)}</div><img class='doc-preview' src='{esc(page['preview_rel'])}' alt='{esc(cap)}'><div class='archive-caption'>{esc(cap)}</div></section>")
    return "".join(screen+printed)

def _media_block(m,output_html,hero=False,person_name=None,family_names=None,db=None):
    citation=citation_suffix(media_source_labels(db,m["id"])) if db is not None else ""
    ext=Path(m["file_path"]).suffix.lower()
    if ext==".pdf": return _pdf_block(m,output_html,person_name,family_names,citation)
    image=_image_block(m,hero=hero,output_html=output_html,citation=citation)
    if image:return image
    original=copy_original(m["file_path"],output_html,m["id"]) if output_html else None
    link=""
    label=_clean_document_title(media_title(m),person_name,family_names)
    return f"<div class='document-card'><strong>{esc(label)}{(' '+esc(citation)) if citation else ''}</strong><p>{esc(ext.upper().lstrip('.') or 'FILE')} · {'Available' if m['exists_on_disk'] else 'Missing'}</p>{link}</div>"

def _fitted_document_block(m,output_html,heading,person_name=None,family_names=None,db=None):
    """Birth-model fitted first PDF page for any named document section."""
    citation=citation_suffix(media_source_labels(db,m["id"])) if db is not None else ""
    r=render_pdf(m["file_path"],output_html,m["id"],dpi=150)
    if not r["pages"]:
        return f"<h2>{esc(heading)}</h2>"+_pdf_block(m,output_html,person_name,family_names,citation)
    first=r["pages"][0]; original=r["original"]; cite=f" {citation}" if citation else ""
    label=_clean_document_title(media_title(m),person_name,family_names)
    cap=_caption(m,person_name,family_names,first["page"])+cite
    link=""
    web=[f"<div class='web-only'><h2>{esc(heading)}</h2></div>","<section class='pdf-web-plate web-only'>",f"<h3>{esc(label)}</h3>",f"<div class='preview'><img src='{esc(first['preview_rel'])}' alt='{esc(cap)} preview'></div>",f"<p class='pdf-caption'>{esc(cap)}</p>",link,"</section>"]
    printed=[f"<section class='document-fitted-page {esc(first['orientation'])}'><h2 class='document-fitted-heading'>{esc(heading)}</h2><div class='document-fitted-title'>{esc(label)}{esc(cite)}</div><img class='document-fitted-preview' src='{esc(first['preview_rel'])}' alt='{esc(cap)}'><div class='document-fitted-caption'>{esc(cap)}</div></section>"]
    for page in r["pages"][1:]:
        page_cap=_caption(m,person_name,family_names,page["page"])+cite
        printed.append(f"<section class='archive-page {esc(page['orientation'])} pdf-extra-page'><div class='archive-title'>{esc(label)}{esc(cite)}</div><img class='doc-preview' src='{esc(page['preview_rel'])}' alt='{esc(page_cap)}'><div class='archive-caption'>{esc(page_cap)}</div></section>")
    return "".join(web+printed)

def _birth_document_block(m,output_html,person_name=None,db=None):
    """Render the first Birth Documents PDF as one fitted print page.

    The section heading, document title/source, first PDF preview, caption and
    original-PDF link are emitted in one dedicated page. Remaining PDF pages
    continue through ordinary archive pages.
    """
    citation=citation_suffix(media_source_labels(db,m["id"])) if db is not None else ""
    title=media_title(m)
    r=render_pdf(m["file_path"],output_html,m["id"],dpi=150)
    original=r["original"]; pages=r["pages"]
    cite=f" {citation}" if citation else ""

    # If rendering is unavailable, retain a normal visible Birth Documents
    # heading and deterministic document fallback.
    if not pages:
        fallback=_pdf_block(m,output_html,person_name,None,citation)
        return "<h2>Birth Documents</h2>"+fallback

    first=pages[0]
    label=_clean_document_title(title,person_name,None)
    cap=_caption(m,person_name,None,first["page"])+cite

    # Web/HTML retains the familiar section heading and natural first-page preview.
    link=""
    web_caption=_caption(m,person_name,None,None)+cite
    screen=[
      "<div class='web-only'><h2>Birth Documents</h2></div>",
      "<section class='pdf-web-plate web-only'>",
      f"<h3>{esc(label)}{f' <span class=\"citation-ref\">{esc(citation)}</span>' if citation else ''}</h3>",
      "<div class='preview'>",
      f"<img src='{esc(first['preview_rel'])}' alt='{esc(web_caption)} preview'>",
      "</div>",
      f"<p class='pdf-caption'>{esc(web_caption)}</p>",
      f"<p class='small'>{len(pages)} PDF page{'s' if len(pages)!=1 else ''}</p>" if len(pages)>1 else "",
      link,
      "</section>",
    ]

    original_print=""
    printed=[
      f"<section class='birth-document-page {esc(first['orientation'])}'>"
      f"<h2 class='birth-document-heading'>Birth Documents</h2>"
      f"<div class='birth-document-title'>{esc(label)}{esc(cite)}</div>"
      f"<img class='birth-document-preview' src='{esc(first['preview_rel'])}' alt='{esc(cap)}'>"
      f"<div class='birth-document-caption'>{esc(cap)}</div>"
      f"{original_print}"
      f"</section>"
    ]

    # Pages 2+ use the ordinary archive layout and therefore begin on their own pages.
    for i,page in enumerate(pages[1:],start=1):
        page_cap=_caption(m,person_name,None,page["page"])+cite
        printed.append(
          f"<section class='archive-page {esc(page['orientation'])} pdf-extra-page'>"
          f"<div class='archive-title'>{esc(label)}{esc(cite)}</div>"
          f"<img class='doc-preview' src='{esc(page['preview_rel'])}' alt='{esc(page_cap)}'>"
          f"<div class='archive-caption'>{esc(page_cap)}</div>"
          f"</section>"
        )
    if r["warning"]:
        screen.insert(-1,f"<p class='small'>{esc(r['warning'])}</p>")
    return "".join(screen+printed)

def _publication_fact_sections(db,pid):
    """Deterministic, topic-separated facts for Life & Notes."""
    groups=[("Life Events",[]),("Education",[]),("Work Life",[])]
    by=dict(groups)
    for e in person_events(db,pid):
        typ=(e["event_type"] or "Event").strip()
        if typ.casefold()=="changed":continue
        low=typ.casefold()
        heading="Education" if "educat" in low or "school" in low else "Work Life" if any(x in low for x in ("occupation","employment","work","career")) else "Life Events"
        vals=[x for x in (e["date_text"],e["place_text"],e["value_text"]) if x and x!="Y"]
        detail=" — ".join(str(x) for x in vals)
        refs=citation_suffix(event_source_labels(db,e["id"]))
        line=f"<div class='fact-line'><strong>{esc(typ)}:</strong> {esc(detail) if detail else 'Recorded'}"
        if refs:line+=f" <span class='citation-ref'>{esc(refs)}</span>"
        line+="</div>"
        by[heading].append(line)
    return [(h,rows) for h,rows in groups if rows]



def _event_values(events,kind):
    out=[]
    for e in events:
        if (e["event_type"] or "").casefold()!=kind.casefold():continue
        value=e["value_text"] or e["note_text"] or e["place_text"]
        if value and value!="Y" and value not in out:out.append(str(value))
    return out

def _person_marriage_details(db,pid):
    rows=db.execute("""SELECT f.marriage_date,f.marriage_place,p.display_name
      FROM families f JOIN family_members mine ON mine.family_id=f.id
      LEFT JOIN family_members other ON other.family_id=f.id AND other.person_id<>mine.person_id
        AND lower(other.role) IN ('husband','wife','spouse')
      LEFT JOIN people p ON p.id=other.person_id
      WHERE mine.person_id=? AND lower(mine.role) IN ('husband','wife','spouse') ORDER BY f.id""",(pid,)).fetchall()
    spouses=[];dates=[];places=[]
    for r in rows:
        if r["display_name"] and r["display_name"] not in spouses:spouses.append(r["display_name"])
        if r["marriage_date"] and r["marriage_date"] not in dates:dates.append(r["marriage_date"])
        if r["marriage_place"] and r["marriage_place"] not in places:places.append(r["marriage_place"])
    return spouses,dates,places

def _person_summary_html(db,pid,output_html=None,anchor=None,portrait=None):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone(); aid=f" id='{esc(anchor)}'" if anchor else ""
    events=person_events(db,pid)
    birth=next((e for e in events if (e["event_type"] or "").casefold()=="birth"),None)
    rows=[]
    def add(label,values,group=False):
        if isinstance(values,str) or values is None: values=[values] if values else []
        values=[str(x) for x in values if x]
        if not values:return
        cls="summary-label summary-group-start" if group else "summary-label"
        vcls="summary-group-start" if group else ""
        rows.append(f"<div class='{cls}'>{esc(label)}</div><div class='{vcls}'>"+"<br>".join(esc(x) for x in values)+"</div>")
    add("Birth Date",birth["date_text"] if birth else None)
    add("Birth Place",birth["place_text"] if birth else None)
    add("Occupation",_event_values(events,"Occupation"),True)
    add("Education",_event_values(events,"Education"))
    add("Religion",_event_values(events,"Religion"))
    from .discovery import relationship_connections
    rel=relationship_connections(db,pid); parents=rel.get("parents",[])
    def parent_sex(x):
        r=db.execute("SELECT sex FROM people WHERE id=?",(x["id"],)).fetchone()
        return (r[0] or "").upper() if r else ""
    father=next((x for x in parents if parent_sex(x)=="M"),None)
    mother=next((x for x in parents if parent_sex(x)=="F"),None)
    if not father and parents: father=parents[0]
    if not mother and len(parents)>1: mother=parents[1]
    add("Father",father["display_name"] if father else None,True)
    add("Mother",mother["display_name"] if mother else None)
    spouses,dates,places=_person_marriage_details(db,pid)
    add("Spouse",spouses,True); add("Marriage Date",dates); add("Marriage Place",places)
    kids=[x["display_name"] for x in rel.get("children",[])]
    add("Children",kids,True)
    details=f"<div class='person-summary-grid'>{''.join(rows)}</div>" if rows else ""
    portrait_html=""
    if portrait:
        uri=_embedded_image_uri(portrait["file_path"])
        if uri: portrait_html=f"<div class='person-summary-portrait'><img src='{esc(uri)}' alt='{esc(p['display_name'])}'></div>"
    cls="person-summary-layout"+("" if portrait_html else " no-portrait")
    return f"<section class='person-summary'{aid}><div class='chapter-kicker'>Life &amp; Biography</div><h2>{esc(p['display_name'])}</h2><div class='{cls}'>{details}{portrait_html}</div></section>"

def _publication_biography(db,pid):
    """Return publication-current biography without changing interactive cache semantics."""
    # Publishing must not depend on a prior Biography-page visit, and it must not
    # reuse prose built from an older evidence fingerprint. This specifically
    # retires cached biographies created when CHAN/Changed metadata was evidence.
    row=db.execute("SELECT source_hash,narrative_version,narrative FROM companion_person_narrative_cache WHERE person_id=?",(pid,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='companion_person_narrative_cache'").fetchone() else None
    fp=source_fingerprint(db,pid)
    if row and row[0]==fp and row[1]==NARRATIVE_VERSION and (row[2] or "").strip():
        return row[2]
    return (person_narrative(db,pid,force=True).get("narrative") or "").strip()

def _person_section(db,pid,output_html,anchor=None):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    groups=person_document_groups(db,pid)
    portrait=groups["portrait"][0] if groups["portrait"] else None
    P=["<div class='pagebreak'></div>",_person_summary_html(db,pid,output_html,anchor,portrait)]

    # Publication owns biography availability. person_narrative validates both the
    # evidence fingerprint and narrative version, so stale pre-CHAN-hardening prose
    # is regenerated automatically.
    narrative=_publication_biography(db,pid)
    if narrative:
        P.append(f"<section class='person-biography publication-narrative'><h3>Biography</h3><div class='note'>{esc(narrative)}</div></section>")
    else:
        P.append("<p>No biographical material is currently available.</p>")

    sources=person_sources(db,pid)
    if sources:
        P.append("<section class='person-sources'><h3>Sources</h3><ol class='sources'>")
        for source in sources:
            P.append(f"<li><span class='source-ref'>{esc(source_label(source))}</span> {esc(source_text(source))}</li>")
        P.append("</ol></section>")

    ordered=(("birth","Birth Documents"),("death","Death & Burial Documents"),
             ("military","Military Documents"),("other-documents","Other Documents"))
    for key,label in ordered:
        if not groups[key]:
            continue

        P.append(f"<section class='document-section{' birth-documents-section' if key=='birth' else ''}'>")

        if key=="birth":
            first=groups[key][0]
            first_is_pdf=Path(first["file_path"]).suffix.lower()==".pdf"
            if first_is_pdf:
                # The dedicated birth renderer owns the heading and first PDF page.
                P.append(_birth_document_block(first,output_html,person_name=p["display_name"],db=db))
                remaining=groups[key][1:]
            else:
                P.append(f"<h2>{esc(label)}</h2>")
                P.append(_media_block(first,output_html,person_name=p["display_name"],db=db))
                remaining=groups[key][1:]
            for m in remaining:
                P.append(_media_block(m,output_html,person_name=p["display_name"],db=db))
        else:
            first=groups[key][0]
            if Path(first["file_path"]).suffix.lower()==".pdf":
                P.append(_fitted_document_block(first,output_html,label,person_name=p["display_name"],db=db))
                remaining=groups[key][1:]
            else:
                P.append(f"<h2>{esc(label)}</h2>"); P.append(_media_block(first,output_html,person_name=p["display_name"],db=db)); remaining=groups[key][1:]
            for m in remaining:
                P.append(_media_block(m,output_html,person_name=p["display_name"],db=db))

        P.append("</section>")
    if groups["other-photos"]:
        P.append("<h2>Other Photographs</h2><div class='photo-grid'>")
        photos=groups["other-photos"]
        for i in range(0,len(photos),2):
            pair=photos[i:i+2]
            tail=" single-tail" if len(pair)==1 else ""
            P.append(f"<section class='photo-page photo-pair{tail}'>")
            for item in pair:
                P.append(_media_block(item,output_html,person_name=p["display_name"],db=db))
            P.append("</section>")
        P.append("</div>")
    if groups["legacy"]:
        P.append("<h2>Legacy Media</h2>")
        for m in groups["legacy"]:
            P.append(_media_block(m,output_html,person_name=p["display_name"],db=db))
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
            refs=citation_suffix([source_label(x) for x in family_sources(db,family_id)])
            text=" — ".join(esc(x) for x in (f["marriage_date"],f["marriage_place"]) if x)
            P.append("<p><strong>Marriage:</strong> "+text+(f" <span class='citation-ref'>{esc(refs)}</span>" if refs else "")+"</p>")
        for m in o["wedding_photos"]:
            P.append(_media_block(m,output_html,hero=True,family_names=family_names,db=db))
        for i,m in enumerate(o["marriage_documents"]):
            if i==0 and Path(m["file_path"]).suffix.lower()==".pdf":
                P.append(_fitted_document_block(m,output_html,"Marriage Documents",family_names=family_names,db=db))
            else:
                P.append(_media_block(m,output_html,family_names=family_names,db=db))

    if h:P.append(_person_section(db,h["id"],output_html,person_anchors.get(h["id"])))
    if w:P.append(_person_section(db,w["id"],output_html,person_anchors.get(w["id"])))

    surfaced={m["id"] for m in o["wedding_photos"]+o["marriage_documents"]}
    extra=[m for m in family_media(db,family_id) if m["id"] not in surfaced]
    if extra:
        P.append("<div class='pagebreak'></div><h2>Family Documents &amp; Media</h2>")
        for m in extra:P.append(_media_block(m,output_html,family_names=family_names,db=db))

    P.append("<div class='pagebreak'></div><h2>Children</h2>")
    kids=children(db,family_id)
    if kids:
        P.append("<ul class='children-list'>")
        for ch in kids:
            d=life_dates(db,ch["id"])
            dates=[]
            if d["birth"]:dates.append("b. "+d["birth"])
            if d["death"]:dates.append("d. "+d["death"])
            date_html=(" <span class='person-dates'>— "+esc(" — ".join(dates))+"</span>") if dates else ""
            P.append("<li class='person-line'><strong class='person-name'>"+esc(ch["display_name"])+"</strong>"+date_html+"</li>")
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
       f"<section class='title-page'><img class='publishing-mark' src='{publishing_mark_uri()}' alt='Reunion Companion'><div class='chapter-kicker'>Reunion Companion</div>",
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
        # Keep the user-facing error concise, but preserve the complete import
        # traceback in the frozen backend log for diagnosis.
        import traceback
        traceback.print_exc()
        raise RuntimeError(
            f"PDF publishing runtime could not be loaded: {type(e).__name__}: {e}"
        ) from e
    HTML(filename=str(html_path),base_url=str(html_path.parent)).write_pdf(str(pdf_path))
    return pdf_path

def write_book_pdf(db,start_pid,path=None,generations=4,theme=DEFAULT_THEME):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(start_pid,)).fetchone()["display_name"]
    pdf=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Professional_Family_History.pdf")
    pdf.parent.mkdir(parents=True,exist_ok=True)
    # HTML and copied/rendered assets are implementation details for PDF-only publishing.
    # Keep them outside the report directory and remove them automatically after rendering.
    with tempfile.TemporaryDirectory(prefix="reunion-companion-pdf-") as td:
        html=Path(td)/(pdf.stem+".html")
        write_book(db,start_pid,html,generations,theme)
        export_pdf_from_html(html,pdf)
    return pdf

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
