from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_12_4_2():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.4.2 — Publish Tile DOM Alignment Correction"' in s


def test_all_five_person_publish_actions_share_form_button_dom(tmp_path):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    html=person_page(db,3,"publish")
    assert html.count("publish-action-form") >= 5
    assert html.count("button class='publish-action") >= 5
    assert "<a class='publish-action" not in html
    db.close()


def test_descendant_and_book_navigation_use_get_forms(tmp_path):
    db=connect(tmp_path/"x.sqlite3"); _seed(db)
    html=person_page(db,3,"publish")
    assert "method='get' action='/descendant-report/3'" in html
    assert "method='get' action='/book-scope/3'" in html
    db.close()


def test_shared_button_uses_identical_fixed_grid_columns():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-action{display:grid;grid-template-columns:42px minmax(0,1fr) 18px" in s
    assert ".publish-action-form>button.publish-action{height:100%" in s


def test_book_wide_span_is_on_form_not_inner_button():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-action-form.wide{grid-column:1/-1}" in s
    assert "class='publish-action-form wide' method='get' action='/book-scope/{pid}'" in s
    assert "class='publish-action wide'" not in s


def test_descendant_optical_centring_is_retained():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-action-icon.descendant-icon svg{transform:translateY(-1.5px)}" in s
