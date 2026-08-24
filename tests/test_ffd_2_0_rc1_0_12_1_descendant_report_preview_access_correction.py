from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_12_1():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.1 — Descendant Report Preview Access Correction"' in s


def test_person_publish_shows_primary_descendant_report_entry(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    # RC1.0.12.2 promotes the preview to the full configuration workflow.
    # RC1.0.12.3 keeps the family-specific launch but adopts the final shorter label.
    assert "Descendant Report…" in html
    assert "/descendant-report/3" in html
    db.close()


def test_family_page_uses_same_preview_label():
    s=Path("src/reunion_companion/companion/beta_ui.py").read_text()
    assert "Configure Descendant Report…" in s or "Descendant Report…" in s
    assert "/descendant-report/{f[\"husband\"][\"id\"] if f[\"husband\"] else f[\"wife\"][\"id\"]}?family={fid}" in s
