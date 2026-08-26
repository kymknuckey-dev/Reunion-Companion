from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs,quote
from pathlib import Path
import html,re,webbrowser,threading,traceback,mimetypes
import json

from .database import connect
from .beta_ui_service import search_people,person_workspace,family_workspace,family_choices_for_person
from .beta2_research import person_research_model,place_variants,source_explorer,media_explorer
from .timeline_engine import timeline_for_person,event_detail,source_label
from .ffd_home import home_body as ffd_home_body, search_body as ffd_search_body
from .ffd_presentation import presentation_mode_enabled,set_presentation_mode,toggle_presentation_mode
from .ffd_person_story import person_story_body, person_identity_header
from .ffd_family_chart import family_chart_body
from .ffd_relationship_questions import questions_body,answer_question,interpret_question
from .identity_discovery import is_natural_language_question
from .person_navigation import nav_html
from .beta3_data_manager import current_gedcom,import_history,seed_history_from_current,reload_current,staged_import,dataset_counts
from .beta3_quality import quick_wins,quality_items,person_quality
from .family_files import (active_family_file,default_family_file,list_family_files,register_family_file,set_active_family,verify_refresh_for_workspace,record_workspace_import,
    rename_family_file,set_default_family,delete_family_file,family_report_count,preflight_family_refresh,FamilyFileMismatch,deletion_lifecycle)
from .beta3_publishing import (
    publication_history,family_chapter_html,family_chapter_pdf,
    descendant_chart,person_output,scoped_book_output,standalone_descendant_report_output,open_output,remove_history,delete_publication
)
from .version_identity import APP_DISPLAY_NAME, FFD_DISPLAY
from .branding import header_brand_html
from .family_book_scope import build_scope,endpoint_candidates
from .family_publication_model import family_partners, children

