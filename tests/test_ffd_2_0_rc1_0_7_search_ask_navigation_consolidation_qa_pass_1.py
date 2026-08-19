from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_release_identity_is_search_ask_navigation_consolidation():
    source=(ROOT/'macos_app'/'build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.8 — Publishing Runtime Hardening QA Pass 1"' in source

def test_companion_sidebar_has_one_no_context_discovery_entry():
    source=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    layout=source[source.index('def layout(title,body,person_context=None,active=None):'):source.index('def family_mismatch_body')]
    assert ">Companion</div><a href='/'>Home</a><a href='/search'>Search</a>" in layout
    assert "href='/questions'>Ask</a>" not in layout

def test_contextual_ask_about_is_retained():
    source=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert "href='/questions?person={pid}&origin={pid}'>Ask about</a>" in source

def test_search_question_pipeline_is_retained():
    source=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    search=source[source.index('def search_page'):source.index('def person_page')]
    assert 'is_natural_language_question(q)' in search
    assert 'answer_question(db,q,None,selected_identity_id)' in search
