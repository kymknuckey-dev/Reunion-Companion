from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.publishing_v11 import book_html
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed


def test_release_identity_is_rc1_0_11_3_1():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.3.1 — Spouse Family Chart Root Correction"' in source


def _spouse_section(html):
    # Isolate the continuing family's chapter first; the book may contain an
    # earlier spouse-context chart for the starting family as well.
    chapter=html.split("<div class='chapter-kicker'>Chapter 2</div>",1)[1]
    return chapter.split('Spouse Family &amp; Descendants',1)[1].split("</section></div></section>",1)[0]


def test_spouse_chart_central_family_is_actual_married_couple(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    spouse=_spouse_section(html)
    family_pos=spouse.index('<h3>Family</h3>')
    descendants_pos=spouse.index("<h3>Wife&#x27;s Family &amp; Descendants</h3>")
    family_block=spouse[family_pos:descendants_pos]
    assert 'Line Son' in family_block
    assert 'Line Wife' in family_block
    assert 'Wife Father' not in family_block
    assert 'Wife Mother' not in family_block
    db.close()


def test_spouse_parents_are_context_above_actual_family(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    spouse=_spouse_section(book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101]))
    family_pos=spouse.index('<h3>Family</h3>')
    assert spouse.index('Wife Father') < family_pos
    assert spouse.index('Wife Mother') < family_pos
    assert spouse.index('Wife Paternal Grandfather') < family_pos
    db.close()


def test_spouse_descendants_belong_to_actual_couple_and_collateral_branch_stops(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    spouse=_spouse_section(book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101]))
    descendants=spouse.split("<h3>Wife&#x27;s Family &amp; Descendants</h3>",1)[1]
    assert 'Endpoint Son' in descendants
    assert 'Wife Sister' in descendants
    assert 'Sister Partner' in descendants
    assert 'Sister Child' in descendants
    assert 'Too Deep' not in spouse
    db.close()


def test_html_and_pdf_share_corrected_spouse_chart_source(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    spouse=_spouse_section(html)
    assert 'Line Son' in spouse and 'Line Wife' in spouse
    source=Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert 'write_book(db,start_pid,html,generations,theme,end_pid,selected_family_ids)' in source
    db.close()
