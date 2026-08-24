from pathlib import Path
import hashlib

from reunion_companion.companion.database import connect
from reunion_companion.companion.descendant_chart import chart_html
from reunion_companion.companion.spouse_context_chart import spouse_context_chart_html
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_11_3_3():
    s=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.3.3 — Unified Family Chart Presentation"' in s


def test_family_chart_data_remains_present_after_presentation_change(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed(db)
    html=chart_html(db,3,5,2)
    for name in ('Line Son','Line Wife','Root Husband','Root Wife','Wife Father','Wife Mother',
                 'Paternal Grandfather','Wife Paternal Grandfather','Endpoint Son'):
        assert name in html
    db.close()


def test_family_chart_uses_stacked_spouse_style_sections(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed(db)
    html=chart_html(db,3,5,2)
    assert "family-descendant-chart" in html
    assert "unified-lineage" in html
    assert "unified-parent-context" in html
    assert "family-central-family" in html
    assert "family-descendants" in html
    css=Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert '.family-descendant-chart .unified-lineage{display:block' in css
    assert '.family-descendant-chart .unified-parent-context{display:block}' in css
    assert '.family-descendant-chart .tree-row{border-bottom:0}' in css
    assert '.family-descendant-chart .family-central-family{border-top:2px solid currentColor;border-bottom:2px solid currentColor' in css
    db.close()


def test_spouse_chart_renderer_is_not_modified_by_presentation_unification():
    # Guard the established spouse chart implementation against accidental edits
    # in this presentation-only pass.
    source=Path('src/reunion_companion/companion/spouse_context_chart.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == '489b453945d14e511a95d3964c2ad6fd0f6d2d29044845273bb4149e50474fa9'


def test_spouse_chart_still_has_agreed_family_of_origin_sections(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed(db)
    html=spouse_context_chart_html(db,101,3)
    for text in ("Father&#x27;s Paternal Line","Mother&#x27;s Paternal Line",
                 "Wife&#x27;s Parents","<h3>Family</h3>","Wife&#x27;s Family &amp; Descendants"):
        assert text in html
    db.close()
