from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_12_4_1():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.4.1 — Publish Icon Column Alignment Correction"' in s


def test_publish_tiles_use_fixed_icon_text_chevron_grid():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-action{display:grid;grid-template-columns:42px minmax(0,1fr) 18px" in s
    assert "column-gap:12px" in s


def test_icon_container_has_fixed_geometry_and_optical_centering():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-action-icon{width:42px;height:42px" in s
    assert "display:grid;place-items:center" in s
    assert ".publish-action-icon.descendant-icon svg{transform:translateY(-1.5px)}" in s


def test_family_cards_share_same_42px_icon_column():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert ".publish-family-card>div:first-child{display:grid!important;grid-template-columns:42px minmax(0,1fr)" in s


def test_descendant_icon_gets_specific_optical_alignment_class(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "publish-action-icon descendant-icon" in html
    assert "Descendant Report…" in html
    db.close()


def test_report_generation_modules_are_untouched_by_alignment_pass():
    desc=Path("src/reunion_companion/companion/descendant_report.py").read_text()
    assert "write_descendant_report_pdf" in desc
    publish=Path("src/reunion_companion/companion/beta3_publishing.py").read_text()
    assert "standalone_descendant_report_output" in publish
