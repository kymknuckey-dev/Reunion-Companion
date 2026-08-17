from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_person_presentation_qa1_release_identity():
    s=(ROOT/'macos_app'/'build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.7 — Visual Presentation QA Pass 2"' in s

def test_presentation_overview_uses_single_editorial_identity_hero():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'return layout(p["display_name"],person_story_body(db,w,True),p,"overview")' in s

def test_person_story_prioritises_human_facts_without_database_counter_fallbacks():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert 'Life Story' in s
    assert 'Spouse' in s
    assert 'Immediate Family' in s
    assert 'occupation' in s
    assert 'Recorded life events' not in s

def test_person_story_has_editorial_life_family_and_media_structure():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert "<h2 class='ffd-section'>Life Story</h2>" in s
    assert 'Immediate Family' in s
    assert 'ffd-media-strip' in s
    assert 'View person →' not in s

def test_life_sequence_is_date_led_where_dates_are_available():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert 'def _event_sort_key' in s
    assert 'sorted(clean,key=_event_sort_key)' in s
