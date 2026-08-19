from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_life_at_a_glance_removed_and_life_story_retained():
    text=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert 'Life at a Glance' not in text
    assert '>Life Story<' in text

def test_family_portraits_support_real_media_and_three_brand_placeholders():
    text=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert '_person_portrait' in text
    assert 'ffd-family-thumb' in text
    for name in ('PersonMale.png','PersonFemale.png','PersonNeutral.png'):
        assert (ROOT/'src/reunion_companion/companion/branding_assets'/name).is_file()
        assert name in text

def test_current_release_identity_is_pass2():
    text=(ROOT/'macos_app/build_app.py').read_text()
    assert 'FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6' in text
