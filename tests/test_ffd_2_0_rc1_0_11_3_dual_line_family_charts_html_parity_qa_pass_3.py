from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.descendant_chart import chart_html
from reunion_companion.companion.publishing_v11 import book_html
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_11_3():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.3 — Dual-Line Family Charts & HTML Parity QA Pass 3"' in source


def test_master_chart_has_distinct_husband_and_wife_descendant_sides(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    # Use the continuing couple: both sides have recorded ancestry in the fixture.
    html=chart_html(db,3,5,2)
    assert "Husband&#x27;s Descendants" in html
    assert "Wife&#x27;s Descendants" in html
    assert "husband-descendants" in html
    assert "wife-descendants" in html
    assert html.index("Husband&#x27;s Descendants") < html.index("Husband&#x27;s parents")
    assert html.index("Wife&#x27;s Descendants") < html.index("Wife&#x27;s parents")
    assert 'Paternal Grandfather' in html
    assert 'Wife Paternal Grandfather' in html
    db.close()


def test_spouse_family_chart_uses_same_dual_line_master_template(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    spouse=html.split('Spouse Family &amp; Descendants',1)[1]
    assert "Husband&#x27;s Descendants" in spouse
    assert "Wife&#x27;s Descendants" in spouse
    assert "husband-descendants" in spouse
    assert "wife-descendants" in spouse
    assert 'Wife Paternal Grandfather' in spouse
    assert 'Sister Child' in spouse
    assert 'Too Deep' not in spouse
    db.close()


def test_html_history_book_contains_both_family_chart_sections_and_both_lines(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    assert '<h1>Family History</h1>' in html
    assert 'Family &amp; Descendants' in html
    assert 'Spouse Family &amp; Descendants' in html
    # HTML and PDF share book_html; these labels must therefore exist in the
    # persisted HTML report rather than only in PDF-specific presentation.
    assert html.count("Husband&#x27;s Descendants") >= 2
    assert html.count("Wife&#x27;s Descendants") >= 2
    assert 'Research Profile' not in html
    db.close()


def test_embedded_book_charts_remain_bounded_and_future_deep_report_is_documented(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    assert 'Sister Child' in html
    assert 'Too Deep' not in html
    spec=Path('RC1.0.11.3_DUAL_LINE_FAMILY_CHARTS_HTML_PARITY_QA_PASS_3.md').read_text()
    assert 'standalone Family & Descendants report' in spec
    assert 'do not implement in RC1.0.11.3' in spec
    db.close()
