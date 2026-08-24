from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.publishing_v11 import book_html
from test_ffd_2_0_rc1_0_11_2_unified_family_charts_html_book_qa_pass_2 import _seed, _person, _family


def _seed_origin(db):
    _seed(db)
    _person(db,40,'Mother Father','M');_person(db,41,'Mother Mother','F')
    _person(db,42,'Mother Paternal Grandfather','M');_person(db,43,'Mother Paternal Grandmother','F')
    _family(db,390,42,43,(40,))
    _family(db,391,40,41,(21,))
    db.commit()


def _spouse_section(html):
    chapter=html.split("<div class='chapter-kicker'>Chapter 2</div>",1)[1]
    return chapter.split('Spouse Family &amp; Descendants',1)[1].split("</section></div></section>",1)[0]


def test_release_identity_is_rc1_0_11_3_2():
    s=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.3.2 — Spouse Family-of-Origin Chart Correction"' in s


def test_spouse_chart_father_line_comes_from_wifes_father_not_current_husband(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed_origin(db)
    s=_spouse_section(book_html(db,1,tmp_path/'b.html',6,end_pid=6,selected_family_ids=[100,101]))
    father=s.split("Father&#x27;s Paternal Line",1)[1].split("Mother&#x27;s Paternal Line",1)[0]
    assert 'Wife Paternal Grandfather' in father
    assert 'Paternal Great Grandfather' not in father
    db.close()


def test_spouse_chart_mother_line_comes_from_wifes_mother(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed_origin(db)
    s=_spouse_section(book_html(db,1,tmp_path/'b.html',6,end_pid=6,selected_family_ids=[100,101]))
    mother=s.split("Mother&#x27;s Paternal Line",1)[1].split("Wife&#x27;s Parents",1)[0]
    assert 'Mother Paternal Grandfather' in mother
    assert 'Wife Paternal Grandfather' not in mother
    db.close()


def test_wifes_parents_are_shown_and_current_marriage_remains_family(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed_origin(db)
    s=_spouse_section(book_html(db,1,tmp_path/'b.html',6,end_pid=6,selected_family_ids=[100,101]))
    parents=s.split("Wife&#x27;s Parents",1)[1].split("<h3>Family</h3>",1)[0]
    family=s.split("<h3>Family</h3>",1)[1].split("Wife&#x27;s Family &amp; Descendants",1)[0]
    assert 'Wife Father' in parents and 'Wife Mother' in parents
    assert 'Line Son' in family and 'Line Wife' in family
    assert 'Wife Father' not in family and 'Wife Mother' not in family
    db.close()


def test_wifes_family_descendants_are_parents_children_spouses_and_children_then_stop(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed_origin(db)
    s=_spouse_section(book_html(db,1,tmp_path/'b.html',6,end_pid=6,selected_family_ids=[100,101]))
    d=s.split("Wife&#x27;s Family &amp; Descendants",1)[1]
    assert 'Line Wife' in d                 # wife as a child of her parents
    assert 'Line Son' in d                  # her current spouse beside her
    assert 'Endpoint Son' in d              # their child
    assert 'Wife Sister' in d
    assert 'Sister Partner' in d
    assert 'Sister Child' in d
    assert 'Too Deep' not in d
    assert "Spouse&#x27;s siblings" not in s
    db.close()


def test_spouse_chart_uses_rules_not_colour_and_can_stack_origin_lines(tmp_path):
    css=Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    # RC1.0.11.3.3.1 supersedes the earlier side-by-side default: the two
    # spouse family-of-origin lines now stack vertically at all widths.
    assert '.spouse-origin-chart .spouse-origin-lines{display:block;margin:4mm 0 6mm}' in css
    assert '.spouse-origin-chart .spouse-origin-lines{display:grid' not in css
    assert '.spouse-origin-chart .tree-row{border-bottom:0}' in css
    assert '.spouse-origin-chart .spouse-central-family{border-top:2px solid currentColor;border-bottom:2px solid currentColor' in css


def test_html_and_pdf_continue_to_share_spouse_chart_source(tmp_path):
    db=connect(tmp_path/'x.sqlite3');_seed_origin(db)
    html=book_html(db,1,tmp_path/'b.html',6,end_pid=6,selected_family_ids=[100,101])
    assert "Father&#x27;s Paternal Line" in html
    assert "Mother&#x27;s Paternal Line" in html
    assert "Wife&#x27;s Family &amp; Descendants" in html
    source=Path('src/reunion_companion/companion/publishing_v11.py').read_text()
    assert 'write_book(db,start_pid,html,generations,theme,end_pid,selected_family_ids)' in source
    db.close()
