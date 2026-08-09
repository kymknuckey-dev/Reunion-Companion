from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs,quote
from pathlib import Path
import html,re,webbrowser,threading,traceback

from .database import connect
from .beta_ui_service import search_people,person_workspace,family_workspace,family_choices_for_person
from .beta2_research import person_research_model,place_variants,source_explorer,media_explorer
from .timeline_engine import timeline_for_person,event_detail,source_label
from .beta3_data_manager import current_gedcom,import_history,seed_history_from_current,reload_current,staged_import,dataset_counts
from .beta3_quality import quick_wins,quality_items,person_quality
from .beta3_publishing import (
    publication_history,family_chapter_html,family_chapter_pdf,
    descendant_chart,person_output,open_output
)

CSS="""
:root{--bg:#f4f4f1;--card:#fff;--text:#222;--muted:#6c6c68;--line:#d9d9d4;--good:#246b3a;--warn:#945d00;--accent:#36424e;--soft:#eef0ed;--danger:#9c2f2f}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--text)}
header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:14px 22px;display:flex;gap:20px;align-items:center}
header a{color:var(--text);text-decoration:none;margin-right:13px}
main{max-width:1200px;margin:24px auto;padding:0 22px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.search{display:flex;gap:10px}
.stack{display:flex;flex-direction:column;gap:9px}
input,button,select{font:inherit;padding:10px 12px;border:1px solid #bbb;border-radius:7px;background:#fff}
input{flex:1}
button,.button{background:var(--accent);color:#fff;border-color:var(--accent);text-decoration:none;display:inline-block;padding:10px 13px;border-radius:7px;cursor:pointer}
.secondary{background:#fff;color:var(--text)}
.result{display:block;padding:10px 0;border-bottom:1px solid #eee;color:var(--text);text-decoration:none}
.meta,.small{color:var(--muted)}
.small{font-size:12px;overflow-wrap:anywhere}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}
.tabs a{padding:8px 10px;background:#fff;border:1px solid var(--line);border-radius:7px;text-decoration:none;color:var(--text)}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:19px;margin:0 0 12px}
h3{font-size:15px;margin:14px 0 6px}
.topic{padding:0 0 12px;margin:0 0 12px;border-bottom:1px solid #eee}
.badge{display:inline-block;border-radius:999px;padding:4px 8px;font-size:12px}
.good{background:#e5f2e8;color:var(--good)}
.warn{background:#fff0d8;color:var(--warn)}
.info{background:#edf1f5;color:#3f5266}
.kpi{font-size:27px;font-weight:700}
.quick{display:block;text-decoration:none;color:var(--text)}
.quick:hover{border-color:#999}
.timeline{position:relative;margin-left:12px}
.timeline:before{content:"";position:absolute;left:8px;top:0;bottom:0;width:2px;background:#d7d7d2}
.event-card{position:relative;margin:0 0 18px 30px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:15px}
.event-card:before{content:"";position:absolute;left:-27px;top:18px;width:12px;height:12px;border-radius:50%;background:var(--accent);border:3px solid var(--bg)}
.event-head{display:flex;justify-content:space-between;gap:15px}
.panel-note{background:var(--soft);border-radius:7px;padding:10px;margin-top:10px}
table{width:100%;border-collapse:collapse}
td,th{text-align:left;padding:8px;border-bottom:1px solid #eee;vertical-align:top}
pre.note{white-space:pre-wrap;font-family:inherit}
.error{border-left:4px solid var(--danger)}
.timeline-toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.timeline-toolbar a{padding:8px 11px;border:1px solid var(--line);border-radius:999px;text-decoration:none;color:var(--text);background:#fff}
.timeline-toolbar a.active{background:var(--accent);color:#fff}
.timeline-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.timeline-story{font-size:16px;line-height:1.55;margin:10px 0}
.event-link{text-decoration:none;color:inherit}
.event-link h2:hover{text-decoration:underline}
.observation{margin-top:8px;padding:8px 10px;background:#fff7e8;border-radius:6px;font-size:13px}
.evidence-list{margin:8px 0 0;padding-left:20px}
.event-navigation{display:flex;justify-content:space-between;gap:12px}
.raw-grid{display:grid;grid-template-columns:minmax(130px,190px) 1fr;gap:7px 15px}
"""

def esc(v):
    return html.escape("" if v is None else str(v))

