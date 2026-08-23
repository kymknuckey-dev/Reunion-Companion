from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_pass2_release_identity():
    s=(ROOT/'macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.10 — Multi-page PDF Reproduction QA Pass 1"' in s

def test_utility_header_neutralises_presentation_button_enlargement():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert '.presentation button,.presentation .button{font-size:18px;padding:12px 16px}' in s
    assert '.rc-utility-header .rc-mode-option{font-size:14px!important;padding:8px 12px!important' in s
    assert '.rc-utility-header select{font-size:14px!important;padding:8px 10px!important' in s

def test_research_overview_uses_event_source_references_not_counts():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'SELECT source_id FROM event_sources WHERE event_id=? ORDER BY source_id' in s
    assert 'Source {int(sid)}' in s
    assert "Sources {source_count}" not in s
