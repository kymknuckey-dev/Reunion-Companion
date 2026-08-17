from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def source(name):
    return (ROOT/'src'/'reunion_companion'/'companion'/name).read_text()

def test_release_identity_is_navigation_qa_pass_1():
    s=(ROOT/'macos_app'/'build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.7 — Person Presentation & Application Navigation — Navigation QA Pass 1"' in s

def test_global_top_navigation_and_visible_build_identity_are_removed():
    s=source('beta_ui.py')
    layout=s[s.index('def layout(title,body,person_context=None,active=None):'):s.index('def family_mismatch_body')]
    assert "<nav>\n<a href='/'>Home</a><a href='/search'>Search</a><a href='/reports'>Reports</a>" not in layout
    assert 'FFD_DISPLAY' not in layout
    assert 'presentation-banner' not in layout

def test_mode_control_and_family_selector_share_utility_header():
    s=source('beta_ui.py')
    assert "Presentation</button>" in s
    assert "Research</button>" in s
    assert "{mode_control_html(presentation)}{family_selector_html()}" in s
    assert 'action=\'/presentation/mode\'' in s

def test_sidebar_before_person_is_companion_only():
    s=source('beta_ui.py')
    layout=s[s.index('def layout(title,body,person_context=None,active=None):'):s.index('def family_mismatch_body')]
    assert ">Companion</div><a href='/'>Home</a><a href='/search'>Search</a><a href='/questions'>Ask</a>" in layout
    assert "href='/search'>People" not in layout
    assert ">Explore</div>" not in layout
    assert "href='/places'>Places" not in layout

def test_presentation_context_navigation_and_output_are_person_specific():
    s=source('beta_ui.py')
    assert '("family-chart","Family Chart"' in s
    assert '("media","Media"' in s
    assert "Ask about</a>" in s
    assert "href='/person/{pid}?tab=publish'>Publish" in s
    assert "href='/reports?origin={pid}'>Reports" in s

def test_research_context_adds_research_only_destinations():
    s=source('beta_ui.py')
    assert '("sources","Sources"' in s
    assert '("confidence","Confidence"' in s
    assert '("research","Research"' in s
    assert '("data-quality","Data Quality"' in s
    assert 'heading=name if presentation else f"Research — {name}"' in s

def test_person_pages_no_longer_render_horizontal_person_nav():
    s=source('beta_ui.py')
    person=s[s.index('def person_page'):s.index('def family_page')]
    assert 'nav_html(' not in person
    routes=s[s.index('def render_get'):s.index('def _post_form')]
    assert 'nav_html(' not in routes