def layout(title,body):
    return f"""<!doctype html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{esc(title)} — Reunion Companion Beta 3.2 Sprint 1</title><style>{CSS}
</style></head><body>
<header><strong>Reunion Companion</strong><nav>
<a href='/'>Search</a><a href='/data'>Data</a><a href='/quality'>Quality</a>
<a href='/research'>Research</a><a href='/places'>Places</a><a href='/sources'>Sources</a>
<a href='/media'>Media</a><a href='/publishing'>Publishing</a>
</nav><span class='meta'>Beta 3.2 · Sprint 1</span></header><main>{body}</main></body></html>"""

def error_page(title,error):
    return layout(title,f"""<div class='card error'><h1>{esc(title)}</h1>
<p>Companion could not render this page.</p>
<pre class='note'>{esc(error)}</pre>
<p class='meta'>The local UI remains running. Return to <a href='/'>Search</a>.</p></div>""")

def home(db,q=""):
    rows=""
    if q:
        rows="".join(
            f"<a class='result' href='/person/{p['id']}'><strong>{esc(p['display_name'])}</strong> "
            f"<span class='meta'>{esc(p['gedcom_xref'])}</span></a>"
            for p in search_people(db,q)
        )
    qw=quick_wins(db)
    if q:
        lower=f"<div class='card'><h2>People</h2>{rows or '<p>No matches.</p>'}</div>"
    else:
        lower=f"""<div class='grid'>
<a class='card quick' href='/quality'><h2>Data Quality</h2>
<div class='kpi'>{sum(qw.values()):,}</div><p class='meta'>Current measurable cleanup opportunities</p></a>
<a class='card quick' href='/data'><h2>Data Manager</h2>
<p>Reload the current GEDCOM or import a newer Reunion export.</p></a>
<a class='card quick' href='/publishing'><h2>Publishing Centre</h2>
<p>Web, biographies, family chapters, books and print-ready PDF.</p></a></div>"""
    return layout("Search",f"""<div class='card'><h1>Search Reunion</h1>
<p class='meta'>Reload, review, improve in Reunion, reload, and publish.</p>
<form class='search' action='/' method='get'><input name='q' value='{esc(q)}' placeholder='Search for a person'>
<button>Search</button></form></div>{lower}""")

def data_page(db,msg=""):
    seed_history_from_current(db)
    cur=current_gedcom(db)
    hist=import_history(db)
    counts=dataset_counts(db)
    stats="".join(f"<div><strong>{esc(k.title())}</strong><div class='kpi'>{v:,}</div></div>" for k,v in counts.items())
    history=""
    for x in hist:
        diff=", ".join(f"{k} {v:+d}" for k,v in x["diff"].items() if v)
        history+=f"""<div class='topic'><strong>{esc(Path(x['source_path']).name)}</strong><br>
<span class='small'>{esc(x['imported_at'])}</span>
<div>{esc(diff or 'Baseline / no count changes')}</div></div>"""
    message=f"<div class='card'><strong>{esc(msg)}</strong></div>" if msg else ""
    current=esc(cur["source_path"]) if cur else "No GEDCOM recorded"
    disabled="" if cur else "disabled"
    return layout("Data Manager",f"""<h1>Data Manager</h1>{message}
<div class='card'><h2>Current GEDCOM</h2><div class='small'>{current}</div>
<div class='grid' style='margin-top:15px'>{stats}</div>
<form method='post' action='/data/reload' style='margin-top:16px'><button {disabled}>Reload Current GEDCOM</button></form></div>
<div class='card'><h2>Import / Replace GEDCOM</h2>
<p class='meta'>Enter the full path to a Reunion GEDCOM export. The new import is staged before it replaces the working dataset.</p>
<form class='search' method='post' action='/data/import'>
<input name='path' placeholder='/Users/.../Family.ged'><button>Import GEDCOM</button></form></div>
<div class='card'><h2>Import History</h2>{history or '<p>No Companion import history yet.</p>'}</div>""")

