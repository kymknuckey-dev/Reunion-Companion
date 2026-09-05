from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_sidebar_has_home_without_separate_search_destination():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    live=s[s.index("<style>"):]
    assert "<a{home_cls} href='/'>Home</a>" in live
    assert "<a{search_cls} href='/search'>Search</a>" not in live

def test_home_owns_search_and_old_search_route_is_compatible():
    s=(ROOT/'src/reunion_companion/companion/beta_ui.py').read_text()
    assert 'def _home_search_results' in s
    assert 'Reuse the established Search renderer' in s
    assert 'if path in ("/", "/search"):' in s
    h=(ROOT/'src/reunion_companion/companion/ffd_home.py').read_text()
    assert "action='/' method='get'" in h

def test_home_cleanup_removes_old_operational_sections_and_compacts_glance():
    h=(ROOT/'src/reunion_companion/companion/ffd_home.py').read_text()
    rendered=h[h.index('return f"""'):]
    assert "<h2 class='ffd-section'>Family to Explore</h2>" not in rendered
    assert "<h2 class='ffd-section'>A Living Family History</h2>" not in rendered
    assert "ffd-home-glance" in rendered
    assert "Bookmarked People" in rendered

def test_release_metadata():
    expected='FFD 2.0 RC1.0.14.8.9.9.4.1.3.12.5 — Home & Search Consolidation'
    for f in ('macos_app/build_app.py','macos_app/package_dmg.py'):
        assert expected in (ROOT/f).read_text()