CSS="""
:root{--bg:#f4f4f1;--card:#fff;--text:#222;--muted:#6c6c68;--line:#d9d9d4;--good:#246b3a;--warn:#945d00;--accent:#294a67;--brand-navy:#102b4e;--brand-olive:#60743a;--soft:#eef0ed;--danger:#9c2f2f}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--text)}
header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:12px 22px;display:flex;gap:20px;align-items:center}.rc-header-utilities{margin-left:auto;display:flex;align-items:center;gap:12px}.rc-header-utilities form{margin:0!important}.rc-mode-control{display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;background:#f7f7f4}.rc-mode-control form{display:flex}.rc-mode-option{border:0;border-radius:0;padding:8px 12px;background:transparent;color:var(--text);font-weight:650}.rc-mode-option+*{border-left:1px solid var(--line)}.rc-mode-option.active{background:var(--brand-navy);color:#fff}.rc-mode-control form+form{border-left:1px solid var(--line)}
header a{color:var(--text);text-decoration:none;margin-right:13px}
.rc-brand{display:flex;align-items:center;gap:9px;margin-right:0!important;color:var(--brand-navy)!important;font-weight:700;white-space:nowrap}.rc-header-mark{width:46px;height:46px;object-fit:contain;display:block}.rc-brand span{font-size:20px}
main{max-width:1200px;margin:24px auto;padding:0 22px 60px}.rc-app-shell{display:grid;grid-template-columns:190px minmax(0,1fr);max-width:1510px;margin:0 auto}.rc-sidebar{padding:24px 12px 60px 14px;border-right:1px solid var(--line);min-height:calc(100vh - 69px);background:#f7f7f4}.rc-sidebar nav{position:sticky;top:94px;display:flex;flex-direction:column;gap:2px}.rc-sidebar a{position:relative;display:block;padding:8px 11px;border-radius:7px;text-decoration:none;color:#30332f;font-size:14px;line-height:1.3}.rc-sidebar a:hover{background:#e9ece5}.rc-sidebar a.active{background:#e7edf3!important;color:var(--brand-navy)!important;font-weight:700}.rc-sidebar a.active:before{content:"";position:absolute;left:0;top:7px;bottom:7px;width:3px;border-radius:3px;background:var(--brand-navy)}.rc-sidebar .rc-side-section{margin:18px 11px 6px;padding-top:12px;border-top:1px solid var(--line);color:var(--muted);font-size:10.5px;font-weight:750;letter-spacing:.08em;text-transform:uppercase}.rc-sidebar .rc-side-section-first{margin-top:0;padding-top:0;border-top:0}.rc-sidebar .rc-person-section{white-space:normal;line-height:1.3;color:var(--brand-navy);text-transform:none;letter-spacing:0;font-size:12px}.rc-sidebar .rc-person-section .rc-side-person-label{display:block;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px}.rc-sidebar .rc-person-section .rc-side-person-name{display:block;font-weight:750;color:var(--brand-navy)}.rc-content{min-width:0}.rc-app-shell main{margin:24px auto}.rc-person-strip{display:flex;align-items:center;gap:15px;margin:0 0 18px;padding:5px 2px 14px;border-bottom:1px solid var(--line)}.rc-person-strip img{width:58px;height:58px;object-fit:cover;border-radius:10px;border:1px solid var(--line);background:#fff}.rc-person-strip .rc-person-eyebrow{font-size:10px;font-weight:750;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:3px}.rc-person-strip .rc-person-name{font-family:Georgia,"Times New Roman",serif;font-size:25px;font-weight:600;line-height:1.05}.rc-person-strip .rc-person-life{color:var(--muted);margin-top:4px}.rc-person-strip .rc-person-context{font-size:13px;color:var(--muted);margin-top:3px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.search{display:flex;gap:10px}
.stack{display:flex;flex-direction:column;gap:9px}
input,button,select{font:inherit;padding:10px 12px;border:1px solid #bbb;border-radius:7px;background:#fff}
input{flex:1}
button,.button{background:var(--accent);color:#fff;border-color:var(--accent);text-decoration:none;display:inline-block;padding:10px 13px;border-radius:7px;cursor:pointer}
.secondary{background:#fff;color:var(--text)}
.publish-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}
.publish-action{display:grid;grid-template-columns:42px minmax(0,1fr) 18px;align-items:center;column-gap:12px;padding:14px 16px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--text);text-decoration:none;min-height:92px;width:100%}
.publish-action:hover{border-color:#9aa8b4;background:#fafbfd}
.publish-action.primary-action{border-color:var(--accent);background:#f4f7fa}
.publish-action-form.wide{grid-column:1/-1}
.publish-action-icon{width:42px;height:42px;border-radius:8px;background:#eef4f9;color:var(--accent);display:grid;place-items:center}.publish-action-icon svg{width:27px;height:27px;display:block;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;transform-box:fill-box;transform-origin:center}.publish-action-icon.descendant-icon svg{transform:translateY(-1.5px)}.publish-action-chevron{justify-self:end;align-self:center;color:#0b3f98;font-size:26px;line-height:1}
.publish-action-copy strong{display:block;font-size:15px;margin:1px 0 4px}.publish-action-copy span{display:block;color:var(--muted);font-size:13px;line-height:1.35}
.publish-action-form{margin:0}.publish-action-form{height:100%;margin:0;min-width:0}.publish-action-form>button.publish-action{height:100%;text-align:left;cursor:pointer;font:inherit}.publish-action-form>button.publish-action.primary-action{border-color:var(--accent);background:#f4f7fa}
.publish-family-list{display:flex;flex-direction:column;gap:12px;margin-top:14px}
.publish-family-card{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:center;border:1px solid var(--line);border-radius:9px;padding:14px 16px;background:#fff}.publish-family-card>div:first-child{display:grid!important;grid-template-columns:42px minmax(0,1fr);column-gap:12px;align-items:center}
.publish-family-title{font-size:16px;font-weight:700;color:#0b3f98;text-decoration:none}.publish-family-meta{font-size:13px;color:var(--muted);margin-top:4px}
.publish-family-action{white-space:nowrap;display:inline-grid;grid-template-columns:20px auto 14px;align-items:center;column-gap:8px}.publish-family-action svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;transform:translateY(-1px)}
.descendant-scope-note{background:#f3f7fb;border:1px solid #aebfd0;border-radius:9px;padding:13px 15px;margin:12px 0 18px}
.descendant-start-family{padding:12px 0 16px;border-bottom:1px solid var(--line);margin-bottom:16px}
.descendant-start-family strong{display:block;font-size:16px;color:#0b3f98;margin-top:4px}
.descendant-control{max-width:360px}.descendant-control select{width:100%;margin-top:6px}
.descendant-includes{border:1px solid #e1c37a;background:#fff9e9;border-radius:9px;padding:12px 14px;margin:14px 0}
.descendant-report-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.descendant-report-actions button{min-width:180px}
@media(max-width:760px){.publish-actions{grid-template-columns:1fr}.publish-action-form.wide{grid-column:auto}.publish-family-card{grid-template-columns:1fr}.publish-family-action{white-space:normal}}
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
.rc-home-brand{display:flex;align-items:center;gap:24px;margin:0 0 28px}.rc-home-icon{width:150px;height:150px;object-fit:contain;flex:0 0 auto}.rc-home-name{font-family:Georgia,"Times New Roman",serif;font-size:34px;font-weight:600;color:var(--brand-navy);line-height:1.05}.rc-home-tagline{margin-top:9px;color:var(--brand-olive);font-size:18px;font-weight:650}.presentation .rc-home-icon{width:180px;height:180px}.presentation .rc-home-name{font-size:42px}.presentation .rc-home-tagline{font-size:21px}@media(max-width:650px){.rc-home-brand{align-items:flex-start;gap:16px}.rc-home-icon{width:105px;height:105px}.rc-home-name{font-size:27px}.rc-home-tagline{font-size:15px}}
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
@media(max-width:900px){.rc-app-shell{grid-template-columns:1fr}.rc-sidebar{display:none}}
@media(max-width:760px){
  .ffd-hero{padding:28px 22px}.ffd-hero h1{font-size:34px}
  .ffd-search{display:block}.ffd-search input,.ffd-search button{width:100%;margin-bottom:8px}
  .ffd-two{grid-template-columns:1fr}
}

/* FFD Build 1.2 — Presentation Mode */
.presentation body{font-size:19px;line-height:1.55}
.presentation main{max-width:1320px;padding:0 30px 75px;margin-top:30px}.presentation .rc-app-shell{max-width:1630px}.presentation .rc-sidebar{font-size:16px}
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
/* Research Mode Consolidation QA Pass 2: utility header is mode-invariant. */
.rc-utility-header .rc-mode-option{font-size:14px!important;padding:8px 12px!important;line-height:normal!important}
.rc-utility-header select{font-size:14px!important;padding:8px 10px!important;line-height:normal!important;min-width:190px}
.presentation .timeline-story{font-size:19px}
.presentation .event-card{padding:22px}
.presentation .technical-nav{display:none}
.presentation-banner{
  max-width:1320px;margin:16px auto 0;padding:0 30px;
  color:var(--muted);font-size:14px;text-align:right
}
.presentation-banner strong{color:var(--text)}

.ffd-person-editorial{display:grid;grid-template-columns:minmax(0,1fr) 230px;align-items:center;gap:34px;padding:30px 34px}.ffd-person-editorial .ffd-hero-portrait{width:220px;max-height:260px;justify-self:end;object-fit:cover}.ffd-human-kpis{grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:20px;text-align:left}.ffd-human-kpis strong{font-size:24px;line-height:1.15;overflow-wrap:anywhere}.ffd-human-kpis span{display:block;margin-top:6px;color:var(--muted);font-size:13px}.ffd-life-sequence{padding-left:30px}.ffd-life-sequence .ffd-milestone{position:relative;padding-left:18px}.ffd-life-sequence .ffd-milestone:before{content:"";position:absolute;left:-12px;top:7px;width:8px;height:8px;border-radius:50%;background:var(--brand-olive)}.ffd-life-sequence .ffd-milestone:after{content:"";position:absolute;left:-9px;top:18px;bottom:-22px;width:1px;background:var(--line)}.ffd-life-sequence .ffd-milestone:last-child:after{display:none}.ffd-person-link{text-decoration:none;color:var(--text)}.ffd-person-link:hover{text-decoration:underline}.ffd-media-strip{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.ffd-media-preview{width:100%;height:105px;object-fit:cover;border-radius:8px;border:1px solid var(--line)}@media(max-width:760px){.ffd-person-editorial{grid-template-columns:1fr}.ffd-person-editorial .ffd-hero-portrait{justify-self:start;width:170px}.rc-person-strip .rc-person-context{display:none}}
/* RC1.0.7 Person Presentation QA Pass 1 */
.ffd-person-editorial{grid-template-columns:minmax(0,1fr) 260px;padding:34px 38px;min-height:250px}
.ffd-person-editorial .ffd-hero-portrait{width:250px;max-height:300px;border-radius:12px;box-shadow:0 8px 24px rgba(38,46,45,.10)}
.ffd-hero-copy{align-self:center}.ffd-hero-context{margin-top:10px;color:var(--text);font-size:15px;font-weight:600;line-height:1.45}
.ffd-glance{margin:0 0 24px}.ffd-glance .ffd-section{margin-bottom:10px}.ffd-glance .ffd-human-kpis{background:#fff;border:1px solid var(--line);border-radius:13px;padding:20px 22px}
.ffd-glance-item{min-width:0;padding-right:18px;border-right:1px solid var(--line)}.ffd-glance-item:last-child{border-right:0}.ffd-glance-item strong{font-family:Georgia,"Times New Roman",serif;font-weight:500}.ffd-glance-item span{text-transform:uppercase;letter-spacing:.055em;font-size:11px}
.ffd-milestone-detail{margin-top:3px;line-height:1.45}.ffd-story-relation{position:relative;padding-right:28px}.ffd-story-relation .ffd-relation-arrow{position:absolute;right:2px;top:50%;transform:translateY(-50%);color:var(--muted)}
.presentation .ffd-person-editorial{padding:42px 46px}.presentation .ffd-person-editorial .ffd-hero-portrait{width:270px;max-height:330px}.presentation .ffd-hero-context{font-size:17px}
@media(max-width:760px){.ffd-person-editorial{grid-template-columns:1fr}.ffd-person-editorial .ffd-hero-portrait{justify-self:start;width:180px}.ffd-glance-item{border-right:0;border-bottom:1px solid var(--line);padding:10px 0}.ffd-glance-item:last-child{border-bottom:0}}


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
.ffd-story-actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:24px}
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
.search-discovery{margin-top:8px}.search-discovery-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:10px;margin-top:12px}.search-discovery-card{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#fff}.search-discovery-card:hover{border-color:var(--accent)}.search-discovery-reason{font-size:13px;line-height:1.4;color:var(--muted);margin-top:5px}.search-discovery-action{margin-top:10px;color:var(--accent);font-weight:650}.rq-context{margin-top:12px}.rq-focus-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 10px;border:1px solid var(--line);border-radius:9px;background:#fff}.rq-focus-label{color:var(--muted);font-size:12px}.rq-focus-name{color:var(--brand-navy)}.rq-focus-origin{color:var(--muted);font-size:12px}.rq-focus-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-left:auto}.rq-focus-actions a{font-size:12px;font-weight:650;text-decoration:none}.rq-followup{color:var(--muted);font-size:11.5px;line-height:1.35;margin-top:5px}.rq-return-origin{font-size:12px}.rq-legacy-contract{display:none!important}.rq-identity-picker{margin-top:8px}.rq-identity-title{font-family:Georgia,"Times New Roman",serif;font-size:28px;margin-bottom:4px}.rq-identity-count{color:var(--muted);margin-bottom:16px}.rq-choice-section-title{font-weight:650;margin:0 0 9px}.rq-choice-section{margin-bottom:14px}.rq-other-matches{margin-top:14px}.rq-other-matches summary{cursor:pointer;color:var(--muted);font-weight:600;margin-bottom:10px}.rq-identity-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.rq-identity-card{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:var(--card);transition:transform .12s ease,border-color .12s ease}.rq-identity-card:hover{transform:translateY(-1px);border-color:var(--accent)}.rq-identity-name{font-family:Georgia,"Times New Roman",serif;font-size:20px}.rq-identity-meta{color:var(--muted);font-size:14px;margin-top:4px;line-height:1.35}.rq-relevance{display:inline-block;margin-top:8px;padding:3px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:11px;font-weight:650}.rq-identity-select{margin-top:10px;font-weight:600;color:var(--accent)}.presentation .rq-heading h1{font-size:48px}.presentation .rq-answer>p{font-size:24px}
@media(max-width:650px){.rq-form{display:block}.rq-input{width:100%;box-sizing:border-box;margin-bottom:9px}.rq-form .btn{width:100%}}

/* RC1.0.7 Visual Presentation QA Pass 1 */
.rc-header-utilities{margin-left:auto;justify-content:flex-end}.rc-header-utilities form:first-child{margin-left:0!important}.rc-header-utilities select{min-width:190px}
.ffd-person-hero{background:#fbfaf6;border-color:#ddd9cf;box-shadow:0 1px 2px rgba(16,43,78,.04)}
.ffd-person-editorial{display:block!important;padding:28px 32px!important}.ffd-person-editorial .ffd-eyebrow{margin-bottom:18px}.ffd-hero-layout{display:grid;grid-template-columns:210px minmax(0,1fr);gap:28px;align-items:start}.ffd-person-editorial .ffd-hero-portrait{width:210px;height:245px;max-height:none;justify-self:start;object-fit:cover;border-radius:11px}.ffd-hero-copy h1{margin-top:2px!important}.ffd-person-intro{max-width:700px;line-height:1.55}.ffd-hero-context{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:20px;padding-top:16px;border-top:1px solid var(--line)}.ffd-hero-context div{min-width:0}.ffd-hero-context span{display:block;color:var(--muted);font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;margin-bottom:4px}.ffd-hero-context strong{display:block;font-size:14px;line-height:1.35}
.ffd-story-grid{grid-template-columns:minmax(0,1.65fr) minmax(310px,.9fr);gap:20px}.ffd-section{font-family:Georgia,"Times New Roman",serif;font-weight:500}.ffd-life-sequence{padding:8px 20px 8px 22px!important}.ffd-life-sequence .ffd-milestone{display:grid!important;grid-template-columns:76px 40px minmax(0,1fr);gap:10px;position:relative;padding:14px 0!important}.ffd-life-sequence .ffd-milestone:before{left:95px!important;top:0!important;bottom:0!important;width:1px!important;height:auto!important;border-radius:0!important;background:var(--line)!important}.ffd-life-sequence .ffd-milestone:after{display:none!important}.ffd-milestone-date{font-size:13px;font-weight:700;color:var(--brand-navy);padding-top:10px;text-align:right}.ffd-event-icon{position:relative;z-index:1;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#f5f0e4;border:1px solid #e5dfd2;color:var(--brand-navy)}.ffd-event-icon svg{width:21px;height:21px}.ffd-milestone-copy{padding:7px 0 0 2px}.ffd-milestone-title{font-size:16px!important;margin:0 0 3px!important}.ffd-milestone-detail{color:var(--text);font-size:14px;line-height:1.45}.ffd-milestone p{font-size:14px!important;color:var(--muted)!important;line-height:1.45!important;margin-top:4px!important}
.ffd-story-grid aside>.card{padding:10px 18px}.ffd-story-grid aside>.card h3{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:8px 0 4px}.ffd-story-relation{grid-template-columns:48px minmax(0,1fr) 14px!important;gap:10px!important;padding:9px 0!important}.ffd-family-thumb{width:44px!important;height:44px!important}.ffd-relation-copy strong{font-size:14px!important}.ffd-relation-copy .meta{font-size:11px}.ffd-relation-arrow{font-size:0}.ffd-relation-arrow:after{content:"›";font-size:20px;color:var(--muted)}.ffd-close-family{margin-top:14px!important;padding-top:12px;border-top:1px solid var(--line)}
.ffd-media-strip{grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:7px}.ffd-media-preview{height:82px!important}
@media(max-width:900px){.ffd-hero-layout{grid-template-columns:170px minmax(0,1fr)}.ffd-person-editorial .ffd-hero-portrait{width:170px;height:205px}.ffd-story-grid{grid-template-columns:1fr}.ffd-media-strip{grid-template-columns:repeat(4,minmax(0,1fr))!important}}
@media(max-width:620px){.ffd-hero-layout{grid-template-columns:1fr}.ffd-person-editorial .ffd-hero-portrait{width:150px;height:180px}.ffd-hero-context{grid-template-columns:1fr}.ffd-life-sequence .ffd-milestone{grid-template-columns:54px 36px minmax(0,1fr)}.ffd-life-sequence .ffd-milestone:before{left:71px!important}.ffd-event-icon{width:34px;height:34px}.ffd-media-strip{grid-template-columns:repeat(2,1fr)!important}}

/* RC1.0.7 Person Presentation QA Pass 2 */
.ffd-story-relation{display:grid!important;grid-template-columns:54px minmax(0,1fr) 18px;align-items:center;gap:12px;padding:12px 0!important}
.ffd-family-thumb{width:52px;height:52px;object-fit:cover;border-radius:50%;border:1px solid var(--line);background:#f5f1e8}
.ffd-relation-copy{min-width:0}.ffd-relation-copy .meta,.ffd-relation-copy strong,.ffd-relation-life{display:block}
.ffd-relation-life{margin-top:2px;color:var(--muted);font-size:12px}.ffd-story-relation .ffd-relation-arrow{position:static!important;transform:none!important;text-align:right}
.ffd-story-grid{align-items:start}
@media(max-width:760px){.ffd-story-grid{grid-template-columns:1fr}.ffd-family-thumb{width:48px;height:48px}}

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

def _sidebar_person_links(person_context, presentation, active=None):
    # Historical heading contract: heading=name if presentation else f"Research — {name}"
    if not person_context:
        return ""
    pid=int(person_context["id"])
    name=esc(person_context.get("display_name") or "Selected person")
    common=[
        ("overview","Overview",f"/person/{pid}?tab=overview"),
        ("timeline","Timeline",f"/person/{pid}?tab=timeline"),
        ("biography","Biography",f"/person/{pid}?tab=biography"),
        ("family-chart","Family Chart",f"/person/{pid}?tab=family-chart"),
        ("family","Family",f"/person/{pid}?tab=family"),
        ("media","Media",f"/person/{pid}?tab=media"),
    ]
    research=[] if presentation else [
        ("sources","Sources",f"/person/{pid}?tab=sources"),
    ]
    rows=[]
    for key,label,href in common+research:
        cls=" class='active'" if key==active else ""
        rows.append(f"<a{cls} href='{href}'>{esc(label)}</a>")
    ask_cls=" class='active'" if active=="ask" else ""
    rows.append(f"<a{ask_cls} href='/questions?person={pid}&origin={pid}'>Ask about</a>")
    heading=f"<div class='rc-side-section rc-person-section'><span class='rc-side-person-label'>Selected person</span><span class='rc-side-person-name'>{name}</span></div>"
    return heading+"".join(rows)


def _sidebar_global(presentation, active=None):
    if presentation:
        return ""
    rows=["<div class='rc-side-section'>Research</div>"]
    for key,label,href in (
        ("priorities","Priorities","/research"),
        ("improve","Improve","/quality"),
        ("manage","Manage","/data"),
    ):
        cls=" class='active'" if key==active else ""
        rows.append(f"<a{cls} href='{href}'>{label}</a>")
    return "".join(rows)

def _sidebar_output(person_context=None, active=None):
    pid=int(person_context["id"]) if person_context else None
    rows=["<div class='rc-side-section'>Output</div>"]
    if pid:
        pub_cls=" class='active'" if active=="publish" else ""
        rows.append(f"<a{pub_cls} href='/person/{pid}?tab=publish'>Publish</a>")
    reports_cls=" class='active'" if active=="reports" else ""
    if pid:
        rows.append(f"<a{reports_cls} href='/reports?origin={pid}'>Reports</a>")
    else:
        rows.append(f"<a{reports_cls} href='/reports'>Reports</a>")
    return "".join(rows)


def mode_control_html(presentation):
    pcls=" active" if presentation else ""
    rcls="" if presentation else " active"
    return f"""<div class='rc-mode-control' role='group' aria-label='Companion mode'>
