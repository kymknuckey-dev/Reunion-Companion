from pathlib import Path
from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page, descendant_report_page
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed

def test_release_identity():
    s=Path("macos_app/build_app.py").read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.12.4.3 — Publish Families Duplication Removal"' in s

def test_person_publish_has_no_duplicate_families_section(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "<h2>Families</h2>" not in html
    assert "Select a family to configure a descendant report or view family details." not in html
    assert "Descendant Report…" in html
    assert "/descendant-report/3" in html
    db.close()

def test_primary_descendant_workflow_still_auto_selects_single_family(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=descendant_report_page(db,3,{})
    assert "Line Son and Line Wife" in html
    assert "type='hidden' name='family_id' value='101'" in html
    assert "Choose starting family" not in html
    db.close()

def test_deferred_reports_remain_available(tmp_path):
    db=connect(tmp_path/"x.sqlite3");_seed(db)
    html=person_page(db,3,"publish")
    assert "Research Profile (HTML)" in html
    assert "Biography (HTML)" in html
    assert "Person Report (HTML)" in html
    db.close()
