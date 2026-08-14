from __future__ import annotations
import html

PRESENTATION_ITEMS = [
    ("overview", "Overview"),
    ("family-chart", "Interactive Family Chart"),
    ("timeline", "Timeline"),
    ("biography", "Biography"),
    ("family", "Family"),
    ("media", "Media"),
    ("ask", "Ask about the Family"),
    ("publish", "Publish"),
]
RESEARCH_ITEMS = [
    ("overview", "Overview"),
    ("family-chart", "Interactive Family Chart"),
    ("timeline", "Timeline"),
    ("biography", "Biography"),
    ("family", "Family"),
    ("media", "Media"),
    ("sources", "Sources"),
    ("confidence", "Confidence"),
    ("research", "Research"),
    ("data-quality", "Data Quality"),
    ("ask", "Ask about the Family"),
    ("publish", "Publish"),
]

def items(presentation: bool):
    return PRESENTATION_ITEMS if presentation else RESEARCH_ITEMS

def href(pid: int, key: str):
    return f"/questions?person={pid}&origin={pid}" if key == "ask" else f"/person/{pid}?tab={key}"

def nav_html(pid: int, presentation: bool, active: str | None = None):
    out=[]
    for key,label in items(presentation):
        cls=" class='active'" if key == active else ""
        out.append(f"<a{cls} href='{href(pid,key)}'>{html.escape(label)}</a>")
    return "<div class='tabs ffd-person-nav'>"+"".join(out)+"</div>"

def action_cards(pid: int, presentation: bool):
    descriptions={
      "overview":"Person overview", "family-chart":"Ancestors and descendants",
      "timeline":"Follow the recorded timeline", "biography":"Read the recorded narrative",
      "family":"Explore relationships", "media":"Photos and documents", "sources":"Review supporting evidence",
      "confidence":"Review evidence coverage", "research":"Research observations and gaps",
      "data-quality":"Review data-quality opportunities", "ask":"Ask conversational family questions",
      "publish":"Create reports and family-history output",
    }
    return "".join(
      f"<a class='ffd-action-card' href='{href(pid,key)}'><span>{html.escape(label)}</span><small>{html.escape(descriptions[key])}</small></a>"
      for key,label in items(presentation)
    )
