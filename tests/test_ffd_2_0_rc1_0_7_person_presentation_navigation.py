from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_rc107_release_identity():
    source=(ROOT/'macos_app'/'build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.7 — Person Presentation & Application Navigation' in source

def test_rc107_application_sidebar_is_part_of_global_layout():
    source=(ROOT/'src'/'reunion_companion'/'companion'/'beta_ui.py').read_text()
    assert "class='rc-sidebar'" in source
    assert "href='/questions'>Ask" in source
    assert "href='/reports?origin={pid}'>Reports" in source

def test_rc107_person_identity_is_separate_from_person_navigation():
    story=(ROOT/'src'/'reunion_companion'/'companion'/'ffd_person_story.py').read_text()
    assert "def person_identity_header" in story
    assert "rc-person-strip" in story
    assert "Key Life Events" in story

def test_rc107_overview_removes_duplicate_navigation_blocks():
    story=(ROOT/'src'/'reunion_companion'/'companion'/'ffd_person_story.py').read_text()
    assert "action_cards" not in story
    assert "Explore Further" not in story
    assert "ffd-media-strip" in story
