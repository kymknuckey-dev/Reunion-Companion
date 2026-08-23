from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_visual_pass_release_identity():
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1"' in (ROOT/'macos_app/build_app.py').read_text()

def test_overview_uses_polished_event_icon_timeline():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert 'ffd-event-icon' in s
    assert 'ffd-milestone-date' in s
    assert 'View full Timeline' not in s
    assert 'View full Family' not in s

def test_family_selector_precedes_mode_control():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert '{family_selector_html()}{mode_control_html(presentation)}' in s

def test_companion_person_placeholders_exist():
    for name in ('PersonMale.png','PersonFemale.png','PersonNeutral.png'):
        assert (ROOT/'src/reunion_companion/companion/branding_assets'/name).is_file()
