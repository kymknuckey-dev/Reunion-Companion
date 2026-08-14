from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs,quote
from pathlib import Path
import html,re,webbrowser,threading,traceback,mimetypes

from .database import connect
from .beta_ui_service import search_people,person_workspace,family_workspace,family_choices_for_person
from .beta2_research import person_research_model,place_variants,source_explorer,media_explorer
from .timeline_engine import timeline_for_person,event_detail,source_label
from .ffd_home import home_body as ffd_home_body, search_body as ffd_search_body
from .ffd_presentation import presentation_mode_enabled,toggle_presentation_mode
from .ffd_person_story import person_story_body
from .ffd_family_chart import family_chart_body
from .ffd_relationship_questions import questions_body
from .person_navigation import nav_html
from .beta3_data_manager import current_gedcom,import_history,seed_history_from_current,reload_current,staged_import,dataset_counts
from .beta3_quality import quick_wins,quality_items,person_quality
from .family_files import (active_family_file,default_family_file,list_family_files,register_family_file,set_active_family,verify_refresh_for_workspace,record_workspace_import,
    rename_family_file,set_default_family,delete_family_file,family_report_count,preflight_family_refresh,FamilyFileMismatch,deletion_lifecycle)
from .beta3_publishing import (
    publication_history,family_chapter_html,family_chapter_pdf,
    descendant_chart,person_output,open_output,remove_history,delete_publication
)
from .version_identity import APP_DISPLAY_NAME, FFD_DISPLAY

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

/* FFD Build 1.1 — additive presentation layer */
.ffd-hero{
  background:linear-gradient(135deg,#eeece5,#f8f7f3);
  border:1px solid var(--line);border-radius:16px;
  padding:40px 38px;margin-bottom:24px
}
.ffd-hero h1{
  font-family:Georgia,"Times New Roman",serif;
  font-size:42px;font-weight:500;line-height:1.08;margin:5px 0 10px
}
.ffd-eyebrow{
  color:var(--muted);font-size:13px;font-weight:650;
  letter-spacing:.07em;text-transform:uppercase
}
.ffd-credit{font-family:Georgia,"Times New Roman",serif;font-size:20px;margin:9px 0}
.ffd-intro{max-width:760px;font-size:17px;line-height:1.5;color:#464844}
.ffd-search{display:flex;gap:10px;margin-top:22px;max-width:780px}
.ffd-search input{font-size:17px;padding:13px 14px}
.ffd-section{
  font-family:Georgia,"Times New Roman",serif;font-weight:500;
  font-size:24px;margin:27px 0 12px
}
.ffd-explore{min-height:145px}
.ffd-explore p{line-height:1.45}
.ffd-two{display:grid;grid-template-columns:1.35fr 1fr;gap:18px}
.ffd-stat .kpi{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:34px}
.ffd-page-heading{margin:8px 0 22px}
.ffd-page-heading h1{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:36px}
@media(max-width:760px){
  .ffd-hero{padding:28px 22px}.ffd-hero h1{font-size:34px}
  .ffd-search{display:block}.ffd-search input,.ffd-search button{width:100%;margin-bottom:8px}
  .ffd-two{grid-template-columns:1fr}
}

/* FFD Build 1.2 — Presentation Mode */
.presentation body{font-size:19px;line-height:1.55}
.presentation header{padding:17px 24px}
.presentation header strong a{font-size:19px}
.presentation main{max-width:1320px;padding:0 30px 75px;margin-top:30px}
.presentation h1{font-size:38px}
.presentation h2{font-size:23px}
.presentation h3{font-size:18px}
.presentation .card{padding:24px;border-radius:13px}
.presentation .result{padding:14px 0}
.presentation .small{font-size:14px}
.presentation .meta{font-size:15px}
.presentation .ffd-hero{padding:48px 44px}
.presentation .ffd-hero h1{font-size:52px}
.presentation .ffd-credit{font-size:24px}
.presentation .ffd-intro{font-size:20px;max-width:850px}
.presentation .ffd-section{font-size:29px}
.presentation .ffd-search input{font-size:20px;padding:15px}
.presentation button,.presentation .button{font-size:18px;padding:12px 16px}
.presentation .timeline-story{font-size:19px}
.presentation .event-card{padding:22px}
.presentation .technical-nav{display:none}
.presentation-banner{
  max-width:1320px;margin:16px auto 0;padding:0 30px;
  color:var(--muted);font-size:14px;text-align:right
}
.presentation-banner strong{color:var(--text)}

/* FFD 1.3 Person Story */
.ffd-person-hero{background:linear-gradient(135deg,#eeece5,#f8f7f3);border:1px solid var(--line);border-radius:16px;padding:38px;margin-bottom:24px}
.ffd-person-hero h1{font-family:Georgia,"Times New Roman",serif;font-size:44px;font-weight:500;margin:6px 0}.ffd-lifespan{font-family:Georgia,"Times New Roman",serif;font-size:22px;color:var(--muted)}
.ffd-person-intro{font-size:17px;line-height:1.55;max-width:800px}.ffd-story-actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:22px}
.ffd-story-grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,.9fr);gap:22px}.ffd-story-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;text-align:center}
.ffd-story-kpis strong{display:block;font-family:Georgia,"Times New Roman",serif;font-size:34px;font-weight:500}.ffd-story-kpis span{display:block;color:var(--muted);font-size:13px}
.ffd-milestone,.ffd-story-relation,.ffd-deeper a{display:block;padding:14px 0;border-bottom:1px solid var(--line)}.ffd-milestone:last-child,.ffd-story-relation:last-child,.ffd-deeper a:last-child{border-bottom:0}
.ffd-milestone-type{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}.ffd-milestone p{margin:6px 0 0;color:var(--muted)}.ffd-story-relation span,.ffd-story-relation strong{display:block}
.presentation .ffd-person-hero{padding:48px 44px}.presentation .ffd-person-hero h1{font-size:54px}.presentation .ffd-lifespan{font-size:26px}.presentation .ffd-person-intro{font-size:20px}
@media(max-width:850px){.ffd-story-grid{grid-template-columns:1fr}}

