from __future__ import annotations
from pathlib import Path
import html,re
from .discovery import person_evidence_summary,relationship_connections,family_snapshot
from .intelligence import person_quality

CSS="""
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif; color:#222; line-height:1.45; max-width: 900px; margin: 0 auto; font-size: 10.5pt; }
h1 { font-size: 24pt; margin:0 0 3mm; border-bottom:2px solid #333; padding-bottom:2mm; }
h2 { font-size: 15pt; margin-top:7mm; border-bottom:1px solid #bbb; padding-bottom:1mm; page-break-after:avoid; }
h3 { font-size: 12pt; margin-top:5mm; page-break-after:avoid; }
p { margin: 2.5mm 0; }
ul { margin-top:2mm; padding-left:6mm; }
li { margin:1.2mm 0; }
.meta { color:#666; font-size:9pt; }
.event { margin:1.5mm 0; }
.note { white-space:pre-wrap; }
.media-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:5mm; }
.media-card { break-inside:avoid; border:1px solid #ddd; padding:3mm; }
.media-card img { max-width:100%; max-height:90mm; display:block; margin:0 auto 2mm; object-fit:contain; }
.small { font-size:8.5pt; color:#666; overflow-wrap:anywhere; }
.source { break-inside:avoid; }
.warning { border-left:3px solid #777; padding-left:3mm; }
.pagebreak { break-before:page; }
@media print { a { color:#222; text-decoration:none; } }
"""

def esc(x):return html.escape(str(x or ""))
def slug(s):return re.sub(r"[^A-Za-z0-9._-]+","_",s).strip("_") or "report"

def default_report_dir():
    p=Path.home()/"Documents"/"Reunion Companion Reports";p.mkdir(parents=True,exist_ok=True);return p

def _image_uri(path):
    p=Path(path).expanduser()
    if not p.exists():return None
    if p.suffix.lower() not in ('.jpg','.jpeg','.png','.gif','.webp'):return None
    return p.resolve().as_uri()

def _source_rows(db,pid):
    return db.execute("""
      SELECT DISTINCT s.* FROM sources s WHERE s.id IN (
        SELECT source_id FROM person_sources WHERE person_id=?
        UNION SELECT es.source_id FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=?
        UNION SELECT ns.source_id FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=?
        UNION SELECT fs.source_id FROM family_sources fs JOIN family_members fm ON fm.family_id=fs.family_id WHERE fm.person_id=?
      ) ORDER BY s.id""",(pid,pid,pid,pid)).fetchall()

def _all_media(db,pid):
    return db.execute("""
      SELECT DISTINCT m.* FROM media m WHERE m.id IN (
        SELECT media_id FROM person_media WHERE person_id=?
        UNION SELECT em.media_id FROM event_media em JOIN events e ON e.id=em.event_id WHERE e.person_id=?
        UNION SELECT fm.media_id FROM family_media fm JOIN family_members fmem ON fmem.family_id=fm.family_id WHERE fmem.person_id=?
      ) ORDER BY m.id""",(pid,pid,pid)).fetchall()