def quality_page(db):
    q=quick_wins(db)
    cards=[
        ("Place variants","place_variant_groups","/places"),
        ("Unsourced events","unsourced_events","/quality/items?kind=unsourced-events"),
        ("Missing birth places","missing_birth_place","/quality/items?kind=missing-birth-place"),
        ("Missing death places","missing_death_place","/quality/items?kind=missing-death-place"),
        ("Missing media","missing_media","/quality/items?kind=missing-media"),
        ("Legacy PICT","legacy_pict","/quality/items?kind=legacy-pict"),
        ("Untitled sources","untitled_sources","/quality/items?kind=untitled-sources"),
        ("Duplicate source titles","duplicate_source_titles","/quality/items?kind=duplicate-sources"),
    ]
    body="<h1>Data Quality Centre</h1><p class='meta'>Review here, change the authoritative record in Reunion, then reload the GEDCOM.</p><div class='grid'>"
    for label,key,url in cards:
        body+=f"<a class='card quick' href='{url}'><h2>{esc(label)}</h2><div class='kpi'>{q[key]:,}</div><p class='meta'>Review items</p></a>"
    return layout("Data Quality",body+"</div>")

def quality_items_page(db,kind):
    items=quality_items(db,kind)
    body=f"<h1>{esc(kind.replace('-',' ').title())}</h1><div class='card'><p>{len(items):,} item(s)</p>"
    for x in items:
        if x.get("person_id"):
            body+=f"""<a class='result' href='/person/{x['person_id']}?tab=data-quality'>
<strong>{esc(x.get('display_name'))}</strong> — {esc(x.get('event_type') or '')} {esc(x.get('date_text') or '')}</a>"""
        else:
            title=x.get("title") or x.get("display_text") or x.get("file_path") or x.get("ids") or "Item"
            body+=f"<div class='topic'><strong>{esc(title)}</strong><div class='small'>{esc(x.get('file_path') or '')}</div></div>"
    return layout("Quality Items",body+"</div>")

def timeline_tab(db,pid,view="story"):
    model=timeline_for_person(db,pid)
    if not model:return "<div class='card'>Timeline unavailable.</div>"
    if view not in {"story","research","data"}:view="story"
    summary=model["summary"]
    body=f"""<div class='card'><h2>Life Timeline</h2>
<p class='meta'>One event-driven timeline. Choose how much detail you want to see.</p>
<div class='timeline-toolbar'>
<a class='{"active" if view=="story" else ""}' href='/person/{pid}?tab=timeline&view=story'>Story</a>
<a class='{"active" if view=="research" else ""}' href='/person/{pid}?tab=timeline&view=research'>Research</a>
<a class='{"active" if view=="data" else ""}' href='/person/{pid}?tab=timeline&view=data'>Data</a>
</div>
<div class='timeline-meta'><span class='badge info'>{summary['event_count']} events</span>
<span class='badge info'>{summary['dated_count']} dated</span>
<span class='badge info'>{summary['supported_count']} with linked evidence</span>
<span class='badge info'>{summary['observation_count']} review observations</span></div></div>
<div class='timeline'>"""
    for e in model["events"]:
        evidence="<span class='badge good'>Linked evidence</span>" if e["evidence_status"]=="supported" else "<span class='badge warn'>No linked evidence</span>"
        body+=f"<section class='event-card' id='event-{e['id']}'><div class='event-head'><div><a class='event-link' href='/event/{e['id']}?view={view}'><h2>{esc(e['type'])}</h2></a><div><strong>{esc(e['date']) or 'Undated'}</strong></div></div>{evidence}</div>"
        if view=="story":
            body+=f"<div class='timeline-story'>{esc(e['story'])}</div>"
            meta=[]
            if e["age"]:meta.append(f"Age {e['age']}")
            if e["since_previous"]:meta.append(f"{e['since_previous']} since previous dated event")
            if meta:body+="<div class='meta'>"+" · ".join(esc(x) for x in meta)+"</div>"
            if e["note"]:body+=f"<div class='panel-note'><strong>Note</strong><br>{esc(e['note'])}</div>"
        elif view=="research":
            if e["place"]:body+=f"<p><strong>Place</strong><br>{esc(e['place'])}</p>"
            if e["value"]:body+=f"<p><strong>Detail</strong><br>{esc(e['value'])}</p>"
            if e["age"]:body+=f"<p><strong>Age</strong> {esc(e['age'])}</p>"
            if e["note"]:body+=f"<div class='panel-note'><strong>Event note</strong><br>{esc(e['note'])}</div>"
            body+=f"<div class='timeline-meta'><span class='badge info'>{e['source_count']} source(s)</span><span class='badge info'>{e['media_count']} media item(s)</span></div>"
            if e["sources"]:
                body+="<ul class='evidence-list'>"+"".join(f"<li>{esc(source_label(s))}</li>" for s in e["sources"])+"</ul>"
            for o in e["observations"]:body+=f"<div class='observation'>Review: {esc(o)}</div>"
        else:
            rows=[
                ("Event ID",e["id"]),("GEDCOM Tag",e["gedcom_tag"]),("Original Date",e["date"]),
                ("Date Precision",e["date_precision"]),("Date Qualifier",e["date_qualifier"]),
                ("Place",e["place"]),("Value",e["value"]),("Source Count",e["source_count"]),
                ("Media Count",e["media_count"]),("Age",e["age"]),
                ("Since Previous",e["since_previous"]),("Until Next",e["until_next"])
            ]
            body+="<div class='raw-grid'>"+"".join(f"<strong>{esc(k)}</strong><span>{esc(v)}</span>" for k,v in rows)+"</div>"
            for o in e["observations"]:body+=f"<div class='observation'>Review: {esc(o)}</div>"
        body+=f"<p><a href='/event/{e['id']}?view={view}'>Open event workspace →</a></p></section>"
    return body+"</div>"

