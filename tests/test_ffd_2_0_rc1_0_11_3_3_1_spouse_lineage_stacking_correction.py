from pathlib import Path
import hashlib

from reunion_companion.companion.database import connect
from reunion_companion.companion.publishing_v11 import book_html
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_11_3_3_1():
    s=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.3.3.1 — Spouse Lineage Stacking Correction"' in s


def test_spouse_origin_lines_are_stacked_vertically():
    css=Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert '.spouse-origin-chart .spouse-origin-lines{display:block;margin:4mm 0 6mm}' in css
    assert '.spouse-origin-chart .spouse-origin-lines{display:grid' not in css
    assert 'grid-template-columns:1fr 1fr' not in css.split('.spouse-origin-chart .spouse-origin-lines',1)[1].split('.family-chart-pair',1)[0]


def test_spouse_chart_data_and_order_are_unchanged(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    chapter=html.split("<div class='chapter-kicker'>Chapter 2</div>",1)[1]
    spouse=chapter.split('Spouse Family &amp; Descendants',1)[1]
    assert spouse.index("Father&#x27;s Paternal Line") < spouse.index("Mother&#x27;s Paternal Line")
    assert "Wife&#x27;s Parents" in spouse
    assert "<h3>Family</h3>" in spouse
    assert "Wife&#x27;s Family &amp; Descendants" in spouse
    assert 'Line Son' in spouse
    assert 'Line Wife' in spouse
    assert 'Wife Sister' in spouse
    assert 'Sister Partner' in spouse
    assert 'Sister Child' in spouse
    assert 'Too Deep' not in spouse
    db.close()


def test_family_chart_presentation_remains_from_rc1_0_11_3_3():
    css=Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert '.family-descendant-chart .unified-lineage{display:block' in css
    assert '.family-descendant-chart .unified-parent-context{display:block}' in css
    assert '.family-descendant-chart .tree-row{border-bottom:0}' in css
    assert '.family-descendant-chart .family-central-family{border-top:2px solid currentColor;border-bottom:2px solid currentColor' in css
