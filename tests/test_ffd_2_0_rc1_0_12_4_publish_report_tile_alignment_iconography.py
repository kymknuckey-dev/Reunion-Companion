from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_12_4():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.4 — Publish Report Tile Alignment & Iconography"' in s


def test_publish_actions_use_icons_not_letter_badges(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "<svg" in html
    assert "Research Profile (HTML)" in html
    assert "Biography (HTML)" in html
    assert "Person Report (HTML)" in html
    assert "Descendant Report…" in html
    assert "Configure Family-history Book…" in html
    for letter in (">P<",">B<",">R<",">D<",">F<"):
        assert letter not in html
    db.close()


def test_descendant_and_book_actions_share_same_tile_structure(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "publish-action primary-action" in html
    # RC1.0.12.4.2 moves the full-width span to the shared outer form so
    # the inner button keeps the identical tile box model.
    assert "publish-action-form wide" in html
    assert html.count("publish-action-chevron") >= 5
    assert html.count("publish-action-icon") >= 5
    db.close()


def test_family_cards_removed_by_final_publish_cleanup(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "<h2>Families</h2>" not in html
    assert "Descendant Report…" in html
    db.close()

def test_report_renderers_are_untouched_by_tile_pass():
    desc=Path("src/reunion_companion/companion/descendant_report.py").read_text()
    assert "desc-family generation-" in desc
    assert "write_descendant_report_pdf" in desc
    publish=Path("src/reunion_companion/companion/beta3_publishing.py").read_text()
    assert "standalone_descendant_report_output" in publish