def event_page(db,event_id,view="research"):
    d=event_detail(db,event_id)
    if not d:return layout("Event not found","<div class='card'><h1>Event not found</h1></div>")
    e=d["event"];p=d["person"]
    body=f"""<p><a href='/person/{p['id']}?tab=timeline&view={view}'>← {esc(p['display_name'])} timeline</a></p>
<h1>{esc(e['type'])}</h1><div class='meta'>{esc(p['display_name'])} · Event {e['id']}</div>
<div class='grid'><div class='card'><h2>Overview</h2>
<div class='topic'><h3>Date</h3><div>{esc(e['date']) or 'Not recorded'}</div><div class='small'>Precision: {esc(e['date_precision'])}{' · '+esc(e['date_qualifier']) if e['date_qualifier'] else ''}</div></div>
<div class='topic'><h3>Place</h3><div>{esc(e['place']) or 'Not recorded'}</div></div>
<div class='topic'><h3>Detail</h3><div>{esc(e['value']) or '—'}</div></div>
<div class='topic'><h3>Age</h3><div>{esc(e['age']) or 'Not calculable from available dates'}</div></div>
</div>
<div class='card'><h2>Timeline Context</h2>
<p>Since previous dated event: <strong>{esc(e['since_previous']) or '—'}</strong></p>
<p>Until next dated event: <strong>{esc(e['until_next']) or '—'}</strong></p>
<p>Previous event: {esc(d['previous_event']['type']) if d['previous_event'] else '—'}</p>
<p>Next event: {esc(d['next_event']['type']) if d['next_event'] else '—'}</p>
</div></div>
<div class='card'><h2>Evidence</h2>"""
    if e["sources"]:
        for s in e["sources"]:
            body+=f"<div class='topic'><strong>{esc(source_label(s))}</strong><div class='small'>{esc(s.get('gedcom_xref'))}</div></div>"
    else:body+="<p>No source is directly linked to this event.</p>"
    body+="</div><div class='card'><h2>Media</h2>"
    if e["media"]:
        for m in e["media"]:body+=f"<div class='topic'><strong>{esc(m.get('title') or Path(m.get('file_path') or '').name)}</strong><div class='small'>{esc(m.get('file_path'))}</div></div>"
    else:body+="<p>No media is directly linked to this event.</p>"
    body+="</div><div class='card'><h2>Notes</h2>"+(f"<pre class='note'>{esc(e['note'])}</pre>" if e["note"] else "<p>No event note.</p>")+"</div>"
    body+="<div class='card'><h2>Related People</h2>"
    if e["related_people"]:
        for r in e["related_people"]:body+=f"<a class='result' href='/person/{r['id']}'><strong>{esc(r['display_name'])}</strong> <span class='meta'>{esc(r['relation'])}</span></a>"
    else:body+="<p>No event-specific related people inferred.</p>"
    body+="</div><div class='card'><h2>Review Observations</h2>"
    if e["observations"]:
        for o in e["observations"]:body+=f"<div class='observation'>{esc(o)}</div>"
    else:body+="<p>No deterministic observations for this event.</p>"
    body+="</div><div class='card'><h2>Raw Event Data</h2><div class='raw-grid'>"
    for k,v in [("Event ID",e["id"]),("GEDCOM Tag",e["gedcom_tag"]),("Original Date",e["date"]),("Place",e["place"]),("Value",e["value"]),("Date precision",e["date_precision"])]:
        body+=f"<strong>{esc(k)}</strong><span>{esc(v)}</span>"
    body+="</div></div>"
    prev=d["previous_event"];nxt=d["next_event"]
    body+="<div class='event-navigation'>"
    body+=(f"<a class='button secondary' href='/event/{prev['id']}?view={view}'>← {esc(prev['type'])}</a>" if prev else "<span></span>")
    body+=(f"<a class='button secondary' href='/event/{nxt['id']}?view={view}'>{esc(nxt['type'])} →</a>" if nxt else "<span></span>")
    return layout(f"{e['type']} — {p['display_name']}",body)

