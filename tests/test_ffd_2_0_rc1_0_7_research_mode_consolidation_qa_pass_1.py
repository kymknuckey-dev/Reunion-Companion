from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    s=(ROOT/'macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6"' in s

def test_research_home_is_three_purpose_consolidation():
    s=(ROOT/'src/reunion_companion/companion/ffd_home.py').read_text()
    assert 'Research Priorities' in s and 'Improve the Data' in s and 'Data Manager' in s
    block=s[s.index('research_explore='):s.index('return f"""',s.index('research_explore='))]
    for old in ('Find a Person','<h2>Places</h2>','<h2>Sources</h2>','<h2>Media</h2>','<h2>Reports</h2>'):
        assert old not in block

def test_research_person_nav_is_consolidated():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    nav=s[s.index('research=[] if presentation else'):s.index('rows=[]',s.index('research=[] if presentation else'))]
    assert 'Sources' in nav
    assert 'Confidence' not in nav and 'Data Quality' not in nav and '("research","Research"' not in nav
    assert 'Ask about' in s

def test_research_overview_is_evidence_dashboard():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert "confidence_by_id=" in s
    assert 'Source {int(sid)}' in s
    assert 'Needs evidence' in s and 'Supported' in s
    assert "href='/person/{pid}?tab=sources'" in s

def test_quality_centre_consolidates_place_and_unsourced_facts():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    q=s[s.index('def quality_page'):s.index('def quality_items_page')]
    assert 'Place variants' in q
    assert 'Unsourced events / facts' in q
    assert 'Missing birth places' not in q
    assert 'Missing death places' not in q

def test_smaller_research_header_is_canonical():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert '.presentation header{padding:17px 24px}' not in s
    assert '.presentation header strong a{font-size:19px}' not in s
