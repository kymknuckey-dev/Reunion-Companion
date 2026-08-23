from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_visual_pass3_release_identity():
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction"' in (ROOT/'macos_app/build_app.py').read_text()

def test_visual_pass3_separates_chronology_dot_from_event_icon():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert "ffd-chronology-dot" in s
    assert "ffd-milestone-dated" in s
    assert "ffd-event-icon" in s

def test_visual_pass3_has_visible_spine_and_navy_dot():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert '.ffd-life-timeline .ffd-chronology:before' in s
    assert '.ffd-chronology-dot' in s
    assert 'background:var(--brand-navy)' in s

def test_visual_pass3_undated_rows_remain_visually_distinguishable():
    s=(ROOT/'src/reunion_companion/companion/ffd_person_story.py').read_text()
    assert "ffd-milestone-undated" in s