def person_page(db,pid,tab="overview",view="story"):
    w=person_workspace(db,pid)
    if not w:
        return layout("Not found","<div class='card'><h1>Person not found</h1></div>")
    p=w["person"]
    tabs=["overview","timeline","biography","family","sources","media","confidence","research","data-quality","publish"]
    nav="<div class='tabs'>"+"".join(f"<a href='/person/{pid}?tab={t}'>{esc(t.replace('-',' ').title())}</a>" for t in tabs)+"</div>"

    if tab=="overview":
        life=w["life"];bits=[]
        for label,key,pk in (("Birth","birth","birth_place"),("Death","death","death_place")):
            if life.get(key) or life.get(pk):
                bits.append(f"<div class='topic'><h3>{label}</h3><div>{esc(life.get(key))}</div><div class='meta'>{esc(life.get(pk))}</div></div>")
        for typ in ("Occupation","Education","Religion"):
            vals=[e["value_text"] for e in w["events"] if e["event_type"]==typ and e["value_text"]]
            if vals:
                bits.append(f"<div class='topic'><h3>{esc(typ)}</h3><div>{esc(vals[0])}</div></div>")
        body="<div class='card'><h2>Person Card</h2>"+("".join(bits) or "<p>No summary facts.</p>")+"</div>"
    elif tab=="timeline":
        body=timeline_tab(db,pid,view)
    elif tab=="biography":
        body="<div class='card'><h2>Biography / Narrative Material</h2>"
        if w["notes"]:
            for n in w["notes"]:
                title=n.get("note_type") or n.get("gedcom_tag") or "Note"
                body+=f"<div class='topic'><h3>{esc(title)}</h3><pre class='note'>{esc(n.get('text') or '')}</pre></div>"
        else:
            body+="<p>No narrative notes.</p>"
        body+="</div>"
    elif tab=="family":
        def block(title,rows):
            return f"<div class='card'><h2>{esc(title)}</h2>"+(
                "".join(f"<a class='result' href='/person/{x['id']}'>{esc(x['display_name'])}</a>" for x in rows)
                or "<p>None recorded.</p>"
            )+"</div>"
        c=w["connections"]
        body="<div class='grid'>"+block("Parents",c["parents"])+block("Spouses",c["spouses"])+block("Children",c["children"])+block("Siblings",c["siblings"])+"</div>"
    elif tab=="sources":
        body="<div class='card'><h2>Sources</h2>"
        if w["sources"]:
            for s in w["sources"]:
                txt=s.get("display_text") or s.get("text") or s.get("title") or "(undescribed source)"
                body+=f"<div class='topic'><strong>{esc(txt)}</strong></div>"
        else:
            body+="<p>No linked sources.</p>"
        body+="</div>"
    elif tab=="media":
        body="<div class='card'><h2>Media</h2>"
        if w["media"]:
            for m in w["media"]:
                body+=f"<div class='topic'><strong>{esc(m.get('title') or Path(m.get('file_path') or '').name)}</strong><div class='small'>{esc(m.get('file_path'))}</div></div>"
        else:
            body+="<p>No media.</p>"
        body+="</div>"
    elif tab=="confidence":
        body="<div class='card'><h2>Evidence Coverage</h2><p>This is evidence coverage, not a truth score.</p>"
        for e in w["confidence"]["events"]:
            badge="<span class='badge good'>Supported</span>" if e["status"]=="supported" else "<span class='badge warn'>No attached evidence</span>"
            body+=f"<div class='topic'><strong>{esc(e['type'])}</strong> {badge}<div class='small'>{esc(e['date'])} {esc(e['place'] or e['value'])}</div></div>"
        body+="</div>"
    elif tab=="research":
        r=person_research_model(db,pid)
        body="<div class='card'><h2>Research</h2>"
        if r["anomalies"]:
            for a in r["anomalies"]:
                cls="warn" if a["severity"]=="warning" else "info"
                body+=f"<div class='topic'><span class='badge {cls}'>{esc(a['kind'])}</span> {esc(a['message'])}</div>"
        else:
            body+="<p>No deterministic review flags.</p>"
        body+="</div>"
    elif tab=="data-quality":
        flags=person_quality(db,pid)
        body="<div class='card'><h2>Data Quality</h2><p class='meta'>Suggested changes are made in Reunion, then the GEDCOM is reloaded.</p>"
        if flags:
            for f in flags:
                body+=f"<div class='topic'><strong>{esc(f['kind'])}</strong><div>{esc(f['detail'])}</div></div>"
        else:
            body+="<p>No current quick-win flags.</p>"
        body+="</div>"
    elif tab=="publish":
        fams=family_choices_for_person(db,pid)
        body=f"""<div class='card'><h2>Person Publishing</h2><div class='stack'>
<form method='post' action='/publish/person/{pid}/profile'><button>Research Profile (HTML)</button></form>
<form method='post' action='/publish/person/{pid}/biography'><button>Biography (HTML)</button></form>
<form method='post' action='/publish/person/{pid}/person'><button>Person Report (HTML)</button></form>
<form method='post' action='/publish/person/{pid}/family'><button>Family Report (HTML)</button></form>
<form method='post' action='/publish/person/{pid}/book'><button>Family-history Book (HTML)</button></form>
<form method='post' action='/publish/person/{pid}/book-pdf'><button>Family-history Book (Print-ready PDF)</button></form>
</div></div><div class='card'><h2>Families</h2>"""
        if fams:
            for f in fams:
                title=" and ".join(x for x in (f["husband"],f["wife"]) if x)
                body+=f"<a class='result' href='/family/{f['id']}'>{esc(title)}</a>"
        else:
            body+="<p>No spouse family recorded.</p>"
        body+="</div>"
    else:
        body="<div class='card'>Unknown person tab.</div>"

    return layout(p["display_name"],f"<h1>{esc(p['display_name'])}</h1><div class='meta'>{esc(p['gedcom_xref'])}</div>{nav}{body}")