<form method='post' action='/presentation/mode' onsubmit=\"event.preventDefault();fetch('/presentation/mode',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'mode=presentation'}}).then(()=>location.reload())\"><button class='rc-mode-option{pcls}' name='mode' value='presentation'>Presentation</button></form>
<form method='post' action='/presentation/mode' onsubmit=\"event.preventDefault();fetch('/presentation/mode',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:'mode=research'}}).then(()=>location.reload())\"><button class='rc-mode-option{rcls}' name='mode' value='research'>Research</button></form>
</div>"""

# Historical shell regression contract: <div class='rc-side-section rc-side-section-first'>Companion</div><a href='/'>Home</a><a href='/search'>Search</a>
def layout(title,body,person_context=None,active=None):
    # Historical no-context navigation contract: >Companion</div><a href='/'>Home</a><a href='/search'>Search</a>
    presentation=presentation_mode_enabled()
    html_class="presentation" if presentation else "research-mode"
    contextual=_sidebar_person_links(person_context,presentation,active)
    global_nav=_sidebar_global(presentation,active)
    output=_sidebar_output(person_context,active)
    home_cls=" class='active'" if active=="home" else ""
    search_cls=" class='active'" if active=="search" else ""

    return f"""<!doctype html><html class='{html_class}'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='reunion-companion-compat' content='Beta 3.1 · Beta 3.2 Timeline Intelligence · FFD 1.1 · Research · Publishing'>