def person_report_html(db,pid):
    d=person_evidence_summary(db,pid);p=d['person'];c=d['connections'];q=person_quality(db,pid)
    parts=["<!doctype html><html><head><meta charset='utf-8'>",f"<title>{esc(p['display_name'])}</title><style>{CSS}</style></head><body>"]
    parts += [f"<h1>{esc(p['display_name'])}</h1>",f"<div class='meta'>Companion ID {p['id']} · GEDCOM {esc(p['gedcom_xref'])} · Sex {esc(p['sex'])}</div>"]
    parts.append("<h2>Life Record</h2>")
    if d['events']:
        for e in d['events']:
            bits=[e['event_type']]+[x for x in (e['date_text'],e['place_text'],e['value_text']) if x and x!='Y']
            parts.append("<div class='event'>"+" — ".join(esc(x) for x in bits)+"</div>")
    else:parts.append("<p>No events recorded.</p>")
    parts.append("<h2>Family</h2>")
    for key,label in [('parents','Parents'),('spouses','Spouses'),('children','Children'),('siblings','Siblings')]:
        parts.append(f"<h3>{label}</h3><ul>")
        parts += [f"<li>{esc(x['display_name'])} <span class='meta'>[ID {x['id']}]</span></li>" for x in c[key]] or ["<li>None recorded</li>"]
        parts.append("</ul>")
    notes=db.execute("SELECT * FROM notes WHERE person_id=? ORDER BY id",(pid,)).fetchall()
    if notes:
        parts.append("<h2>Notes</h2>")
        for n in notes:
            parts.append(f"<h3>{esc(n['note_type'] or n['gedcom_tag'] or 'Note')}</h3>")
            parts.append(f"<div class='note'>{esc(n['text'])}</div>")
    media=_all_media(db,pid)
    if media:
        parts.append("<h2>Documents &amp; Media</h2><div class='media-grid'>")
        for m in media:
            uri=_image_uri(m['file_path']);title=m['title'] or Path(m['file_path']).name
            parts.append("<div class='media-card'>")
            if uri:parts.append(f"<img src='{esc(uri)}' alt='{esc(title)}'>")
            status="Available" if m['exists_on_disk'] else "Missing"
            parts.append(f"<strong>{esc(title)}</strong><div class='small'>{status} · {esc(m['file_path'])}</div></div>")
        parts.append("</div>")
    src=_source_rows(db,pid)
    if src:
        parts.append("<h2>Sources</h2><ol>")
        for s in src:
            txt=s['display_text'] or s['text'] or s['title'] or '(undescribed source)'
            extra=f" — {s['source_type']}" if s['source_type'] else ""
            parts.append(f"<li class='source'><strong>{esc(s['gedcom_xref'])}</strong> — {esc(txt)}{esc(extra)}</li>")
        parts.append("</ol>")
    parts.append("<h2>Research Review</h2>")
    if q['conflicts'] or q['cautions']:
        parts.append("<div class='warning'><ul>")
        for typ,msg,snip in q['cautions']:
            parts.append(f"<li><strong>{esc(typ)}:</strong> {esc(msg)}"+(f" — {esc(snip)}" if snip else "")+"</li>")
        for typ,vals in q['conflicts']:
            parts.append(f"<li><strong>Potential {esc(typ)} conflict:</strong> "+" | ".join(esc(" — ".join(x for x in v if x)) for v in vals)+"</li>")
        parts.append("</ul></div>")
    else:parts.append("<p>No obvious research-quality issues detected by the Companion.</p>")
    parts.append("<p class='meta'>Generated from the current Reunion Companion snapshot. Research-review flags describe the exported database evidence and are not historical verdicts.</p>")
    parts.append("</body></html>")
    return ''.join(parts)

def write_person_report(db,pid,path=None):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()['display_name']
    p=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Person_Report.html")
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(person_report_html(db,pid),encoding='utf-8');return p

def family_report_html(db,pid):
    p=db.execute("SELECT * FROM people WHERE id=?",(pid,)).fetchone();snaps=family_snapshot(db,pid)
    parts=["<!doctype html><html><head><meta charset='utf-8'>",f"<title>Family of {esc(p['display_name'])}</title><style>{CSS}</style></head><body>",f"<h1>Family of {esc(p['display_name'])}</h1>"]
    if not snaps:parts.append("<p>No family records found.</p>")
    for f,members in snaps:
        parts.append(f"<h2>{esc(f['gedcom_xref'] or 'Family '+str(f['id']))}</h2>")
        if f['marriage_date'] or f['marriage_place']:
            parts.append("<p><strong>Marriage:</strong> "+" — ".join(esc(x) for x in (f['marriage_date'],f['marriage_place']) if x)+"</p>")
        parts.append("<ul>")
        for m in members:
            marker=" ←" if m['id']==pid else ""
            parts.append(f"<li><strong>{esc(m['role'].title())}:</strong> {esc(m['display_name'])}{marker}</li>")
        parts.append("</ul>")
        fm=db.execute("SELECT m.* FROM media m JOIN family_media fm ON fm.media_id=m.id WHERE fm.family_id=? ORDER BY m.id",(f['id'],)).fetchall()
        if fm:
            parts.append("<h3>Family documents &amp; media</h3><ul>")
            for x in fm:parts.append(f"<li>{esc(x['title'] or Path(x['file_path']).name)} <span class='small'>— {esc(x['file_path'])}</span></li>")
            parts.append("</ul>")
        fs=db.execute("SELECT s.* FROM sources s JOIN family_sources fs ON fs.source_id=s.id WHERE fs.family_id=? ORDER BY s.id",(f['id'],)).fetchall()
        if fs:
            parts.append("<h3>Family sources</h3><ul>")
            for s in fs:parts.append(f"<li>{esc(s['gedcom_xref'])} — {esc(s['display_text'] or s['text'] or s['title'] or '(undescribed source)')}</li>")
            parts.append("</ul>")
    parts.append("<p class='meta'>Generated from the current Reunion Companion snapshot.</p></body></html>")
    return ''.join(parts)

def write_family_report(db,pid,path=None):
    name=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()['display_name']
    p=Path(path).expanduser() if path else default_report_dir()/(slug(name)+"_Family_Report.html")
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(family_report_html(db,pid),encoding='utf-8');return p