def family_page(db,fid,msg=""):
    f=family_workspace(db,fid)
    if not f:
        return layout("Not found","<div class='card'>Family not found.</div>")
    title=" and ".join(x["display_name"] for x in (f["husband"],f["wife"]) if x)
    o=f["overview"]
    message=f"<div class='card'><strong>{esc(msg)}</strong></div>" if msg else ""
    return layout(title,f"""<h1>{esc(title)}</h1>{message}
<div class='grid'><div class='card'><h2>Family Overview</h2>
<p>{esc(f['family'].get('marriage_date'))}<br>{esc(f['family'].get('marriage_place'))}</p>
<p>{o['children_count']} children · {o['known_descendants']} known descendants</p></div>
<div class='card'><h2>Publication Readiness</h2>
<p>{o['wedding_photo_count']} wedding photo(s)</p><p>{o['marriage_document_count']} marriage document(s)</p></div></div>
<div class='card'><h2>Publishing</h2><div class='stack'>
<form method='post' action='/publish/family/{fid}/chapter'><button>Professional Chapter (HTML)</button></form>
<form method='post' action='/publish/family/{fid}/chapter-pdf'><button>Professional Chapter (Print-ready PDF)</button></form>
<form method='post' action='/publish/family/{fid}/descendants'><button>Descendant Chart (HTML)</button></form>
</div><p class='meta'>Nothing is generated by merely opening this page. Publication occurs only after pressing a publish button.</p></div>""")

def research_page(db):
    rows=db.execute("""SELECT p.id,p.display_name,
      SUM(CASE WHEN e.id IS NOT NULL
        AND NOT EXISTS(SELECT 1 FROM event_sources es WHERE es.event_id=e.id)
        AND NOT EXISTS(SELECT 1 FROM event_media em WHERE em.event_id=e.id)
        THEN 1 ELSE 0 END) unsourced
      FROM people p LEFT JOIN events e ON e.person_id=p.id AND e.event_type<>'Changed'
      GROUP BY p.id,p.display_name HAVING unsourced>0
      ORDER BY unsourced DESC,p.display_name LIMIT 100""").fetchall()
    body="<h1>Research Dashboard</h1><div class='card'>"
    for r in rows:
        body+=f"<a class='result' href='/person/{r['id']}?tab=research'><strong>{esc(r['display_name'])}</strong><span class='badge warn' style='float:right'>{r['unsourced']} unsourced</span></a>"
    return layout("Research",body+"</div>")

