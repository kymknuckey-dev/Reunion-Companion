from __future__ import annotations
from pathlib import Path
import html,re,base64,mimetypes
from .publishing_v7 import CSS,esc,slug,default_report_dir,_source_rows,_all_media
from .story_engine import story_sections
from .timeline_engine import intelligent_timeline
from .knowledge_card import knowledge_card
from .audit_engine import audit_person

EXTRA_CSS="""
.cover { border-bottom:3px solid #333; padding-bottom:5mm; margin-bottom:7mm; }
.card { display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin:5mm 0; }
.metric { border:1px solid #ccc; padding:3mm; break-inside:avoid; }
.metric strong { display:block; font-size:14pt; }
.chapter { break-inside:avoid; margin-bottom:4mm; }
.provenance { border-top:1px solid #aaa; margin-top:8mm; padding-top:3mm; font-size:8.5pt; color:#666; }
"""


def _embedded_image_uri(path):
    """Return a self-contained data URI for browser-supported local images.

    Foundation 8 originally emitted absolute file:// URLs. Those URLs are valid,
    but some browser/security combinations do not load local sibling resources
    reliably. Embedding the bytes makes the biography portable and removes that
    browser dependency.
    """
    p=Path(path).expanduser()
    if not p.is_file():
        return None
    ext=p.suffix.lower()
    allowed={".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
             ".gif":"image/gif",".webp":"image/webp"}
    mime=allowed.get(ext)
    if not mime:
        return None
    try:
        payload=base64.b64encode(p.read_bytes()).decode("ascii")
    except OSError:
        return None
    return f"data:{mime};base64,{payload}"


def biography_html(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone()
    card=knowledge_card(db,pid); audit=audit_person(db,pid)
    parts=["<!doctype html><html><head><meta charset='utf-8'>",
           f"<title>{esc(p['display_name'])} — Biography</title><style>{CSS}{EXTRA_CSS}</style></head><body>",
           "<div class='cover'>",f"<h1>{esc(p['display_name'])}</h1>",
           "<div class='meta'>Reunion Companion · Genealogical Intelligence Biography</div></div>"]
    parts.append("<div class='card'>")
    for label,value in (("Evidence",f"{card['evidence']}%"),("Events",card["events"]),("Sources",card["sources"]),
                        ("Media",card["media"]),("Notes",card["notes"]),("Research items",card["research_items"])):
        parts.append(f"<div class='metric'><span>{esc(label)}</span><strong>{esc(value)}</strong></div>")
    parts.append("</div>")

    parts.append("<h2>Life Story</h2>")
    for heading,txt in story_sections(db,pid):
        parts.append(f"<h3>{esc(heading)}</h3><p>{esc(txt)}</p>")

    parts.append("<h2>Life Chapters</h2>")
    for chapter,events in intelligent_timeline(db,pid):
        parts.append(f"<div class='chapter'><h3>{esc(chapter)}</h3><ul>")
        for e in events:
            bits=[e["event_type"]]+[x for x in (e["date_text"],e["place_text"],e["value_text"]) if x and x!="Y"]
            parts.append("<li>"+" — ".join(esc(x) for x in bits)+"</li>")
        parts.append("</ul></div>")

    media=_all_media(db,pid)
    if media:
        parts.append("<h2>Documents &amp; Media</h2><div class='media-grid'>")
        for m in media:
            title=m["title"] or Path(m["file_path"]).name
            uri=_embedded_image_uri(m["file_path"])
            parts.append("<div class='media-card'>")
            if uri:parts.append(f"<img src='{esc(uri)}' alt='{esc(title)}'>")
            parts.append(f"<strong>{esc(title)}</strong><div class='small'>{'Available' if m['exists_on_disk'] else 'Missing'} · {esc(m['file_path'])}</div></div>")
        parts.append("</div>")

    src=_source_rows(db,pid)
    if src:
        parts.append("<h2>Sources</h2><ol>")
        for s in src:
            parts.append(f"<li><strong>{esc(s['gedcom_xref'])}</strong> — {esc(s['display_text'] or s['text'] or s['title'] or '(undescribed source)')}</li>")
        parts.append("</ol>")

    parts.append("<h2>Research Review</h2>")
    parts.append(f"<p><strong>Evidence linkage:</strong> {audit['evidence']}% · <strong>Research readiness:</strong> {audit['completeness']}%</p>")
    if audit["issues"]:
        parts.append("<ul>")
        for priority,area,msg,detail in audit["issues"]:
            parts.append(f"<li><strong>{esc(priority)} — {esc(area)}:</strong> {esc(msg)}"+(f" — {esc(detail)}" if detail else "")+"</li>")
        parts.append("</ul>")
    else:parts.append("<p>No obvious research-review items detected.</p>")

    parts.append("<div class='provenance'>Generated from the current Reunion Companion snapshot. Narrative text is assembled deterministically from imported events and notes; authored note text is preserved. Evidence and audit scores describe visible database linkage, not historical truth.</div>")
    parts.append("</body></html>")
    return "".join(parts)

def write_biography(db,pid,path=None):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()["display_name"]
    p=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Biography.html")
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(biography_html(db,pid),encoding="utf-8");return p