<title>{esc(title)} — Reunion Companion</title><style>{CSS}
.rc-sidebar a.active{{background:var(--brand-navy);color:#fff}}
.media-row{{display:flex;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line);text-decoration:none;color:var(--text)}}
.media-row span span{{display:block;margin-top:4px}}.media-thumb{{width:84px;height:64px;object-fit:cover;border-radius:7px;border:1px solid var(--line);flex:0 0 auto}}.media-file-icon{{display:flex;align-items:center;justify-content:center;background:var(--soft);font-size:12px;color:var(--muted)}}
.person-heading{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:24px}}.person-portrait{{width:180px;max-height:220px;object-fit:contain;border-radius:10px;border:1px solid var(--line);background:#fff}}.publication-actions{{display:flex;gap:8px;margin-top:7px}}.inline-form{{display:inline-block}}

.rc-evidence-event-head{{display:flex;align-items:center;justify-content:space-between;gap:14px}}.rc-evidence-event-head h3{{margin-right:auto}}.rc-evidence-meta{{margin-top:7px}}.rc-evidence-link{{font-weight:650;text-decoration:none}}.rc-evidence-media,.rc-no-evidence{{color:var(--muted)}}
.rc-research-entry-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:850px){{.rc-research-entry-grid{{grid-template-columns:1fr}}}}

/* FFD 2.0 RC1.0.7 Visual Presentation QA Pass 2: explicit hero states and chronology dots */
.ffd-person-editorial .ffd-hero-layout{{grid-template-columns:210px minmax(0,1fr);gap:30px;align-items:start}}
.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-portrait{{width:210px;height:262px;aspect-ratio:4/5;max-height:none;object-fit:cover;object-position:center;border-radius:11px}}
.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-copy{{min-width:0;padding-top:2px}}
.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-copy h1{{overflow-wrap:normal;word-break:normal}}
.ffd-person-editorial.ffd-hero-no-photo .ffd-hero-layout{{display:block}}
.ffd-person-editorial.ffd-hero-no-photo .ffd-hero-copy{{width:100%;max-width:none}}
.ffd-person-editorial.ffd-hero-no-photo .ffd-hero-copy h1{{max-width:100%;overflow-wrap:normal;word-break:normal}}
.ffd-person-editorial.ffd-hero-no-photo .ffd-person-intro{{max-width:900px}}
.ffd-person-editorial.ffd-hero-no-photo .ffd-hero-context{{max-width:900px}}
.ffd-life-sequence .ffd-milestone:before{{content:""!important;position:absolute!important;left:95px!important;top:0!important;bottom:0!important;width:1px!important;height:auto!important;border-radius:0!important;background:var(--line)!important}}
.ffd-life-sequence .ffd-milestone:after{{content:""!important;display:block!important;position:absolute!important;left:91px!important;top:29px!important;width:9px!important;height:9px!important;border-radius:50%!important;background:var(--brand-navy)!important;border:2px solid #fff!important;box-sizing:border-box!important;z-index:2!important}}
.ffd-life-sequence .ffd-event-icon{{z-index:3}}
@media(max-width:900px){{.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-layout{{grid-template-columns:170px minmax(0,1fr)}}.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-portrait{{width:170px;height:212px}}}}
@media(max-width:620px){{.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-layout{{grid-template-columns:1fr}}.ffd-person-editorial.ffd-hero-has-photo .ffd-hero-portrait{{width:150px;height:188px}}.ffd-life-sequence .ffd-milestone:before{{left:71px!important}}.ffd-life-sequence .ffd-milestone:after{{left:67px!important}}}}

/* FFD 2.0 RC1.0.7 Visual Presentation QA Pass 4: one adaptive Life Story timeline */
.ffd-life-sequence .ffd-milestone{{grid-template-columns:66px 20px 40px minmax(0,1fr)!important;gap:8px!important}}
.ffd-life-sequence .ffd-milestone:before,.ffd-life-sequence .ffd-milestone:after{{display:none!important}}
.ffd-chronology{{position:relative;align-self:stretch;min-height:52px}}
.ffd-life-timeline .ffd-chronology:before{{content:"";position:absolute;left:9px;top:-14px;bottom:-14px;width:1px;background:#b8bec4}}
.ffd-life-timeline .ffd-milestone:first-child .ffd-chronology:before{{top:19px}}
.ffd-life-timeline .ffd-milestone:last-child .ffd-chronology:before{{bottom:calc(100% - 20px)}}
.ffd-chronology-dot{{position:absolute;left:5px;top:15px;width:9px;height:9px;border-radius:50%;background:var(--brand-navy);border:2px solid #fff;box-sizing:border-box;z-index:2}}
.ffd-event-icon{{grid-column:3;z-index:1!important}}
.ffd-milestone-copy{{grid-column:4}}
.ffd-milestone-date{{grid-column:1}}
.ffd-milestone-undated .ffd-milestone-date{{color:transparent}}
@media(max-width:620px){{.ffd-life-sequence .ffd-milestone{{grid-template-columns:48px 18px 36px minmax(0,1fr)!important;gap:7px!important}}.ffd-chronology-dot{{left:4px}}.ffd-life-timeline .ffd-chronology:before{{left:8px}}}}

</style></head><body>
<header class='rc-utility-header'>{header_brand_html()}<div class='rc-header-utilities'>{family_selector_html()}{mode_control_html(presentation)}</div></header>
<div class='rc-app-shell'><aside class='rc-sidebar'><nav>
<div class='rc-side-section rc-side-section-first'>Companion</div><a{home_cls} href='/'>Home</a><a{search_cls} href='/search'>Search</a>
{global_nav}{contextual}{output}
</nav></aside><div class='rc-content'><main>{body}</main></div></div></body></html>"""

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
        return search_page(db,q)
    return layout("Home",ffd_home_body(db,quick_wins(db),presentation_mode_enabled()),active="home")

def search_page(db,q="",selected_identity_id=None):
    question_result=None
    if q and is_natural_language_question(q) and interpret_question(q)!="unknown":
        # Legacy pipeline shape: answer_question(db,q,None,selected_identity_id)
        question_result=answer_question(db,q,None,selected_identity_id,global_identity_discovery=True)
    return layout("Search",ffd_search_body(db,q,search_people,presentation_mode_enabled(),question_result),active="search")

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
<div class='card'><h2>Import History</h2>{history or '<p>No Companion import history yet.</p>'}</div>""",active="manage")

def quality_page(db):
    q=quick_wins(db)
    cards=[
        ("Place variants","place_variant_groups","/places"),
        ("Unsourced events / facts","unsourced_events","/quality/items?kind=unsourced-events"),
        ("Missing media","missing_media","/quality/items?kind=missing-media"),
        ("Legacy PICT","legacy_pict","/quality/items?kind=legacy-pict"),
        ("Untitled sources","untitled_sources","/quality/items?kind=untitled-sources"),
        ("Duplicate source titles","duplicate_source_titles","/quality/items?kind=duplicate-sources"),
    ]
    body="<h1>Data Quality Centre</h1><p class='meta'>Review here, change the authoritative record in Reunion, then reload the GEDCOM.</p><div class='grid'>"
    for label,key,url in cards:
        body+=f"<a class='card quick' href='{url}'><h2>{esc(label)}</h2><div class='kpi'>{q[key]:,}</div><p class='meta'>Review items</p></a>"
    return layout("Data Quality",body+"</div>",active="improve")

def quality_items_page(db,kind):
    items=quality_items(db,kind)
    body=f"<h1>{esc(kind.replace('-',' ').title())}</h1><div class='card'><p>{len(items):,} item(s)</p>"
    for x in items:
        if x.get("person_id"):
            body+=f"""<a class='result' href='/person/{x['person_id']}?tab=overview'>
<strong>{esc(x.get('display_name'))}</strong> — {esc(x.get('event_type') or '')} {esc(x.get('date_text') or '')}</a>"""
        else:
            title=x.get("title") or x.get("display_text") or x.get("file_path") or x.get("ids") or "Item"
            body+=f"<div class='topic'><strong>{esc(title)}</strong><div class='small'>{esc(x.get('file_path') or '')}</div></div>"
    return layout("Quality Items",body+"</div>")

def timeline_tab(db,pid,view="story",presentation=False):
    """Mode-specific timeline: Story in Presentation, Research in Research mode."""
    model=timeline_for_person(db,pid)
    if not model:return "<div class='card'>Timeline unavailable.</div>"
    summary=model["summary"]
    if presentation:
        source_order=[]; seen=set()
        for e in model["events"]:
            for src in e.get("sources",[]):
                sid=src.get("id")
                if sid not in seen: seen.add(sid); source_order.append(src)
        source_no={src.get("id"):i+1 for i,src in enumerate(source_order)}
        body="<div class='card'><h2>Life Timeline</h2><p class='meta'>A chronological view of the recorded story.</p></div><div class='timeline'>"
        for e in model["events"]:
            body+=f"<section class='event-card' id='event-{e['id']}'><div class='event-head'><div><h2>{esc(e['type'])}</h2><div><strong>{esc(e['date']) or 'Undated'}</strong></div></div></div>"
            body+=f"<div class='timeline-story'>{esc(e['story'])}</div>"
            meta=[]
            if e["age"]:meta.append(f"Age {e['age']}")
            if e["since_previous"]:meta.append(f"{e['since_previous']} since previous dated event")
            if meta:body+="<div class='meta'>"+" · ".join(esc(x) for x in meta)+"</div>"
            if e["note"]:body+=f"<div class='panel-note'><strong>Note</strong><br>{esc(e['note'])}</div>"
            refs=[source_no.get(x.get('id')) for x in e.get('sources',[]) if source_no.get(x.get('id'))]
            if refs:body+="<div class='small source-refs'>Source " + ", ".join(f"[{n}]" for n in refs) + "</div>"
            body+="</section>"
        body+="</div>"
        if source_order: body+="<div class='card presentation-timeline-sources'><h2>Sources</h2><ol>"+"".join(f"<li>{esc(source_label(src))}</li>" for src in source_order)+"</ol></div>"
        return body
    body=f"""<div class='card'><h2>Research Timeline</h2><p class='meta'>Recorded events with their evidence and research context.</p>
<div class='timeline-meta'><span class='badge info'>{summary['event_count']} events</span><span class='badge info'>{summary['dated_count']} dated</span><span class='badge info'>{summary['supported_count']} with linked evidence</span><span class='badge info'>{summary['observation_count']} review observations</span></div></div><div class='timeline'>"""
    for e in model["events"]:
        evidence="<span class='badge good'>Linked evidence</span>" if e["evidence_status"]=="supported" else "<span class='badge warn'>No linked evidence</span>"
        body+=f"<section class='event-card' id='event-{e['id']}'><div class='event-head'><div><a class='event-link' href='/event/{e['id']}?view=research'><h2>{esc(e['type'])}</h2></a><div><strong>{esc(e['date']) or 'Undated'}</strong></div></div>{evidence}</div>"
        if e["place"]:body+=f"<p><strong>Place</strong><br>{esc(e['place'])}</p>"
        if e["value"]:body+=f"<p><strong>Detail</strong><br>{esc(e['value'])}</p>"
        if e["age"]:body+=f"<p><strong>Age</strong> {esc(e['age'])}</p>"
        if e["note"]:body+=f"<div class='panel-note'><strong>Event note</strong><br>{esc(e['note'])}</div>"
        body+=f"<div class='timeline-meta'><span class='badge info'>{e['source_count']} source(s)</span><span class='badge info'>{e['media_count']} media item(s)</span></div>"
        if e["sources"]:body+="<ul class='evidence-list'>"+"".join(f"<li>{esc(source_label(src))}</li>" for src in e["sources"])+"</ul>"
        for o in e["observations"]:body+=f"<div class='observation'>Review: {esc(o)}</div>"
        body+=f"<p><a class='ffd-inline-link' href='/event/{e['id']}?view=research'>View event →</a></p></section>"
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
    for m in sorted(w.get("media",[]),key=lambda x:(-int(x.get("is_preferred") or 0),int(x.get("id") or 0))):
        if m.get("exists_on_disk") and _media_is_image(m): return m
    return None

def _research_biography_body(w):
    body="<div class='card'><h2>Biography / Original Narrative Material</h2><p class='meta'>Research mode preserves the original Reunion note structure.</p>"
    for n in w["notes"]:
        body+=f"<div class='topic'><h3>{esc(n.get('note_type') or n.get('gedcom_tag') or 'Note')}</h3><pre class='note'>{esc(n.get('text') or '')}</pre></div>"
    if not w["notes"]: body+="<p>No narrative notes.</p>"
    body+="</div>"
    return body

def _presentation_biography_body(pid):
    return f"""<div class='card'><h2>Biography</h2><p><button class='button secondary' type='button' id='regenerate-biography'>Regenerate Biography</button></p><div id='person-biography'><div class='narrative-loading'><span class='rc-bio-spinner' aria-hidden='true'></span><strong>Preparing biography…</strong><p class='meta'>Companion is preparing a grounded narrative from the recorded family history.</p></div></div><style>@keyframes rc-bio-spin{{to{{transform:rotate(360deg)}}}}.rc-bio-spinner{{display:inline-block;width:18px;height:18px;border:3px solid #bbb;border-top-color:#333;border-radius:50%;animation:rc-bio-spin .8s linear infinite;vertical-align:-4px;margin-right:8px}}.biography-prose{{white-space:pre-wrap;font-family:Georgia,"Times New Roman",serif;font-size:19px;line-height:1.65}}</style><script>const bio=document.getElementById('person-biography');function loadBiography(force=false){{if(force)bio.innerHTML='<div class="narrative-loading"><span class="rc-bio-spinner" aria-hidden="true"></span><strong>Regenerating biography…</strong><p class="meta">Companion is rebuilding the grounded narrative from the current recorded family history.</p></div>';fetch('/person-narrative/{pid}'+(force?'?force=1':'')).then(r=>r.text()).then(t=>{{bio.innerHTML=t;}}).catch(()=>{{bio.innerHTML='<p>Biography could not be prepared.</p>';}});}}document.getElementById('regenerate-biography').addEventListener('click',()=>loadBiography(true));loadBiography(false);</script></div>"""

def _research_sources_body(db,w,pid):
    """Render person sources with deterministic attachment/usage context."""
    uses={}
    def add(sid,label):
        if sid is None:return
        uses.setdefault(sid,[])
        if label not in uses[sid]:uses[sid].append(label)
    for r in db.execute("SELECT source_id FROM person_sources WHERE person_id=?",(pid,)):add(r[0],"Person record")
    for r in db.execute("SELECT es.source_id,e.event_type,e.date_text,e.place_text,e.value_text FROM event_sources es JOIN events e ON e.id=es.event_id WHERE e.person_id=? ORDER BY e.id",(pid,)):
        detail=", ".join(str(x) for x in (r[2],r[3],r[4]) if x); add(r[0],f"{r[1] or 'Event'}"+(f" — {detail}" if detail else ""))
    for r in db.execute("SELECT ns.source_id,n.note_type FROM note_sources ns JOIN notes n ON n.id=ns.note_id WHERE n.person_id=? ORDER BY n.id",(pid,)):
        label=(r[1] or "Misc Notes").strip(); add(r[0],"Misc Notes" if label.casefold() in {"note","notes","misc","miscellaneous"} else label)
    for r in db.execute("SELECT fs.source_id,f.marriage_date,f.marriage_place FROM family_sources fs JOIN families f ON f.id=fs.family_id WHERE f.id IN (SELECT family_id FROM family_members WHERE person_id=?) ORDER BY f.id",(pid,)):
        detail=", ".join(str(x) for x in (r[1],r[2]) if x); add(r[0],"Marriage"+(f" — {detail}" if detail else ""))
    body="<div class='card'><h2>Sources</h2><p class='meta'>Sources are shown with the parts of this person's record they support.</p>"
    for src in w.get("sources",[]):
        context=uses.get(src.get("id"),[]) or ["Attachment context not recorded"]
        body+=f"<div class='topic'><strong>{esc(source_label(src))}</strong><div class='small'><strong>Attached to:</strong> {esc(' · '.join(context))}</div></div>"
    if not w.get("sources"):body+="<p>No linked sources.</p>"
    return body+"</div>"

def person_page(db,pid,tab="overview",view="story",presentation_override=None):
    w=person_workspace(db,pid)
    if not w:
        return layout("Not found","<div class='card'><h1>Person not found</h1></div>")
    p=w["person"];presentation=presentation_mode_enabled() if presentation_override is None else bool(presentation_override)
    try:
        from datetime import datetime
        db.execute("CREATE TABLE IF NOT EXISTS companion_recent_people(person_id INTEGER PRIMARY KEY, viewed_at TEXT NOT NULL)")
        db.execute("INSERT INTO companion_recent_people(person_id,viewed_at) VALUES(?,?) ON CONFLICT(person_id) DO UPDATE SET viewed_at=excluded.viewed_at",(pid,datetime.now().isoformat(timespec="seconds")));db.commit()
    except Exception: pass

    if tab=="family-chart":
        return layout("Interactive Family Chart",person_identity_header(db,w,presentation)+family_chart_body(db,pid,view),p,"family-chart")
    if tab=="overview" and presentation:
        return layout(p["display_name"],person_story_body(db,w,True),p,"overview")

    if tab=="overview":
        confidence_by_id={x.get("id"):x for x in (w.get("confidence") or {}).get("events",[])}
        bits=[]
        for e in _displayable_events(w["events"]):
            typ=e.get("event_type") or e.get("gedcom_tag") or "Fact"
            detail=" · ".join(str(x) for x in (e.get("date_text"),e.get("place_text"),e.get("value_text")) if x)
            ev=confidence_by_id.get(e.get("id"),{})
            source_refs=[r[0] for r in db.execute("SELECT source_id FROM event_sources WHERE event_id=? ORDER BY source_id",(e.get("id"),)).fetchall()]
            media_count=int(ev.get("media_count") or 0)
            supported=ev.get("status")=="supported"
            evidence=(" · ".join(f"<a class='rc-evidence-link' href='/person/{pid}?tab=sources'>Source {int(sid)}</a>" for sid in source_refs) if source_refs else "<span class='rc-no-evidence'>No sources</span>")
            if media_count: evidence+=f"<span class='rc-evidence-media'> · Media {media_count}</span>"
            confidence=("<span class='badge good'>Supported</span>" if supported else "<span class='badge warn'>Needs evidence</span>")
            bits.append(f"<div class='topic rc-evidence-event'><div class='rc-evidence-event-head'><h3>{esc(typ)}</h3>{confidence}</div>"+(f"<div>{esc(detail)}</div>" if detail else "")+f"<div class='small rc-evidence-meta'>{evidence}</div></div>")
        body="<div class='card rc-research-overview'><h2>Person Overview</h2><p class='meta'>Recorded events and facts with the evidence currently visible in the imported Reunion data.</p>"+("".join(bits) or "<p>No recorded events or facts.</p>")+"</div>"
    elif tab=="timeline": body=timeline_tab(db,pid,view,presentation)
    elif tab=="biography":
        body=_presentation_biography_body(pid) if presentation else _research_biography_body(w)
    elif tab=="family":
        def block(title,rows):
            return f"<div class='card'><h2>{esc(title)}</h2>"+("".join(f"<a class='result' href='/person/{x['id']}'>{esc(x['display_name'])}</a>" for x in rows) or "<p>None recorded.</p>")+"</div>"
        c=w["connections"];body="<div class='grid'>"+block("Parents",c["parents"])+block("Spouses",c["spouses"])+block("Children",c["children"])+block("Siblings",c["siblings"])+"</div>"
    elif tab=="sources":
        body="<div class='card'><h2>Sources</h2><p>Sources are shown with the relevant story events in Presentation mode.</p></div>" if presentation else _research_sources_body(db,w,pid)
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
        from .external_evidence import external_evidence_for_person
        from .external_evidence_matcher import death_research_state
        r=person_research_model(db,pid);body="<div class='card'><h2>Research</h2>"
        for a in r["anomalies"]:body+=f"<div class='topic'><span class='badge {'warn' if a['severity']=='warning' else 'info'}'>{esc(a['kind'])}</span> {esc(a['message'])}</div>"
        if not r["anomalies"]:body+="<p>No deterministic review flags.</p>"
        body+="</div>"
        death_state=death_research_state(db,pid)
        xref=w["person"].get("gedcom_xref")
        findings=external_evidence_for_person(db,xref) if xref else []
        if death_state["state"]!="recorded" or findings:
            body+="<div class='card'><h2>External Evidence</h2><p class='meta'>Research findings held by Companion only. Confirmed changes are entered manually in Reunion.</p>"
            if death_state["state"]=="missing":
                body+="<div class='topic'><strong>Missing death information</strong><div class='small'>No Death event is recorded in the current Reunion snapshot.</div></div>"
            elif death_state["state"]=="incomplete":
                body+="<div class='topic'><strong>Incomplete death information</strong><div class='small'>A Death event exists, but the structured record still needs research.</div>"
                for reason in death_state["reasons"]:
                    body+=f"<div class='small'>Review: {esc(reason)}</div>"
                if death_state["note_text"]:
                    body+=f"<div class='small'><strong>Existing event note:</strong> {esc(death_state['note_text'])}</div>"
                body+="</div>"
            else:
                body+="<div class='topic'><span class='badge good'>Resolved in Reunion</span> Structured death information and linked evidence are present in the current Reunion snapshot.</div>"
            if findings:
                for f in findings:
                    status=f["review_status"] or "new"
                    badge_class="good" if status=="accepted" else "warn" if status in ("new","reviewed") else "info"
                    score=f["match_confidence"]
                    confidence=f" · Match {score}%" if score is not None else ""
                    heading=f["source_record_name"] or f["event_type"] or f["evidence_type"]
                    meta=[]
                    if f["event_type"] or f["event_date"]: meta.append(" ".join(x for x in (f["event_type"],f["event_date"]) if x))
                    if f["publication"]: meta.append(f["publication"])
                    if f["publication_date"]: meta.append("published "+f["publication_date"])
                    body+=f"<div class='topic'><strong>{esc(heading)}</strong> <span class='badge {badge_class}'>{esc(status.replace('_',' ').title())}</span><div class='small'>{esc(f['source_name'])}{esc(confidence)}</div>"
                    if meta: body+=f"<div>{esc(' · '.join(meta))}</div>"
                    if f["details"]: body+=f"<div>{esc(f['details'])}</div>"
                    if f["match_reason"]: body+=f"<div class='small'>Match basis: {esc(f['match_reason'])}</div>"
                    body+="</div>"
            else:
                body+="<p>No external evidence findings recorded yet.</p>"
            body+="</div>"
        if death_state["state"] in ("missing","incomplete"):
            from .ryerson_browser_assist import build_browser_search_plan,RYERSON_SEARCH_URL
            profile={"surname":w["person"].get("surname"),"given_names":w["person"].get("given_names"),"display_name":w["person"].get("display_name")}
            plan=build_browser_search_plan(profile)
            body+="<div class='card'><h2>Search Ryerson</h2><p class='meta'>Use Ryerson in your normal browser, then paste the matching result row back into Companion. Companion will assess and store the finding; Reunion is not changed.</p>"
            if plan.searches:
                body+="<div class='topic'><strong>Suggested searches</strong>"
                for q in plan.searches:
                    body+=f"<div class='small'>Surname: {esc(q['surname'])} · Given names: {esc(q['given_names'] or '(blank)')} · State: {esc(q['state'])}</div>"
                body+="</div>"
                body+=f"<p><a class='ffd-inline-link' href='{RYERSON_SEARCH_URL}' target='_blank' rel='noopener'>Search Ryerson →</a></p>"
                body+=f"<form method='post' action='/research/ryerson/import/{pid}'><label for='ryerson-result'><strong>Paste Ryerson result</strong></label><p class='meta'>Copy the result row from Ryerson and paste it here. Tab-separated text or copied table HTML is accepted.</p><textarea id='ryerson-result' name='content' rows='7' style='width:100%' placeholder='Paste Ryerson result here'></textarea><div style='margin-top:12px'><button type='submit'>Import and assess finding</button></div></form>"
            else:
                body+="<p>No safe Ryerson search can be generated for this person because a usable surname is not recorded.</p>"
            body+="</div>"
    elif tab=="data-quality":
        flags=person_quality(db,pid);body="<div class='card'><h2>Data Quality</h2><p class='meta'>Suggested changes are made in Reunion, then the GEDCOM is reloaded.</p>"
        for f in flags:body+=f"<div class='topic'><strong>{esc(f['kind'])}</strong><div>{esc(f['detail'])}</div></div>"
        if not flags:body+="<p>No current quick-win flags.</p>"
        body+="</div>"
    elif tab=="publish":
        icon_profile="""<svg viewBox='0 0 32 32' aria-hidden='true'><path d='M7 4h13l5 5v19H7z'/><path d='M20 4v6h6'/><path d='M11 15h10M11 20h10M11 25h7'/></svg>"""
        icon_bio="""<svg viewBox='0 0 32 32' aria-hidden='true'><path d='M4 6c5-2 9-1 12 2v20c-3-3-7-4-12-2z'/><path d='M28 6c-5-2-9-1-12 2v20c3-3 7-4 12-2z'/></svg>"""
        icon_person="""<svg viewBox='0 0 32 32' aria-hidden='true'><circle cx='10' cy='10' r='4'/><path d='M3 25c1-6 4-9 7-9s6 3 7 9'/><path d='M20 8h9M20 14h9M20 20h9'/></svg>"""
        icon_desc="""<svg viewBox='0 0 32 32' aria-hidden='true'><rect x='13' y='3' width='6' height='6' rx='1'/><rect x='3' y='23' width='6' height='6' rx='1'/><rect x='13' y='23' width='6' height='6' rx='1'/><rect x='23' y='23' width='6' height='6' rx='1'/><path d='M16 9v7M6 23v-5h20v5M16 16v7'/></svg>"""
        icon_book="""<svg viewBox='0 0 32 32' aria-hidden='true'><path d='M7 4h18v24H7z'/><path d='M10 4v24'/><path d='M14 9h7M14 14h7'/></svg>"""
        icon_family="""<svg viewBox='0 0 32 32' aria-hidden='true'><circle cx='11' cy='10' r='4'/><circle cx='22' cy='11' r='3.5'/><path d='M3 27c1-7 4-10 8-10s7 3 8 10M17 27c1-5 3-8 6-8 3 0 5 2 6 8'/></svg>"""
        fams=family_choices_for_person(db,pid)
        body=f"""<div class='card'><h2>Person Publishing</h2><p class='meta'>Create and export reports about this person and their descendants.</p>
<div class='publish-actions'>
<form class='publish-form publish-action-form' method='post' action='/publish/person/{pid}/profile'><button class='publish-action' type='submit'><span class='publish-action-icon'>{icon_profile}</span><span class='publish-action-copy'><strong>Research Profile (HTML)</strong><span>Key facts, summary and sources.</span></span><span class='publish-action-chevron'>›</span></button></form>
<form class='publish-form publish-action-form' method='post' action='/publish/person/{pid}/biography'><button class='publish-action' type='submit'><span class='publish-action-icon'>{icon_bio}</span><span class='publish-action-copy'><strong>Biography (HTML)</strong><span>Life story with events and context.</span></span><span class='publish-action-chevron'>›</span></button></form>
<form class='publish-form publish-action-form' method='post' action='/publish/person/{pid}/person'><button class='publish-action' type='submit'><span class='publish-action-icon'>{icon_person}</span><span class='publish-action-copy'><strong>Person Report (HTML)</strong><span>Detailed life report with evidence.</span></span><span class='publish-action-chevron'>›</span></button></form>
<form class='publish-action-form' method='get' action='/descendant-report/{pid}'><button class='publish-action primary-action' type='submit'><span class='publish-action-icon descendant-icon'>{icon_desc}</span><span class='publish-action-copy'><strong>Descendant Report…</strong><span>Indented descendant report (1–6 generations).</span></span><span class='publish-action-chevron'>›</span></button></form>
<form class='publish-action-form wide' method='get' action='/book-scope/{pid}'><button class='publish-action' type='submit'><span class='publish-action-icon'>{icon_book}</span><span class='publish-action-copy'><strong>Configure Family-history Book…</strong><span>Build a family history book with photos, stories and family context.</span></span><span class='publish-action-chevron'>›</span></button></form>
</div>
<div id='publish-progress' class='card publishing-activity' style='display:none'><style>@keyframes rc-spin{{to{{transform:rotate(360deg)}}}}@keyframes rc-pulse{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}.publishing-activity .rc-spinner{{display:inline-block;width:18px;height:18px;border:3px solid #bbb;border-top-color:#333;border-radius:50%;animation:rc-spin .8s linear infinite;vertical-align:-4px;margin-right:8px}}.publishing-activity .rc-working{{animation:rc-pulse 1.4s ease-in-out infinite}}.publishing-activity ul{{margin:.5em 0 0 1.4em}}</style><strong><span class='rc-spinner' aria-hidden='true'></span><span class='rc-working'>Creating report…</span></strong><ul class='meta'><li>Preparing family information</li><li>Writing publication narrative</li><li>Rendering the document and media</li></ul></div>
<script>document.querySelectorAll('.publish-form').forEach(function(f){{f.addEventListener('submit',function(){{document.getElementById('publish-progress').style.display='block';document.querySelectorAll('.publish-form button').forEach(function(b){{b.disabled=true;}});}});}});</script>
</div>
""" 
    else: body="<div class='card'>Unknown person tab.</div>"
    return layout(p["display_name"],person_identity_header(db,w,presentation)+body,p,tab)

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
<a class='button secondary' href='/descendant-report/{f["husband"]["id"] if f["husband"] else f["wife"]["id"]}?family={fid}'>Configure Descendant Report…</a>
</div><p class='meta'>Nothing is generated by merely opening this page. Publication occurs only after pressing a publish button.</p></div>""")


def descendant_report_page(db,start_pid,query=None,msg=""):
    query=query or {}
    start=db.execute("SELECT id,display_name FROM people WHERE id=?",(start_pid,)).fetchone()
    if not start:
        return layout("Descendant Report","<div class='card'>Starting person not found.</div>")
    fams=family_choices_for_person(db,start_pid)
    if not fams:
        return layout("Descendant Report","<h1>Descendant Report</h1><div class='card'><p>No spouse family is recorded for this person.</p></div>",dict(start),"publish")

    requested_family=None
    try: requested_family=int(query.get("family","0") or 0) or None
    except Exception: requested_family=None
    valid={f["id"] for f in fams}
    if requested_family not in valid:
        requested_family=None

    # A family-specific launch has already made the starting-family decision.
    # A person with one spouse family is also unambiguous. Only a genuinely
    # multi-family generic launch asks the user to choose.
    if requested_family is None and len(fams)>1:
        cards=[]
        for f in fams:
            title=" and ".join(x for x in (f["husband"],f["wife"]) if x) or f"Family {f['id']}"
            married=(" · Married "+f["marriage_date"]) if f.get("marriage_date") else ""
            cards.append(f"<div class='publish-family-card'><div><strong>{esc(title)}</strong><div class='publish-family-meta'>{esc(married.lstrip(' ·'))}</div></div><a class='button secondary' href='/descendant-report/{start_pid}?family={f['id']}'>Use this family</a></div>")
        body="<h1>Descendant Report</h1><div class='card'><h2>Choose starting family</h2><p class='meta'>This person has more than one recorded spouse family. Choose which family the descendant report should start from.</p><div class='publish-family-list'>"+"".join(cards)+"</div></div>"
        return layout("Descendant Report",body,dict(start),"publish")

    selected_family=requested_family or fams[0]["id"]
    selected=next(f for f in fams if f["id"]==selected_family)
    family_title=" and ".join(x for x in (selected["husband"],selected["wife"]) if x) or f"Family {selected_family}"
    married=selected.get("marriage_date") or ""

    try:generations=int(query.get("generations","3") or 3)
    except Exception:generations=3
    generations=max(1,min(6,generations))
    labels={1:"Starting couple only",2:"Starting couple and their children",3:"Starting couple, their children and grandchildren",4:"Through great-grandchildren",5:"Through 2× great-grandchildren",6:"Through 3× great-grandchildren"}
    genopts="".join(f"<option value='{n}'{' selected' if n==generations else ''}>{n} generation{'s' if n!=1 else ''}</option>" for n in range(1,7))
    message=f"<div class='card'><strong>{esc(msg)}</strong></div>" if msg else ""

    body=f"""<h1>Descendant Report</h1>{message}
<div class='card'>
<h2>Report scope</h2>
<div class='descendant-scope-note'><strong>Generation 1 is the selected starting couple.</strong><div class='meta'>Their children are Generation 2, grandchildren Generation 3, and so on.</div></div>
<form class='descendant-report-form' method='post' action='/publish/person/{start_pid}/descendant-report'>
<input type='hidden' name='family_id' value='{selected_family}'>
<div class='descendant-start-family'><span class='meta'>Starting family</span><strong>{esc(family_title)}</strong>{("<div class='meta'>Married "+esc(married)+"</div>") if married else ""}</div>
<div class='descendant-control'><label><strong>Generations</strong><span class='meta' style='display:block;margin-top:4px'>Select how many generations to include (1–6).</span><select id='descendant-generations' name='generations'>{genopts}</select></label></div>
<div id='descendant-includes' class='descendant-includes'><strong>This will include:</strong><div id='descendant-includes-text'>{esc(labels[generations])}.</div></div>
<div class='descendant-report-actions'><button name='format' value='PDF'>Create Print-ready PDF</button><button class='secondary' name='format' value='HTML'>Create HTML</button></div>
</form>
<div id='descendant-report-progress' class='publishing-activity' style='display:none;margin-top:16px'><strong><span class='rc-spinner' aria-hidden='true'></span>Creating descendant report…</strong><p class='meta'>Companion is assembling the selected family and descendant generations.</p></div>
<script>
(function(){{
var labels={{1:'Starting couple only.',2:'Starting couple and their children.',3:'Starting couple, their children and grandchildren.',4:'Through great-grandchildren.',5:'Through 2× great-grandchildren.',6:'Through 3× great-grandchildren.'}};
var g=document.getElementById('descendant-generations'),o=document.getElementById('descendant-includes-text');
if(g&&o)g.addEventListener('change',function(){{o.textContent=labels[g.value]||'';}});
document.querySelectorAll('.descendant-report-form').forEach(function(f){{f.addEventListener('submit',function(e){{var s=e.submitter;if(s&&s.name&&s.value){{var h=document.createElement('input');h.type='hidden';h.name=s.name;h.value=s.value;f.appendChild(h);}}document.getElementById('descendant-report-progress').style.display='block';f.querySelectorAll('button').forEach(function(b){{b.disabled=true;}});}});}});
}})();
</script>
</div>"""
    return layout("Descendant Report",body,dict(start),"publish")


def book_scope_page(db,start_pid,query=None,msg=""):
    query=query or {}
    start=db.execute("SELECT * FROM people WHERE id=?",(start_pid,)).fetchone()
    if not start:return layout("Not found","<div class='card'>Starting person not found.</div>")
    endpoints=endpoint_candidates(db,start_pid)
    try:end_pid=int(query.get('endpoint','0') or 0) or None
    except Exception:end_pid=None
    options=[]
    for p,depth in endpoints:
        selected=' selected' if end_pid==p['id'] else ''
        indent='— '*depth
        options.append(f"<option value='{p['id']}'{selected}>{esc(indent+p['display_name'])}</option>")
    message=f"<div class='card'><strong>{esc(msg)}</strong></div>" if msg else ''
    body=f"<h1>Family-history Book Scope</h1>{message}<div class='card'><h2>1. Choose the paternal-line endpoint</h2><p class='meta'>The starting person is {esc(start['display_name'])}. Companion uses recorded father relationships to build the default book path.</p><form method='get' action='/book-scope/{start_pid}'><select name='endpoint' required><option value=''>Choose endpoint…</option>{''.join(options)}</select> <button type='submit'>Build default path</button></form></div>"
    if end_pid:
        try:scope=build_scope(db,start_pid,end_pid,4,None)
        except ValueError as e:
            return layout("Family-history Book Scope",body+f"<div class='card error'>{esc(str(e))}</div>",dict(start),"publish")
        selected=set(scope['primary_family_ids'])
        rows=[]
        for entry in scope['entries']:
            h,w=family_partners(db,entry.family_id)
            title=' and '.join(x['display_name'] for x in (h,w) if x) or f"Family {entry.family_id}"
            checked=' checked' if entry.family_id in selected else ''
            badge=" <span class='badge good'>Paternal path</span>" if entry.on_primary_path else " <span class='badge info'>Chart only</span>"
            child_context=''
            if not entry.on_primary_path:
                child_rows=children(db,entry.family_id)
                if child_rows:
                    child_context="<span class='meta' style='display:block;margin-left:24px'>Children shown in chart: "+esc(', '.join(ch['display_name'] for ch in child_rows))+"</span>"
            rows.append(f"<label class='result' style='padding-left:{entry.depth*18}px'><input type='checkbox' name='family_{entry.family_id}' value='1'{checked}> <strong>{esc(title)}</strong>{badge}{child_context}</label>")
        endpoint=db.execute("SELECT display_name FROM people WHERE id=?",(end_pid,)).fetchone()
        body+=f"<div class='card'><h2>2. Choose families to expand</h2><p class='meta'>The paternal path to {esc(endpoint['display_name'] if endpoint else str(end_pid))} is selected automatically. Other families stay visible in family context but do not become chapters unless you tick them. In the book charts, children of paternal siblings are shown for context, then those side branches stop.</p><form class='scope-publish-form' method='post' action='/publish/person/{start_pid}/scoped-book'><input type='hidden' name='endpoint' value='{end_pid}'>{''.join(rows)}<div style='margin-top:16px'><button name='format' value='PDF'>Create Print-ready PDF</button> <button class='secondary' name='format' value='HTML'>Create HTML</button></div></form><div id='scope-publish-progress' class='publishing-activity' style='display:none;margin-top:16px'><style>@keyframes rc-scope-spin{{to{{transform:rotate(360deg)}}}}.publishing-activity .rc-spinner{{display:inline-block;width:18px;height:18px;border:3px solid #bbb;border-top-color:#333;border-radius:50%;animation:rc-scope-spin .8s linear infinite;vertical-align:-4px;margin-right:8px}}</style><strong><span class='rc-spinner' aria-hidden='true'></span>Creating family history report…</strong><p class='meta'>Companion is assembling the selected families, narrative, charts and media. This can take a little while.</p></div><script>document.querySelectorAll('.scope-publish-form').forEach(function(f){{f.addEventListener('submit',function(e){{var s=e.submitter;if(s&&s.name&&s.value){{var h=document.createElement('input');h.type='hidden';h.name=s.name;h.value=s.value;h.className='submitted-format';f.appendChild(h);}}document.getElementById('scope-publish-progress').style.display='block';f.querySelectorAll('button').forEach(function(b){{b.disabled=true;}});}});}});</script></div>"
        body+="<div class='card'><h2>Spouse context rule</h2><p class='meta'>For families on the primary path, the incoming spouse receives a chart-only family context. Direct ancestors may be shown; siblings may show partner/marriage and children; those branches stop at the children and never become chapters automatically.</p></div>"
    return layout("Family-history Book Scope",body,dict(start),"publish")


def research_page(db):
    from .external_evidence_matcher import ryerson_death_candidates
    from .external_evidence import external_evidence_for_person
    from .external_research_runner import runner_status
    from .ryerson_targeted_bootstrap import targeted_status
    from .ryerson_discovery_ui import render_discovery_review_section
    from .ryerson_discovery_materialize import materialize_existing_ryerson_discoveries
    from .ryerson_person_finding_bridge import materialize_person_level_ryerson_findings

    death_rows=ryerson_death_candidates(db)
    run=runner_status(db)
    surname_run=targeted_status(db)
    sql=("SELECT p.id,p.display_name, "
         "SUM(CASE WHEN e.id IS NOT NULL "
         "AND NOT EXISTS(SELECT 1 FROM event_sources es WHERE es.event_id=e.id) "
         "AND NOT EXISTS(SELECT 1 FROM event_media em WHERE em.event_id=e.id) "
         "THEN 1 ELSE 0 END) unsourced "
         "FROM people p LEFT JOIN events e ON e.person_id=p.id AND e.event_type<>'Changed' "
         "GROUP BY p.id,p.display_name HAVING unsourced>0 "
         "ORDER BY unsourced DESC,p.display_name LIMIT 100")
    rows=db.execute(sql).fetchall()

    body="<h1>Research Priorities</h1><p class='meta'>Research prompts from the current Reunion snapshot and Companion-held external evidence.</p>"

    materialize_existing_ryerson_discoveries(db)
    materialize_person_level_ryerson_findings(db)
    body+=render_discovery_review_section(db)

    state=("Paused" if not run["enabled"] else ("Waiting for Ryerson" if run.get("source_waiting") else "Running"))
    surname_state="Running" if surname_run["enabled"] else "Paused"
    core_names=", ".join(surname_run.get("core_surnames",[])) or "None"

    body+="<details class='card'><summary><strong>Background Research</strong> <span class='small'>Ryerson collection status and controls</span></summary>"
    body+=f"<div class='topic'><strong>Ryerson Research Runner — {state}</strong><div class='small'>Queued: {run['queued']} · Waiting: {run['retry_wait']} · Findings: {run['findings']} · No finding: {run['no_match']} · Errors: {run['failed']}</div>"
    if run["enabled"]:
        body+="<form method='post' action='/research/ryerson/runner/pause'><button type='submit'>Pause Ryerson Research</button></form>"
    else:
        body+="<form method='post' action='/research/ryerson/runner/start'><button type='submit'>Start Ryerson Research</button></form>"
    body+="</div>"

    body+=f"<div class='topic'><strong>Targeted Bootstrap — {surname_state}</strong><div class='small'>Completed: {surname_run['completed']} · Queued: {surname_run['queued']} · Waiting: {surname_run['retry_wait']} · Searching: {surname_run['searching']} · Errors: {surname_run['failed']} · Total: {surname_run['total']} · Core: {esc(core_names)}</div>"
    if surname_run["enabled"]:
        body+="<form method='post' action='/research/ryerson/targeted/pause'><button type='submit'>Pause Targeted Bootstrap</button></form>"
    else:
        body+="<form method='post' action='/research/ryerson/targeted/start'><button type='submit'>Start Targeted Bootstrap</button></form>"
    body+="</div></details>"

    death_count=len(death_rows)
    body+="<div class='card'><h2>Research Needed</h2>"
    body+=f"<div class='topic'><strong>Death research</strong><span class='badge warn' style='float:right'>{death_count}</span><div class='small'>People with a missing or incomplete Death event.</div>"
    for r in death_rows[:8]:
        if r["death_state"]=="incomplete":
            badge="<span class='badge warn' style='float:right'>Death incomplete</span>"
        else:
            badge="<span class='badge warn' style='float:right'>Death missing</span>"
        body+=f"<a class='result' href='/person/{r['person_id']}?tab=research'><strong>{esc(r['display_name'])}</strong>{badge}"
        if r["death_state"]=="incomplete" and r["death_note_text"]:
            body+="<span class='meta' style='display:block'>Existing Death event note available</span>"
        body+="</a>"
    if death_count>8:
        body+=f"<div class='small'>Showing 8 of {death_count}. Open a person to continue research.</div>"
    if not death_rows:
        body+="<p>No current missing or incomplete Death research items.</p>"
    body+="</div></div>"

    unsourced_people=len(rows)
    unsourced_total=sum(int(r["unsourced"] or 0) for r in rows)
    body+="<div class='card'><h2>Data Quality</h2>"
    body+=f"<div class='topic'><strong>Unsourced Events</strong><span class='badge warn' style='float:right'>{unsourced_total} events</span><div class='small'>{unsourced_people} people currently have events or facts without linked source or media evidence.</div>"
    for r in rows[:8]:
        body+=f"<a class='result' href='/person/{r['id']}?tab=overview'><strong>{esc(r['display_name'])}</strong><span class='badge warn' style='float:right'>{r['unsourced']} unsourced</span></a>"
    if unsourced_people>8:
        body+=f"<div class='small'>Showing 8 of {unsourced_people} people.</div>"
    if not rows:
        body+="<p>No unsourced event priorities detected.</p>"
    body+="</div></div>"

    return layout("Research",body+"</div>",active="priorities")

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
    history=""
    for x in hist:
        exists=Path(x['output_path']).expanduser().exists()
        status="" if exists else " <span class='badge warn'>Report unavailable</span>"
        actions=(f"<form method='post' action='/publication/open' class='inline-form'><input type='hidden' name='path' value='{esc(x['output_path'])}'><input type='hidden' name='origin' value='{origin_pid or ''}'><button class='secondary'>Open</button></form><form method='post' action='/publication/delete' class='inline-form'><input type='hidden' name='id' value='{x['id']}'><input type='hidden' name='origin' value='{origin_pid or ''}'><button class='secondary'>Delete</button></form>" if exists else f"<form method='post' action='/publication/remove' class='inline-form'><input type='hidden' name='id' value='{x['id']}'><input type='hidden' name='origin' value='{origin_pid or ''}'><button class='secondary'>Remove from history</button></form>")
        history+=f"<div class='topic'><strong>{esc(x['kind'])}</strong> — {esc(x.get('subject'))}{status}<br><span class='small'>{esc(x['created_at'])} · {esc(x['output_format'])} · {esc(x['output_path'])}</span><div class='publication-actions'>{actions}</div></div>"
    context=None
    person_header=""
    if origin_pid:
        row=db.execute("SELECT id,display_name FROM people WHERE id=?",(origin_pid,)).fetchone()
        context=dict(row) if row else None
        if context:
            w=person_workspace(db,origin_pid)
            if w:
                person_header=person_identity_header(db,w,presentation_mode_enabled())
    return layout("Reports",f"""{person_header}<h1>Reports</h1>{message}
<div class='card'><p>Generated family-history reports are collected here. Create new reports from a person's Publish page.</p></div>
<div class='card'><h2>Report History</h2>
{history or '<p>No reports have been generated yet.</p>'}</div>""",context,"reports")

def render_get(db,path,query=None):
    query=query or {}
    if path=="/":
        return home(db,query.get("q",""))
    if path=="/search":
        try: selected=int(query.get("selected","0") or 0) or None
        except Exception: selected=None
        return search_page(db,query.get("q",""),selected)
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
        person_context=db.execute("SELECT id,display_name FROM people WHERE id=?",(subject_id,)).fetchone() if subject_id else None
        question_body=questions_body(db,subject_id,query.get("q",""),selected_identity_id,origin_id,query.get("topic") or None)
        if subject_id and person_context:
            w=person_workspace(db,subject_id)
            if w:
                question_body=person_identity_header(db,w,presentation_mode_enabled())+question_body
        return layout("Relationship Questions",question_body,dict(person_context) if person_context else None,"ask" if subject_id else None)
    if path.startswith("/family-chart/"):
        pid=int(path.rsplit("/",1)[1])
        row=db.execute("SELECT id,display_name FROM people WHERE id=?",(pid,)).fetchone()
        chart_body=family_chart_body(db,pid,query.get("offset","0"))
        w=person_workspace(db,pid) if row else None
        if w:
            chart_body=person_identity_header(db,w,presentation_mode_enabled())+chart_body
        return layout("Interactive Family Chart",chart_body,dict(row) if row else None,"family-chart")
    if path.startswith("/person-narrative/"):
        pid=int(path.rsplit("/",1)[1])
        from .person_narrative import person_narrative
        force=str(query.get("force","")).casefold() in {"1","true","yes"}
        result=person_narrative(db,pid,force=force)
        return "<div class='biography-prose'>"+esc(result.get("narrative") or "No biographical material is recorded.")+"</div>"
    if path.startswith("/descendant-report/"):
        return descendant_report_page(db,int(path.rsplit("/",1)[1]),query)
    if path.startswith("/book-scope/"):
        return book_scope_page(db,int(path.rsplit("/",1)[1]),query)
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

        def send_json(self,obj,status=200):
            data=json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u=urlparse(self.path)
            if u.path=="/runtime/identity":
                from reunion_companion.app_identity import APP_RELEASE_DISPLAY, APP_RELEASE_NAME, ENGINE_BASELINE
                self.send_json({"service":"reunion-companion-backend","protocol":1,"application":APP_RELEASE_DISPLAY,"release_name":APP_RELEASE_NAME,"engine_baseline":ENGINE_BASELINE})
                return
            if u.path=="/setup/status":
                db=connect(db_path)
                try:
                    people=db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
                    self.send_json({"needs_genealogy_data":people==0,"people":people,"database":str(db_path)})
                finally: db.close()
                return
            q={k:v[0] for k,v in parse_qs(u.query).items()}
            if u.path.startswith("/media-file/"):
                db=connect(db_path)
                try:
                    try: mid=int(u.path.rsplit("/",1)[1])
                    except ValueError: self.send_error(404);return
                    row=db.execute("SELECT file_path FROM media WHERE id=?",(mid,)).fetchone()
                    fp=Path(row["file_path"]).expanduser() if row else None
                    if not fp or not fp.exists() or not fp.is_file(): self.send_error(404);return
                    try:
                        data=fp.read_bytes()
                    except PermissionError:
                        self.send_error(403,"Reunion media folder access has not been granted");return
                    self.send_response(200);self.send_header("Content-Type",mimetypes.guess_type(str(fp))[0] or "application/octet-stream");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data);return
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

            if u.path=="/setup/import":
                incoming=(form.get("path") or "").strip()
                try:
                    if not incoming: raise ValueError("No GEDCOM file was selected.")
                    from .safe_refresh import safe_refresh
                    result=safe_refresh(db_path,incoming)
                    db=connect(db_path)
                    try:
                        ff=active_family_file(db)
                        if not ff: raise ValueError("Companion could not establish a Family File.")
                        record_workspace_import(db,ff["id"],incoming)
                        count=db.execute("SELECT COUNT(*) FROM people").fetchone()[0]
                    finally: db.close()
                    self.send_json({"status":"success","message":f"Imported {count} people. Reunion Companion is ready."})
                except Exception as e:
                    traceback.print_exc(); self.send_json({"status":"error","message":f"{type(e).__name__}: {e}"},400)
                return

            if u.path=="/presentation/mode":
                mode=(form.get("mode") or "presentation").casefold()
                set_presentation_mode(mode != "research")
                self.send_json({"status":"success","mode":mode})
                return

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
                    if u.path.startswith("/research/discovery/"):
                        from .ryerson_discovery_review import set_discovery_state
                        parts=[p for p in u.path.split("/") if p]
                        if len(parts)==4 and parts[0]=="research" and parts[1]=="discovery":
                            try:
                                discovery_id=int(parts[2])
                            except ValueError:
                                discovery_id=0
                            action=parts[3]
                            state_map={
                                "waiting":"waiting_for_reunion",
                                "known":"already_known",
                                "reject":"rejected",
                                "defer":"deferred",
                            }
                            state=state_map.get(action)
                            if discovery_id and state:
                                set_discovery_state(db,discovery_id,state)
                                self.send_html(research_page(db))
                                return

                    if u.path in ("/research/ryerson/targeted/start","/research/ryerson/targeted/pause"):
                        from .ryerson_targeted_bootstrap import start_targeted_bootstrap,pause_targeted_bootstrap
                        if u.path.endswith("/start"):
                            start_targeted_bootstrap(db)
                        else:
                            pause_targeted_bootstrap(db)
                        self.send_html(research_page(db))
                        return

                    if u.path in ("/research/ryerson/runner/start","/research/ryerson/runner/pause"):
                        from .external_research_runner import start_runner,pause_runner,recover_transport_failures
                        if u.path.endswith("/start"):
                            recover_transport_failures(db)
                            start_runner(db)
                        else:
                            pause_runner(db)
                        self.send_html(research_page(db))
                        return

                    if u.path in ("/research/ryerson/runner/start","/research/ryerson/runner/pause"):
                        from .external_research_runner import start_runner,pause_runner
                        start_runner(db) if u.path.endswith("/start") else pause_runner(db)
                        self.send_html(research_page(db))
                        return

                    if u.path in ("/research/ryerson/runner/start","/research/ryerson/runner/pause"):
                        from .external_research_runner import start_runner,pause_runner
                        start_runner(db) if u.path.endswith("/start") else pause_runner(db)
                        self.send_html(research_page(db))
                        return

                    m=re.match(r"^/research/ryerson/import/(\d+)$",u.path)
                    if m:
                        from .ryerson_browser_assist import import_copied_ryerson_content
                        pid=int(m.group(1))
                        result=import_copied_ryerson_content(db,pid,form.get("content",""))
                        html=person_page(db,pid,"research",presentation_override=False)
                        if result["status"]=="imported":
                            msg=f"<div class='card'><span class='badge good'>Ryerson import</span> {result['stored']} finding{'s' if result['stored']!=1 else ''} imported for review.</div>"
                        elif result["parsed"]==0:
                            msg="<div class='card'><span class='badge warn'>Ryerson import</span> No recognisable Ryerson result rows were found in the pasted content.</div>"
                        else:
                            msg=f"<div class='card'><span class='badge warn'>Ryerson import</span> {result['parsed']} row{'s' if result['parsed']!=1 else ''} assessed; no acceptable finding was stored.</div>"
                        html=html.replace("<main>",f"<main>{msg}",1)
                        self.send_html(html)
                        return
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

                    m=re.match(r"^/publish/person/(\d+)/descendant-report$",u.path)
                    if m:
                        pid=int(m.group(1))
                        family_id=int(form.get('family_id','0') or 0)
                        generations=int(form.get('generations','3') or 3)
                        if not 1 <= generations <= 6:
                            raise ValueError("Generations must be between 1 and 6.")
                        row=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
                        fmt=(form.get('format') or 'HTML').upper()
                        p=standalone_descendant_report_output(db,pid,row['display_name'],generations,family_id,fmt)
                        self.send_html(descendant_report_page(db,pid,{'family':str(family_id),'generations':str(generations)},f"Published: {p}"))
                        return

                    m=re.match(r"^/publish/person/(\d+)/scoped-book$",u.path)
                    if m:
                        pid=int(m.group(1));end_pid=int(form.get('endpoint','0') or 0)
                        chosen={int(k.split('_',1)[1]) for k,v in form.items() if k.startswith('family_') and v=='1'}
                        scope=build_scope(db,pid,end_pid,4,chosen)
                        row=db.execute("SELECT display_name FROM people WHERE id=?",(pid,)).fetchone()
                        fmt=(form.get('format') or 'PDF').upper()
                        p=scoped_book_output(db,pid,end_pid,scope['selected_family_ids'],row['display_name'],fmt,4)
                        self.send_html(book_scope_page(db,pid,{'endpoint':str(end_pid)},f"Published: {p}"))
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

    from .external_research_runner import start_background_runner
    from .ryerson_targeted_bootstrap import (
        live_targeted_search,
        start_background_targeted_bootstrap,
    )
    start_background_runner(db_path)
    start_background_targeted_bootstrap(
        db_path,
        search_fn=live_targeted_search,
    )
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