def places_page(db):
    groups=place_variants(db,1000)
    body="<h1>Place Explorer</h1><div class='card'><p class='meta'>Potential variants only; review before changing Reunion.</p>"
    if not groups:
        body+="<p>No obvious variants detected by the current normalizer.</p>"
    for g in groups:
        body+=f"<div class='topic'><h3>{esc(g['canonical_suggestion'])}</h3>"
        for v in g["variants"]:
            body+=f"<div>{esc(v['place'])} <span class='meta'>({v['count']})</span></div>"
        body+="</div>"
    return layout("Places",body+"</div>")

def sources_page(db):
    body="<h1>Source Explorer</h1><div class='card'><table><tr><th>Source</th><th>Usage</th></tr>"
    for s in source_explorer(db):
        txt=s.get("display_text") or s.get("text") or s.get("title") or "(undescribed source)"
        body+=f"<tr><td>{esc(txt)}</td><td>{s['usage_total']}</td></tr>"
    return layout("Sources",body+"</table></div>")

def media_page(db,category=None):
    cats=media_explorer(db)
    if category:
        items=cats.get(category,[])
        body=f"<h1>Media — {esc(category)}</h1><div class='card'><p>{len(items):,} item(s)</p>"
        for m in items:
            body+=f"""<a class='result' href='/media-item/{m['id']}'>
<strong>{esc(m.get('title') or Path(m.get('file_path') or '').name)}</strong>
<div class='small'>{esc(m.get('file_path'))}</div></a>"""
        return layout("Media",body+"</div>")
    body="<h1>Media Explorer</h1><div class='grid'>"
    for cat,items in sorted(cats.items()):
        body+=f"<a class='card quick' href='/media?category={quote(cat)}'><h2>{esc(cat)}</h2><div class='kpi'>{len(items):,}</div><p class='meta'>View all</p></a>"
    return layout("Media",body+"</div>")

def media_item_page(db,mid):
    m=db.execute("SELECT * FROM media WHERE id=?",(mid,)).fetchone()
    if not m:
        return layout("Media","<div class='card'>Media item not found.</div>")
    people=db.execute("""SELECT DISTINCT p.id,p.display_name
      FROM people p
      LEFT JOIN person_media pm ON pm.person_id=p.id
      LEFT JOIN events e ON e.person_id=p.id
      LEFT JOIN event_media em ON em.event_id=e.id
      WHERE pm.media_id=? OR em.media_id=? ORDER BY p.display_name""",(mid,mid)).fetchall()
    links="".join(f"<a class='result' href='/person/{p['id']}?tab=media'>{esc(p['display_name'])}</a>" for p in people)
    return layout("Media Item",f"""<h1>{esc(m['title'] or Path(m['file_path']).name)}</h1>
<div class='card'><div class='small'>{esc(m['file_path'])}</div>
<p>Status: {'Exists' if m['exists_on_disk'] else 'Missing'}</p></div>
<div class='card'><h2>Linked People</h2>{links or '<p>None found.</p>'}</div>""")

def publishing_page(db,msg=""):
    hist=publication_history(db)
    message=f"<div class='card'><strong>{esc(msg)}</strong></div>" if msg else ""
    history=""
    for x in hist:
        history+=f"""<div class='topic'><strong>{esc(x['kind'])}</strong> — {esc(x.get('subject'))}<br>
<span class='small'>{esc(x['created_at'])} · {esc(x['output_format'])} · {esc(x['output_path'])}</span>
<form method='post' action='/publication/open' style='margin-top:6px'>
<input type='hidden' name='path' value='{esc(x['output_path'])}'><button class='secondary'>Open</button></form></div>"""
    return layout("Publishing",f"""<h1>Publishing Centre</h1>{message}
<div class='card'><p>Generation is always explicit. Use a person's Publish tab or a Family Workspace.</p>
<p>Print-ready PDF uses the print stylesheet/page-break rules and can then be printed from Preview.</p></div>
<div class='card'><h2>Publication History</h2>
{history or '<p>No Beta 3.1 publications yet. Existing report files are not treated as newly published.</p>'}</div>""")