.ffd-close-family{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}

/* FFD 1.3.2 — Person Story Visual Alignment */
.ffd-story-tabs{gap:7px}
.ffd-nav-pill{
  display:inline-block;padding:8px 11px;border:1px solid var(--line);
  border-radius:7px;background:#fff;color:var(--text);text-decoration:none
}
.ffd-nav-pill:hover{background:var(--soft);text-decoration:none}
.ffd-story-actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.ffd-action-card{
  display:block;padding:14px 15px;border:1px solid var(--line);
  border-radius:10px;background:#fff;color:var(--text);text-decoration:none
}
.ffd-action-card:hover{background:var(--soft);text-decoration:none}
.ffd-action-card.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.ffd-action-card span{display:block;font-weight:650}
.ffd-action-card small{display:block;margin-top:4px;color:var(--muted);font-size:12px;line-height:1.35}
.ffd-action-card.primary small{color:#eef2ee}
.ffd-milestone{display:block;padding:16px 0;border-bottom:1px solid var(--line)}
.ffd-milestone-title{font-weight:650;margin:2px 0 3px}
.ffd-inline-link{
  display:inline-block;margin-top:7px;color:var(--muted);
  text-decoration:none;font-size:13px;font-weight:600
}
.ffd-inline-link:hover{color:var(--text);text-decoration:none}
.ffd-story-relation{padding:13px 0;border-bottom:1px solid var(--line)}
.ffd-story-relation .meta{display:block;margin-bottom:2px}
.ffd-story-relation strong{display:block;font-size:16px}
.ffd-deeper{padding-top:8px;padding-bottom:8px}
.ffd-secondary-link{
  display:block;padding:13px 2px;border-bottom:1px solid var(--line);
  color:var(--text);text-decoration:none
}
.ffd-secondary-link:last-child{border-bottom:0}
.ffd-secondary-link:hover{text-decoration:none;background:var(--soft)}
.ffd-secondary-link span{display:block;font-weight:650}
.ffd-secondary-link small{display:block;color:var(--muted);margin-top:2px;font-size:12px}
.presentation .ffd-inline-link{font-size:14px}
.presentation .ffd-action-card span{font-size:18px}
.presentation .ffd-action-card small{font-size:14px}
@media(max-width:900px){.ffd-story-actions{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.ffd-story-actions{grid-template-columns:1fr}}

/* FFD 1.3.3 — Timeline Visual Alignment */
.ffd-back-link{display:inline-flex;align-items:center;gap:5px;margin:0 0 16px;padding:7px 10px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--text);text-decoration:none;font-size:13px;font-weight:600}
.ffd-back-link:hover{background:var(--soft);text-decoration:none}
.presentation .ffd-back-link{font-size:14px}

/* FFD 1.3.4 — Person Story Event Style Alignment
   Style-only: make Key Life Events typography follow the existing Timeline
   hierarchy without changing content, event selection, ordering or layout. */
.ffd-milestone-type{
  font-size:18px;
  font-weight:700;
  text-transform:none;
  letter-spacing:0;
  color:var(--text);
  margin-bottom:10px;
}
.ffd-milestone-title{
  font-size:16px;
  font-weight:700;
  line-height:1.4;
  margin:0 0 9px;
}
.ffd-milestone p{
  font-size:16px;
  line-height:1.5;
  color:var(--text);
  margin:7px 0 0;
}
.presentation .ffd-milestone-type{font-size:20px}
.presentation .ffd-milestone-title{font-size:18px}
.presentation .ffd-milestone p{font-size:17px}

/* FFD 1.4 Build 2 — Family Unit Chart Navigation */
.live-chart-heading{text-align:center;max-width:850px;margin:10px auto 24px}.live-chart-heading h1{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:38px;margin:6px 0}.live-chart-heading p{color:var(--muted);line-height:1.5}
.live-chart-direction{text-align:center;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em;margin:14px 0 18px}
.chart-window-nav{display:flex;align-items:center;justify-content:space-between;gap:12px;max-width:1120px;margin:0 auto 20px}.chart-window-status{color:var(--muted);font-size:13px;text-align:center}.chart-window-nav .disabled{opacity:.35;pointer-events:none}
.family-unit-chart{max-width:1120px;margin:0 auto}.unit-generation{margin:0 0 28px}.unit-generation-title{text-align:center;font-family:Georgia,"Times New Roman",serif;font-size:22px;margin:0 0 12px}.unit-family-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.family-unit-card{border:1px solid var(--line);border-radius:12px;background:#fff;padding:14px}.unit-couple{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:8px}
.unit-person{display:block;padding:10px 11px;border:1px solid var(--line);border-radius:9px;background:var(--soft);color:var(--text);text-decoration:none;text-align:center}.unit-person:hover{background:#fff;text-decoration:none}.unit-person strong{display:block;font-family:Georgia,"Times New Roman",serif;font-size:16px;line-height:1.2;margin:3px 0}.unit-role{display:block;color:var(--muted);font-size:11px;font-weight:650}.unit-dates{display:block;color:var(--muted);font-size:12px}
.unit-children-label{text-align:center;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin:11px 0 6px}.unit-children{display:flex;flex-wrap:wrap;gap:7px;justify-content:center}.unit-person.compact{flex:0 1 180px;padding:8px 9px}.unit-person.compact strong{font-size:14px}.unit-person.compact .unit-role{font-size:10px}.unit-person.compact .unit-dates{font-size:11px}
.live-chart-note{max-width:820px;margin:28px auto 0}.presentation .live-chart-heading h1{font-size:46px}.presentation .unit-generation-title{font-size:24px}.presentation .unit-person strong{font-size:18px}.presentation .unit-person.compact strong{font-size:16px}.presentation .unit-dates{font-size:14px}
@media(max-width:700px){.chart-window-nav{display:grid;grid-template-columns:1fr 1fr}.chart-window-status{grid-column:1/-1;grid-row:1}.unit-family-grid{grid-template-columns:1fr}}

/* FFD 1.5 Build 1 — Relationship Questions */
.rq-heading{text-align:center;max-width:820px;margin:10px auto 24px}.rq-heading h1{font-family:Georgia,"Times New Roman",serif;font-weight:500;font-size:42px;margin:6px 0}.rq-heading p{color:var(--muted);line-height:1.5}
.rq-form{max-width:900px;margin:0 auto 22px;display:flex;gap:10px}.rq-input{flex:1;padding:14px 16px;border:1px solid var(--line);border-radius:10px;font:inherit;font-size:16px}.rq-answer{max-width:900px;margin:0 auto 22px;border:1px solid var(--line);border-radius:12px;background:#fff;padding:20px}.rq-answer>p{font-family:Georgia,"Times New Roman",serif;font-size:21px;line-height:1.45;margin:0 0 15px}
.rq-path{display:flex;flex-direction:column;align-items:center;gap:4px;max-width:520px;margin:16px auto}.rq-path-person{display:block;width:100%;padding:10px 14px;border:1px solid var(--line);border-radius:9px;background:var(--soft);text-align:center;color:var(--text);text-decoration:none;font-family:Georgia,"Times New Roman",serif;font-size:17px}.rq-path-edge{color:var(--muted);font-size:12px;text-transform:uppercase}.rq-people{display:flex;flex-wrap:wrap;gap:8px}.rq-person-chip{padding:8px 12px;border:1px solid var(--line);border-radius:999px;background:var(--soft);color:var(--text);text-decoration:none}.rq-help{max-width:900px;margin:0 auto}.rq-example{padding:7px 0;border-bottom:1px solid var(--line);color:var(--muted)}.rq-help p{color:var(--muted)}
.rq-context{margin-top:12px}.rq-context-line{color:var(--muted);line-height:1.5}.rq-followup{color:var(--muted);font-size:12px;line-height:1.4;margin-top:4px}.rq-return-line{margin-top:3px}.rq-return-origin{font-size:13px}.rq-identity-picker{margin-top:8px}.rq-identity-title{font-family:Georgia,"Times New Roman",serif;font-size:28px;margin-bottom:4px}.rq-identity-count{color:var(--muted);margin-bottom:16px}.rq-choice-section-title{font-weight:650;margin:0 0 9px}.rq-choice-section{margin-bottom:14px}.rq-other-matches{margin-top:14px}.rq-other-matches summary{cursor:pointer;color:var(--muted);font-weight:600;margin-bottom:10px}.rq-identity-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.rq-identity-card{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:var(--card);transition:transform .12s ease,border-color .12s ease}.rq-identity-card:hover{transform:translateY(-1px);border-color:var(--accent)}.rq-identity-name{font-family:Georgia,"Times New Roman",serif;font-size:20px}.rq-identity-meta{color:var(--muted);font-size:14px;margin-top:4px;line-height:1.35}.rq-relevance{display:inline-block;margin-top:8px;padding:3px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:11px;font-weight:650}.rq-identity-select{margin-top:10px;font-weight:600;color:var(--accent)}.presentation .rq-heading h1{font-size:48px}.presentation .rq-answer>p{font-size:24px}
@media(max-width:650px){.rq-form{display:block}.rq-input{width:100%;box-sizing:border-box;margin-bottom:9px}.rq-form .btn{width:100%}}

"""

def esc(v):
    return html.escape("" if v is None else str(v))

def family_selector_html():
    try:
        from .database import connect as _connect
        dbp=getattr(family_selector_html,'db_path',None)
        if not dbp:return ''
        db=_connect(dbp)
        try:
            fams=list_family_files(db); active=active_family_file(db)
        finally: db.close()
        opts=''.join(f"<option value='{f['id']}' {'selected' if active and f['id']==active['id'] else ''}>{esc(f['display_name'])}</option>" for f in fams)
        return f"<form method='post' action='/family-file/select' style='margin-left:auto'><select name='workspace_id' onchange='this.form.submit()' aria-label='Family File'>{opts}</select></form>"
    except Exception:return ''

def layout(title,body):
    presentation=presentation_mode_enabled()
    html_class="presentation" if presentation else ""
    mode_label="Exit Presentation" if presentation else "Presentation Mode"
    mode_status="Presentation Mode is ON" if presentation else "Full research interface"

    return f"""<!doctype html><html class='{html_class}'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='reunion-companion-compat' content='Beta 3.1 · Beta 3.2 Timeline Intelligence · FFD 1.1 · Research · Publishing'>
<title>{esc(title)} — Reunion Companion</title><style>{CSS}
.ffd-person-nav a.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.media-row{{display:flex;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line);text-decoration:none;color:var(--text)}}
.media-row span span{{display:block;margin-top:4px}}.media-thumb{{width:84px;height:64px;object-fit:cover;border-radius:7px;border:1px solid var(--line);flex:0 0 auto}}.media-file-icon{{display:flex;align-items:center;justify-content:center;background:var(--soft);font-size:12px;color:var(--muted)}}
.person-heading{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px}}.person-portrait{{width:180px;max-height:220px;object-fit:contain;border-radius:10px;border:1px solid var(--line);background:#fff}}.publication-actions{{display:flex;gap:8px;margin-top:7px}}.inline-form{{display:inline-block}}
</style></head><body>
<header><strong><a href='/' style='margin-right:0'>Reunion Companion</a></strong><nav>
<a href='/'>Home</a><a href='/search'>Search</a><a href='/reports'>Reports</a>
</nav>{family_selector_html()}
<form method='post' action='/presentation/toggle' style='margin-left:auto'>
<button class='secondary'>{mode_label}</button></form>
<span class='meta'>{FFD_DISPLAY}</span></header>
<div class='presentation-banner'><strong>{mode_status}</strong></div>
<main>{body}</main></body></html>"""

def family_mismatch_body(name,score,selected_path):
    selected=str(selected_path or '')
    guessed=Path(selected).stem.replace('_',' ').replace('-',' ').strip() or 'New Family History'
    return f"""<h1>GEDCOM does not match this Family File</h1><div class='card'><h2>This GEDCOM doesn't appear to belong to {esc(name)}.</h2><p>Companion found only a <strong>{float(score):.0%}</strong> match with the existing family data. Nothing has been changed.</p><h3>Add as a New Family File</h3><form method='post' action='/family-file/add'><input name='name' value='{esc(guessed)}' required><input type='hidden' name='path' value='{esc(selected)}'><input name='source_application' placeholder='Source application (e.g. Reunion)' value='Reunion'><button>Add as a New Family File</button></form><p><a href='/data'>Cancel</a></p></div>"""

def error_page(title,error):
    return layout(title,f"""<div class='card error'><h1>{esc(title)}</h1>
<p>Companion could not render this page.</p>
<pre class='note'>{esc(error)}</pre>
<p class='meta'>The local UI remains running. Return to <a href='/'>Search</a>.</p></div>""")

def home(db,q=""):
    # Compatibility: an old-style /?q= search still works.
    if q:
        return layout("Search",ffd_search_body(db,q,search_people,presentation_mode_enabled()))
    return layout("Home",ffd_home_body(db,quick_wins(db),presentation_mode_enabled()))

def search_page(db,q=""):
    return layout("Search",ffd_search_body(db,q,search_people,presentation_mode_enabled()))

def _delete_confirmation(db, workspace_id):
    life=deletion_lifecycle(db,workspace_id)
    target=life['target']; replacement=life['replacement']
    name=target['display_name']; replacement_name=replacement['display_name']
    parts=[f"Delete {name} from Reunion Companion?"]
    if life['was_active']:
        parts.append(f"{name} is currently open. Companion will switch to {replacement_name} before deleting it.")
    if life['was_default']:
        parts.append(f"{name} is the default Family File. {replacement_name} will become the new default.")
    parts.append('The original GEDCOM/family file is not changed.')
    return ' '.join(parts)

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
    ff=active_family_file(db); fams=list_family_files(db)
    family_rows=""
    for x in fams:
        flags=[]
        if x.get('is_default'):flags.append('Default')
        if x.get('is_active'):flags.append('Active')
        badges=(" · ".join(flags))
        reports=family_report_count(db,x['id'])
        actions=f"""<div class='publication-actions'>
<form method='post' action='/family-file/rename' class='inline-form'><input type='hidden' name='workspace_id' value='{x['id']}'><input name='name' value='{esc(x['display_name'])}' required><button class='secondary'>Rename</button></form>
"""
        if not x.get('is_default'):
            actions+=f"<form method='post' action='/family-file/default' class='inline-form'><input type='hidden' name='workspace_id' value='{x['id']}'><button class='secondary'>Make Default</button></form>"
        if len(fams)>1:
            confirm_text=_delete_confirmation(db,x['id']).replace("'","&#39;")
            actions+=f"""<form method='post' action='/family-file/delete' class='inline-form' onsubmit="return confirm('{confirm_text}')"><input type='hidden' name='workspace_id' value='{x['id']}'><label class='small'><input type='checkbox' name='delete_reports' value='1'> Delete {reports} generated report(s) and assets</label><button class='secondary'>Delete Family File</button></form>"""
        family_rows+=f"<div class='topic'><strong>{esc(x['display_name'])}</strong>{(' — '+esc(badges)) if badges else ''} — {esc(x.get('source_application') or 'GEDCOM')}<br><span class='small'>{esc(x.get('gedcom_path') or 'No GEDCOM recorded')} · Reports: {reports}</span>{actions}</div>"
    return layout("Data Manager",f"""<h1>Data Manager</h1>{message}
<div class='card'><h2>Family Files</h2><p class='meta'>The active Family File is <strong>{esc(ff['display_name'] if ff else '')}</strong>. Rename and manage Family Files here. The internal Family File identity does not change when a name is changed.</p>{family_rows}
<h3>Add Family File</h3><form method='post' action='/family-file/add'><input name='name' placeholder='Family File name' required><input name='path' placeholder='/Users/.../Family.ged' required><input name='source_application' placeholder='Source application (e.g. Reunion)'><button>Add Family</button></form></div>
<div class='card'><h2>Current GEDCOM</h2><div class='small'>{current}</div>
<div class='grid' style='margin-top:15px'>{stats}</div>
<form method='post' action='/data/reload' style='margin-top:16px'><button {disabled}>Safe Refresh Current GEDCOM</button></form><p class='small'>Builds and verifies a staged database, backs up the current database, then atomically promotes the refresh.</p></div>
<div class='card'><h2>Safe Refresh from New GEDCOM</h2>
<p class='meta'>Enter the full path to a Reunion GEDCOM export. Companion rebuilds imported data in a staging database, validates it, backs up the working database, and only then replaces it.</p>
<form class='search' method='post' action='/data/import'>
<input name='path' placeholder='/Users/.../Family.ged'><button>Safe Refresh</button></form></div>
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
        body+=f"<p><a class='ffd-inline-link' href='/event/{e['id']}?view={view}'>View event →</a></p></section>"
    return body+"</div>"

def event_page(db,event_id,view="research"):
    d=event_detail(db,event_id)
    if not d:return layout("Event not found","<div class='card'><h1>Event not found</h1></div>")
    e=d["event"];p=d["person"]
    body=f"""<p><a class='ffd-back-link' href='/person/{p['id']}?tab=timeline&view={view}'>← Timeline</a></p>
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

def _displayable_events(events):
    return [e for e in events if (e.get("event_type") or "").casefold() not in ("changed","change") and (e.get("gedcom_tag") or "").upper() != "CHAN"]

def _media_is_image(m):
    return Path(m.get("file_path") or "").suffix.lower() in {".jpg",".jpeg",".png",".gif",".webp",".heic",".tif",".tiff"}

def _person_portrait(w):
    for m in w.get("media",[]):
        if m.get("exists_on_disk") and _media_is_image(m): return m
    return None

def person_page(db,pid,tab="overview",view="story"):
    w=person_workspace(db,pid)
    if not w:
        return layout("Not found","<div class='card'><h1>Person not found</h1></div>")
    p=w["person"];presentation=presentation_mode_enabled()
    try:
        from datetime import datetime
        db.execute("CREATE TABLE IF NOT EXISTS companion_recent_people(person_id INTEGER PRIMARY KEY, viewed_at TEXT NOT NULL)")
        db.execute("INSERT INTO companion_recent_people(person_id,viewed_at) VALUES(?,?) ON CONFLICT(person_id) DO UPDATE SET viewed_at=excluded.viewed_at",(pid,datetime.now().isoformat(timespec="seconds")));db.commit()
    except Exception: pass
    nav=nav_html(pid,presentation,tab if tab != "ask" else "ask")

    if tab=="family-chart":
        return layout("Interactive Family Chart",nav+family_chart_body(db,pid,view))
    if tab=="overview" and presentation:
        return layout(p["display_name"],person_story_body(db,w,True))

    if tab=="overview":
        bits=[]
        for e in _displayable_events(w["events"]):
            typ=e.get("event_type") or e.get("gedcom_tag") or "Fact"
            detail=" · ".join(str(x) for x in (e.get("date_text"),e.get("place_text"),e.get("value_text")) if x)
            if detail: bits.append(f"<div class='topic'><h3>{esc(typ)}</h3><div>{esc(detail)}</div></div>")
        from .person_navigation import action_cards
        body="<div class='ffd-story-actions'>"+action_cards(pid,False)+"</div><div class='card'><h2>Person Overview</h2>"+("".join(bits) or "<p>No summary facts.</p>")+"</div>"
    elif tab=="timeline": body=timeline_tab(db,pid,view)
    elif tab=="biography":
        body="<div class='card'><h2>Biography / Narrative Material</h2>"
        for n in w["notes"]: body+=f"<div class='topic'><h3>{esc(n.get('note_type') or n.get('gedcom_tag') or 'Note')}</h3><pre class='note'>{esc(n.get('text') or '')}</pre></div>"
        if not w["notes"]:body+="<p>No narrative notes.</p>"
        body+="</div>"
    elif tab=="family":
        def block(title,rows):
            return f"<div class='card'><h2>{esc(title)}</h2>"+("".join(f"<a class='result' href='/person/{x['id']}'>{esc(x['display_name'])}</a>" for x in rows) or "<p>None recorded.</p>")+"</div>"
        c=w["connections"];body="<div class='grid'>"+block("Parents",c["parents"])+block("Spouses",c["spouses"])+block("Children",c["children"])+block("Siblings",c["siblings"])+"</div>"
    elif tab=="sources":
        body="<div class='card'><h2>Sources</h2>"+("".join(f"<div class='topic'><strong>{esc(source_label(x))}</strong></div>" for x in w["sources"]) or "<p>No linked sources.</p>")+"</div>"
    elif tab=="media":
        body="<div class='card'><h2>Media</h2>"
        for m in w["media"]:
            thumb=f"<img class='media-thumb' src='/media-file/{m['id']}' alt=''>" if m.get("exists_on_disk") and _media_is_image(m) else "<div class='media-thumb media-file-icon'>File</div>"
            body+=f"<a class='media-row' href='/media-item/{m['id']}'>{thumb}<span><strong>{esc(m.get('title') or Path(m.get('file_path') or '').name)}</strong><span class='small'>{esc(m.get('file_path'))}</span></span></a>"
        if not w["media"]:body+="<p>No media.</p>"
        body+="</div>"
    elif tab=="confidence":
        body="<div class='card'><h2>Evidence Coverage</h2><p>This is evidence coverage, not a truth score.</p>"
        for e in w["confidence"]["events"]:
            badge="<span class='badge good'>Supported</span>" if e["status"]=="supported" else "<span class='badge warn'>No attached evidence</span>"
            body+=f"<div class='topic'><strong>{esc(e['type'])}</strong> {badge}<div class='small'>{esc(e['date'])} {esc(e['place'] or e['value'])}</div></div>"
        body+="</div>"
    elif tab=="research":
        r=person_research_model(db,pid);body="<div class='card'><h2>Research</h2>"
        for a in r["anomalies"]:body+=f"<div class='topic'><span class='badge {'warn' if a['severity']=='warning' else 'info'}'>{esc(a['kind'])}</span> {esc(a['message'])}</div>"
        if not r["anomalies"]:body+="<p>No deterministic review flags.</p>"
        body+="</div>"
    elif tab=="data-quality":
        flags=person_quality(db,pid);body="<div class='card'><h2>Data Quality</h2><p class='meta'>Suggested changes are made in Reunion, then the GEDCOM is reloaded.</p>"
        for f in flags:body+=f"<div class='topic'><strong>{esc(f['kind'])}</strong><div>{esc(f['detail'])}</div></div>"
        if not flags:body+="<p>No current quick-win flags.</p>"
        body+="</div>"
    elif tab=="publish":
        fams=family_choices_for_person(db,pid);body=f"""<div class='card'><h2>Person Publishing</h2><div class='stack'>
<form class='publish-form' method='post' action='/publish/person/{pid}/profile'><button>Research Profile (HTML)</button></form><form class='publish-form' method='post' action='/publish/person/{pid}/biography'><button>Biography (HTML)</button></form><form class='publish-form' method='post' action='/publish/person/{pid}/person'><button>Person Report (HTML)</button></form><form class='publish-form' method='post' action='/publish/person/{pid}/family'><button>Family Report (HTML)</button></form><form class='publish-form' method='post' action='/publish/person/{pid}/book'><button>Family-history Book (HTML)</button></form><form class='publish-form' method='post' action='/publish/person/{pid}/book-pdf'><button>Family-history Book (Print-ready PDF)</button></form><div id='publish-progress' class='card' style='display:none'><strong>Creating family history report…</strong><p class='meta'>Collecting people, processing media and assets, building pages and finalising the report. Large books can take some time.</p></div><script>document.querySelectorAll('.publish-form').forEach(function(f){{f.addEventListener('submit',function(){{document.getElementById('publish-progress').style.display='block';document.querySelectorAll('.publish-form button').forEach(function(b){{b.disabled=true;}});}});}});</script></div></div><div class='card'><h2>Families</h2>"""
        for f in fams:
            title=" and ".join(x for x in (f["husband"],f["wife"]) if x);body+=f"<a class='result' href='/family/{f['id']}'>{esc(title)}</a>"
        if not fams:body+="<p>No spouse family recorded.</p>"
        body+="</div>"
    else: body="<div class='card'>Unknown person tab.</div>"
    person_code="" if presentation else f"<div class='meta'>{esc(p['gedcom_xref'])}</div>"
    portrait=_person_portrait(w) if tab=="overview" else None
    portrait_html=f"<img class='person-portrait' src='/media-file/{portrait['id']}' alt='{esc(p['display_name'])}'>" if portrait else ""
    return layout(p["display_name"],f"<div class='person-heading'><div><h1>{esc(p['display_name'])}</h1>{person_code}</div>{portrait_html}</div>{nav}{body}")

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

def publishing_page(db,msg="", origin_pid=None):
    hist=publication_history(db,10)
    message=f"<div class='card'><strong>{esc(msg)}</strong></div>" if msg else ""
    back=""
    if origin_pid:
        row=db.execute("SELECT display_name FROM people WHERE id=?",(origin_pid,)).fetchone()
        if row: back=f"<p><a class='btn secondary' href='/person/{origin_pid}?tab=publish'>← Back to {esc(row['display_name'])}</a></p>"
    history=""
    for x in hist:
        exists=Path(x['output_path']).expanduser().exists()
        status="" if exists else " <span class='badge warn'>Report unavailable</span>"
        actions=(f"<form method='post' action='/publication/open' class='inline-form'><input type='hidden' name='path' value='{esc(x['output_path'])}'><input type='hidden' name='origin' value='{origin_pid or ''}'><button class='secondary'>Open</button></form><form method='post' action='/publication/delete' class='inline-form'><input type='hidden' name='id' value='{x['id']}'><input type='hidden' name='origin' value='{origin_pid or ''}'><button class='secondary'>Delete</button></form>" if exists else f"<form method='post' action='/publication/remove' class='inline-form'><input type='hidden' name='id' value='{x['id']}'><input type='hidden' name='origin' value='{origin_pid or ''}'><button class='secondary'>Remove from history</button></form>")
        history+=f"<div class='topic'><strong>{esc(x['kind'])}</strong> — {esc(x.get('subject'))}{status}<br><span class='small'>{esc(x['created_at'])} · {esc(x['output_format'])} · {esc(x['output_path'])}</span><div class='publication-actions'>{actions}</div></div>"
    return layout("Reports",f"""<h1>Reports</h1>{message}{back}
<div class='card'><p>Generated family-history reports are collected here. Create new reports from a person's Publish page.</p></div>
<div class='card'><h2>Report History</h2>
{history or '<p>No reports have been generated yet.</p>'}</div>""")

def render_get(db,path,query=None):
    query=query or {}
    if path=="/":
        return home(db,query.get("q",""))
    if path=="/search":
        return search_page(db,query.get("q",""))
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
    if path in ("/publishing","/reports"):
        try: origin=int(query.get("origin","0") or 0) or None
        except Exception: origin=None
        return publishing_page(db,origin_pid=origin)
    if path=="/questions":
        try: subject_id=int(query.get("person","0") or 0) or None
        except Exception: subject_id=None
        try: selected_identity_id=int(query.get("selected","0") or 0) or None
        except Exception: selected_identity_id=None
        try: origin_id=int(query.get("origin","0") or 0) or None
        except Exception: origin_id=None
        return layout("Relationship Questions",(nav_html(subject_id,presentation_mode_enabled(),"ask") if subject_id else "")+questions_body(db,subject_id,query.get("q",""),selected_identity_id,origin_id,query.get("topic") or None))
    if path.startswith("/family-chart/"):
        pid=int(path.rsplit("/",1)[1])
        return layout("Interactive Family Chart",nav_html(pid,presentation_mode_enabled(),"family-chart")+family_chart_body(db,pid,query.get("offset","0")))
    if path.startswith("/person/"):
        tab=query.get("tab","overview")
        state=query.get("offset","0") if tab=="family-chart" else query.get("view","story")
        return person_page(db,int(path.rsplit("/",1)[1]),tab,state)
    if path.startswith("/event/"):
        return event_page(db,int(path.rsplit("/",1)[1]),query.get("view","research"))
    if path.startswith("/family/"):
        return family_page(db,int(path.rsplit("/",1)[1]))
    return layout("Not found","<div class='card'><h1>Not found</h1></div>")

def _post_form(handler):
    n=int(handler.headers.get("Content-Length","0"))
    raw=handler.rfile.read(n).decode("utf-8")
    return {k:v[0] for k,v in parse_qs(raw).items()}

def _activate_default_family_on_startup(db_path):
    """Materialise the saved default Family File when Companion starts.

    Default is the startup preference; active is session state.  If they differ,
    safely materialise the default GEDCOM, then mark that Family File active.
    Merely opening Companion never rewrites Family File fingerprint/provenance.
    """
    probe=connect(db_path)
    try:
        default=default_family_file(probe); active=active_family_file(probe)
        if not default or (active and active['id']==default['id']): return False
        path=default.get('gedcom_path')
        if not path: raise ValueError(f"Default Family File {default['display_name']} has no GEDCOM source.")
        wid=default['id']
    finally:
        probe.close()
    staged_import(db_path,path)
    probe=connect(db_path)
    try:
        set_active_family(probe,wid)
    finally:
        probe.close()
    return True

def run_ui(db_path,host="127.0.0.1",port=8765,open_browser=True):
    db_path=Path(db_path).expanduser()
    _activate_default_family_on_startup(db_path)
    family_selector_html.db_path=db_path
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
            if u.path.startswith("/media-file/"):
                db=connect(db_path)
                try:
                    try: mid=int(u.path.rsplit("/",1)[1])
                    except ValueError: self.send_error(404);return
                    row=db.execute("SELECT file_path FROM media WHERE id=?",(mid,)).fetchone()
                    fp=Path(row["file_path"]).expanduser() if row else None
                    if not fp or not fp.exists() or not fp.is_file(): self.send_error(404);return
                    data=fp.read_bytes();self.send_response(200);self.send_header("Content-Type",mimetypes.guess_type(str(fp))[0] or "application/octet-stream");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data);return
                finally: db.close()
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

            if u.path=="/presentation/toggle":
                toggle_presentation_mode()
                db=connect(db_path)
                try:
                    self.send_html(home(db))
                finally:
                    db.close()
                return

            if u.path=="/family-file/add":
                db=connect(db_path)
                try:
                    wid=register_family_file(db,form.get('name','').strip(),form.get('path',''),form.get('source_application','GEDCOM'))
                    self.send_html(data_page(db,f"Family File registered. Its GEDCOM identity will be checked before any refresh."))
                except Exception as e:self.send_html(data_page(db,f"Add Family File failed: {type(e).__name__}: {e}"),500)
                finally:db.close()
                return
            if u.path=="/family-file/rename":
                db=connect(db_path)
                try:
                    rename_family_file(db,int(form.get('workspace_id','0')),form.get('name',''))
                    self.send_html(data_page(db,"Family File renamed."))
                except Exception as e:self.send_html(data_page(db,f"Rename failed: {e}"),400)
                finally:db.close()
                return
            if u.path=="/family-file/default":
                db=connect(db_path)
                try:
                    set_default_family(db,int(form.get('workspace_id','0')))
                    self.send_html(data_page(db,"Default Family File updated."))
                except Exception as e:self.send_html(data_page(db,f"Default change failed: {e}"),400)
                finally:db.close()
                return
            if u.path=="/family-file/delete":
                wid=int(form.get('workspace_id','0'))
                probe=connect(db_path)
                try:
                    fams=list_family_files(probe); target=next((x for x in fams if x['id']==wid),None)
                    if not target: raise ValueError('Unknown Family File.')
                    if len(fams)<=1: raise ValueError('The only remaining Family File cannot be deleted.')
                    survivor=next((x for x in fams if x['id']!=wid and x.get('is_default')),None) or next(x for x in fams if x['id']!=wid)
                    switch_path=survivor.get('gedcom_path') if target.get('is_active') else None
                    if target.get('is_active') and not switch_path:
                        raise ValueError('A surviving Family File has no GEDCOM source and cannot be activated safely.')
                finally:probe.close()
                try:
                    if switch_path:
                        staged_import(db_path,switch_path)
                    db=connect(db_path)
                    try:
                        delete_family_file(db,wid,form.get('delete_reports','')=='1')
                        self.send_html(data_page(db,"Family File deleted from Reunion Companion. The original GEDCOM/family file was not changed."))
                    finally:db.close()
                except Exception as e:
                    db=connect(db_path)
                    try:self.send_html(data_page(db,f"Delete failed: {e}"),400)
                    finally:db.close()
                return

            if u.path=="/family-file/select":
                db=connect(db_path)
                try:
                    wid=int(form.get('workspace_id','0')); target=[x for x in list_family_files(db) if x['id']==wid][0]
                    path=target.get('gedcom_path')
                    if not path: raise ValueError('This Family File has no GEDCOM source yet.')
                finally:db.close()
                # Selection materialises data but never rewrites Family File identity/provenance.
                staged_import(db_path,path)
                db=connect(db_path)
                try:set_active_family(db,wid); self.send_html(home(db))
                finally:db.close()
                return

            if u.path in ("/data/reload","/data/import"):
                incoming_path=None
                ff=None
                try:
                    probe=connect(db_path)
                    try:
                        preflight=preflight_family_refresh(probe,None if u.path=="/data/reload" else form.get('path',''))
                        ff=preflight['workspace']; incoming_path=preflight['path']
                    finally:probe.close()
                    result=staged_import(db_path,incoming_path)
                    probe=connect(db_path)
                    try:record_workspace_import(probe,ff['id'],incoming_path)
                    finally:probe.close()
                    db=connect(db_path)
                    try:
                        from .safe_refresh import format_change_summary
                        summary=format_change_summary(result.get("changes",{}))
                        backup=result.get("backup_path")
                        msg=f"Safe GEDCOM refresh complete. {summary}." + (f" Backup: {backup}" if backup else "")
                        self.send_html(data_page(db,msg))
                    finally:db.close()
                except Exception as e:
                    db=connect(db_path)
                    try:
                        if isinstance(e,FamilyFileMismatch):
                            body=family_mismatch_body(e.workspace['display_name'],e.match.get('score',0),e.incoming_path)
                            self.send_html(layout('Family File mismatch',body),400)
                        else:
                            traceback.print_exc()
                            self.send_html(data_page(db,f"Safe refresh failed; current data retained. {type(e).__name__}: {e}"),500)
                    finally:db.close()
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
                        self.send_html(publishing_page(db,f"Published: {p}",origin_pid=pid))
                        return

                    if u.path=="/publication/open":
                        p=open_output(form.get("path",""))
                        self.send_html(publishing_page(db,f"Opened: {p}",origin_pid=int(form.get("origin","0") or 0) or None))
                        return
                    if u.path=="/publication/remove":
                        remove_history(db,int(form.get("id","0")));self.send_html(publishing_page(db,"Removed from report history.",origin_pid=int(form.get("origin","0") or 0) or None));return
                    if u.path=="/publication/delete":
                        delete_publication(db,int(form.get("id","0")));self.send_html(publishing_page(db,"Report and associated assets deleted.",origin_pid=int(form.get("origin","0") or 0) or None));return

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
    print(APP_DISPLAY_NAME)
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
