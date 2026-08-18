from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_current_release_identity():
    s=(ROOT/"macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.7 — Research Mode Consolidation QA Pass 2"' in s

def test_companion_sidebar_has_home_and_search_but_no_global_ask():
    s=(ROOT/"src/reunion_companion/companion/beta_ui.py").read_text()
    companion="<div class='rc-side-section rc-side-section-first'>Companion</div><a href='/'>Home</a><a href='/search'>Search</a>"
    assert companion in s
    assert companion + "<a href='/questions'>Ask</a>" not in s

def test_contextual_ask_about_is_retained():
    s=(ROOT/"src/reunion_companion/companion/beta_ui.py").read_text()
    assert "href='/questions?person={pid}&origin={pid}'>Ask about</a>" in s

def test_questions_route_remains_available_for_contextual_ask():
    s=(ROOT/"src/reunion_companion/companion/beta_ui.py").read_text()
    assert "path == '/questions'" in s or '"/questions"' in s or "'/questions'" in s