def render_get(db,path,query=None):
    query=query or {}
    if path=="/":
        return home(db,query.get("q",""))
    if path=="/data":
        return data_page(db)
    if path=="/quality":
        return quality_page(db)
    if path=="/quality/items":
        return quality_items_page(db,query.get("kind",""))
    if path=="/research":
        return research_page(db)
    if path=="/places":
        return places_page(db)
    if path=="/sources":
        return sources_page(db)
    if path=="/media":
        return media_page(db,query.get("category"))
    if path.startswith("/media-item/"):
        return media_item_page(db,int(path.rsplit("/",1)[1]))
    if path=="/publishing":
        return publishing_page(db)
    if path.startswith("/person/"):
        return person_page(db,int(path.rsplit("/",1)[1]),query.get("tab","overview"),query.get("view","story"))
    if path.startswith("/event/"):
        return event_page(db,int(path.rsplit("/",1)[1]),query.get("view","research"))
    if path.startswith("/family/"):
        return family_page(db,int(path.rsplit("/",1)[1]))
    return layout("Not found","<div class='card'><h1>Not found</h1></div>")

def _post_form(handler):
    n=int(handler.headers.get("Content-Length","0"))
    raw=handler.rfile.read(n).decode("utf-8")
    return {k:v[0] for k,v in parse_qs(raw).items()}

def run_ui(db_path,host="127.0.0.1",port=8765,open_browser=True):
    db_path=Path(db_path).expanduser()
    class Handler(BaseHTTPRequestHandler):
        def send_html(self,text,status=200):
            data=text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u=urlparse(self.path)
            q={k:v[0] for k,v in parse_qs(u.query).items()}
            db=connect(db_path)
            try:
                try:
                    self.send_html(render_get(db,u.path,q))
                except Exception as e:
                    traceback.print_exc()
                    self.send_html(error_page("Page Error",f"{type(e).__name__}: {e}"),500)
            finally:
                db.close()

        def do_POST(self):
            form=_post_form(self)
            u=urlparse(self.path)

            if u.path in ("/data/reload","/data/import"):
                try:
                    result=reload_current(db_path) if u.path=="/data/reload" else staged_import(db_path,form.get("path",""))
                    db=connect(db_path)
                    try:
                        diff=", ".join(f"{k} {v:+d}" for k,v in result["diff"].items() if v) or "No count changes"
                        self.send_html(data_page(db,f"GEDCOM import complete. {diff}"))
                    finally:
                        db.close()
                except Exception as e:
                    traceback.print_exc()
                    db=connect(db_path)
                    try:
                        self.send_html(data_page(db,f"Import failed safely; current data retained. {type(e).__name__}: {e}"),500)
                    finally:
                        db.close()
                return

            db=connect(db_path)
            try:
                try:
                    m=re.match(r"^/publish/family/(\d+)/(chapter|chapter-pdf|descendants)$",u.path)
                    if m:
                        fid=int(m.group(1))
                        f=family_workspace(db,fid)
                        subject=" and ".join(x["display_name"] for x in (f["husband"],f["wife"]) if x)
                        action=m.group(2)
                        if action=="chapter":
                            p=family_chapter_html(db,fid,subject)
                        elif action=="chapter-pdf":
                            p=family_chapter_pdf(db,fid,subject)
                        else:
                            p=descendant_chart(db,fid,subject)
                        self.send_html(family_page(db,fid,f"Published: {p}"))
                        return

                    m=re.match(r"^/publish/person/(\d+)/(profile|biography|person|family|book|book-pdf)$",u.path)
                    if m:
                        pid=int(m.group(1))
                        row=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
                        p=person_output(db,pid,row["display_name"],m.group(2))
                        self.send_html(publishing_page(db,f"Published: {p}"))
                        return

                    if u.path=="/publication/open":
                        p=open_output(form.get("path",""))
                        self.send_html(publishing_page(db,f"Opened: {p}"))
                        return

                    self.send_html(layout("Not found","<div class='card'>Not found.</div>"),404)
                except Exception as e:
                    traceback.print_exc()
                    self.send_html(error_page("Action Error",f"{type(e).__name__}: {e}"),500)
            finally:
                db.close()

        def log_message(self,*args):
            pass

    server=ThreadingHTTPServer((host,port),Handler)
    url=f"http://{host}:{port}/"
    print("Reunion Companion Beta 3.1 UI")
    print(f"Database: {db_path}")
    print(f"Open: {url}")
    print("Press Ctrl-C to stop.")
    if open_browser:
        threading.Timer(0.5,lambda:webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
