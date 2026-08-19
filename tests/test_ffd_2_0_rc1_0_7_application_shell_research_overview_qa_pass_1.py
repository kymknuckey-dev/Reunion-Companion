from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source():
    return (ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()

def test_release_identity_is_application_shell_research_overview_pass():
    s=(ROOT/'macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6"' in s

def test_header_brand_geometry_is_mode_independent():
    s=source()
    assert '.rc-header-mark{width:46px;height:46px' in s
    assert '.rc-brand span{font-size:20px}' in s
    assert '.presentation .rc-header-mark' not in s
    assert '.presentation .rc-brand span' not in s
    assert "{family_selector_html()}{mode_control_html(presentation)}" in s

def test_research_overview_no_longer_renders_internal_navigation_cards():
    s=source()
    block=s[s.index('    if tab=="overview":'):s.index('    elif tab=="timeline"')]
    assert 'action_cards' not in block
    assert 'ffd-story-actions' not in block
    assert 'rc-research-overview' in block
    assert 'Person Overview' in block

def test_sidebar_remains_navigation_owner():
    s=source()
    assert "<div class='rc-side-section rc-side-section-first'>Companion</div><a href='/'>Home</a><a href='/search'>Search</a>" in s
    assert '_sidebar_person_links(person_context,presentation,active)' in s
