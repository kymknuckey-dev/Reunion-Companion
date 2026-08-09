from __future__ import annotations

THEMES={
"Dad Classic":{
    "description":"Traditional family-history book layout modelled on the established family-by-family structure.",
    "css":"""
      body { font-family: Georgia, 'Times New Roman', serif; color:#222; line-height:1.45; }
      h1,h2,h3 { font-family: Georgia, 'Times New Roman', serif; }
      h1 { text-align:center; border-bottom:2px solid #555; }
      .chapter-kicker { text-align:center; letter-spacing:.08em; text-transform:uppercase; font-size:9pt; }
      .overview { border:1px solid #aaa; padding:4mm; }
    """
},
"Clean Modern":{
    "description":"Simple modern presentation for screen reading and contemporary printing.",
    "css":"""
      body { font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif; color:#202020; }
      h1,h2,h3 { font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif; }
      h1 { border-bottom:4px solid #333; }
      .overview { border-left:5px solid #777; padding-left:4mm; }
    """
},
"Research Edition":{
    "description":"Evidence-forward layout with stronger source and research-review visibility.",
    "css":"""
      body { font-family:Georgia,'Times New Roman',serif; }
      .evidence-block,.research-block { border:1px solid #999; padding:3mm; }
      .research-only { display:block !important; }
    """
}
}
DEFAULT_THEME="Dad Classic"

def theme_names():
    return list(THEMES)

def theme_css(name=None):
    key=name or DEFAULT_THEME
    return THEMES.get(key,THEMES[DEFAULT_THEME])["css"]

def format_themes():
    L=["Publication Themes","==================",""]
    for name,data in THEMES.items():
        marker=" (default)" if name==DEFAULT_THEME else ""
        L.append(f"{name}{marker}")
        L.append(f"  {data['description']}")
        L.append("")
    return "\n".join(L)
