from __future__ import annotations
from pathlib import Path
from .publishing_v7 import CSS,esc,slug,default_report_dir,_all_media
from .publishing_v8 import _embedded_image_uri
from .profile_builder import build_profile
from .story_engine import story_sections
from .research_timeline import research_timeline_rows
from .confidence_engine import confidence_profile

EXTRA="""
.summary { display:grid; grid-template-columns:repeat(4,1fr); gap:3mm; margin:5mm 0 7mm; }
.box { border:1px solid #bbb; padding:3mm; break-inside:avoid; }
.box strong { display:block; font-size:14pt; }
.warning { border-left:3px solid #777; padding-left:3mm; margin:2mm 0; }
.doc-card { border:1px solid #ccc; padding:3mm; margin:2mm 0; break-inside:avoid; }
"""

def profile_html(db,pid):
    d=build_profile(db,pid);p=d["person"];evid=d["evidence"]
    P=["<!doctype html><html><head><meta charset='utf-8'>",f"<title>{esc(p['display_name'])} — Research Profile</title>",f"<style>{CSS}{EXTRA}</style></head><body>",f"<h1>{esc(p['display_name'])}</h1>","<div class='meta'>Reunion Companion · Foundation 09 Research Intelligence Profile</div>","<div class='summary'>"]
    metrics=(("Status",d["status"]),("Confidence",f"{d['confidence']}%"),("Evidence",f"{d['card']['evidence']}%"),("Research items",len(d["opportunities"])),("Sources",len(evid["sources"])),("Citations",evid["citation_count"]),("Media",d["card"]["media"]),("Notes",d["card"]["notes"]))
    for label,val in metrics:P.append(f"<div class='box'><span>{esc(label)}</span><strong>{esc(val)}</strong></div>")
    P.append("</div><h2>Life Story</h2>")
    for heading,txt in story_sections(db,pid):P.append(f"<h3>{esc(heading)}</h3><p>{esc(txt)}</p>")
    P.append("<h2>Integrated Timeline</h2><ul>")
    for r in research_timeline_rows(db,pid):P.append(f"<li><strong>{esc(r['date'] or '(undated)')} — {esc(r['label'])}</strong> <span class='small'>[{esc(r['kind'])}]</span><br>{esc(r['text'])}</li>")
    P.append("</ul><h2>Research Confidence</h2>")
    for x in confidence_profile(db,pid):P.append(f"<div class='doc-card'><strong>{esc(x.area)} — {x.score}% ({esc(x.level)})</strong><br>{esc(x.reason)}</div>")
    P.append(f"<h2>Evidence</h2><p>Supported events: {evid['supported_events']} / {evid['total_events']} · Supported notes: {evid['supported_notes']} / {evid['total_notes']}</p>")
    if evid["sources"]:
        P.append("<ol>")
        for s in evid["sources"]:
            text=s["display_text"] or s["text"] or s["title"] or "(undescribed source)"
            P.append(f"<li><strong>{esc(s['gedcom_xref'])}</strong> — {esc(text)}</li>")
        P.append("</ol>")
    media=_all_media(db,pid)
    if media:
        P.append("<h2>Documents &amp; Media</h2>")
        for m in media:
            title=m["title"] or Path(m["file_path"]).name;uri=_embedded_image_uri(m["file_path"])
            P.append("<div class='doc-card'>")
            if uri:P.append(f"<img src='{esc(uri)}' alt='{esc(title)}' style='max-width:70mm;max-height:55mm;float:right;margin-left:4mm'>")
            P.append(f"<strong>{esc(title)}</strong><br><span class='small'>{'Available' if m['exists_on_disk'] else 'Missing'} · {esc(m['file_path'])}</span><div style='clear:both'></div></div>")
    P.append("<h2>Research Review</h2>")
    if d["opportunities"]:
        for priority,area,msg,detail in d["opportunities"]:
            P.append(f"<div class='warning'><strong>{esc(priority)} — {esc(area)}</strong><br>{esc(msg)}")
            if detail:P.append(f"<br><span class='small'>{esc(detail)}</span>")
            P.append("</div>")
    else:P.append("<p>No obvious review items detected.</p>")
    P.append("<div class='provenance'><strong>Research interpretation:</strong> Confidence, evidence and gap indicators describe what is visible in the current imported Reunion snapshot. They do not establish historical truth and do not modify Reunion.</div></body></html>")
    return "".join(P)

def write_profile(db,pid,path=None):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()["display_name"]
    p=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Research_Profile.html")
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(profile_html(db,pid),encoding="utf-8");return p
