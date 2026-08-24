from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page, descendant_report_page
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed, _person, _family


def test_release_identity_is_rc1_0_12_3():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.3 — Publish & Descendant Report UX Cleanup"' in s


def test_publish_page_uses_consistent_report_tiles(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "publish-actions" in html
    assert "Research Profile (HTML)" in html
    assert "Biography (HTML)" in html
    assert "Person Report (HTML)" in html
    assert "Descendant Report…" in html
    assert "Configure Family-history Book…" in html
    assert "Indented descendant report (1–6 generations)." in html
    db.close()


def test_publish_family_card_has_explicit_descendant_report_action(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    # RC1.0.12.4.3 removes duplicate family-specific launch cards.
    assert "<h2>Families</h2>" not in html
    assert "Descendant Report…" in html
    db.close()


def test_family_specific_descendant_configuration_fixes_starting_family(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_page(db,3,{"family":"101","generations":"3"})
    assert "Starting family" in html
    assert "Line Son and Line Wife" in html
    assert "type='hidden' name='family_id' value='101'" in html
    assert "name='family_id' required" not in html
    assert "Choose starting family" not in html
    db.close()


def test_single_family_generic_launch_is_also_unambiguous(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_page(db,3,{})
    assert "Line Son and Line Wife" in html
    assert "type='hidden' name='family_id' value='101'" in html
    assert "Choose starting family" not in html
    db.close()


def test_multiple_family_generic_launch_asks_once_then_family_launch_is_fixed(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    _person(db,50,"Second Spouse","F")
    _family(db,150,3,50,(),"1940","Adelaide")
    db.commit()
    choose=descendant_report_page(db,3,{})
    assert "Choose starting family" in choose
    assert "/descendant-report/3?family=101" in choose
    assert "/descendant-report/3?family=150" in choose
    fixed=descendant_report_page(db,3,{"family":"150"})
    assert "Choose starting family" not in fixed
    assert "Line Son and Second Spouse" in fixed
    assert "type='hidden' name='family_id' value='150'" in fixed
    db.close()


def test_generation_selector_is_clear_and_has_inclusion_summary(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_page(db,3,{"family":"101","generations":"4"})
    assert "4 generations" in html
    assert "Through great-grandchildren." in html
    for n in range(1,7):
        assert f"value='{n}'" in html
    assert "Create Print-ready PDF" in html
    assert "Create HTML" in html
    db.close()


def test_publish_ux_css_contains_responsive_tile_and_family_card_rules():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-actions{display:grid;grid-template-columns:repeat(2" in s
    assert ".publish-family-card{display:grid" in s
    assert "@media(max-width:760px)" in s


def test_descendant_report_renderer_is_not_changed_by_ux_pass():
    s=Path("src/reunion_companion/companion/descendant_report.py").read_text()
    assert "desc-family generation-" in s
    assert "desc-children" in s
    assert "desc-subfamilies" in s
    assert ".descendant-report-title .publishing-mark { width:28mm; height:28mm;" in s
