from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_visual_pass2_release_identity():
    assert 'APP_RELEASE="FFD 2.0 RC1.0.7 — Visual Presentation QA Pass 2"' in (ROOT/'macos_app/build_app.py').read_text()

def test_visual_pass2_has_explicit_photo_and_no_photo_hero_states():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert "ffd-hero-has-photo" in s
    assert "ffd-hero-no-photo" in s

def test_visual_pass2_uses_portrait_ratio_and_no_photo_full_width():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'aspect-ratio:4/5' in s
    assert '.ffd-person-editorial.ffd-hero-no-photo .ffd-hero-layout{{display:block}}' in s

def test_visual_pass2_restores_chronology_dot_separately_from_icon():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert '.ffd-life-sequence .ffd-milestone:after' in s
    assert 'background:var(--brand-navy)!important' in s
    assert '.ffd-life-sequence .ffd-event-icon{{z-index:3}}' in s
