from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.descendant_chart import chart_html
from reunion_companion.companion.publishing_v11 import book_html
from reunion_companion.companion.beta_ui import book_scope_page


def _person(db,pid,name,sex='M'):
    db.execute('INSERT INTO people(id,display_name,sex) VALUES(?,?,?)',(pid,name,sex))


def _family(db,fid,husband,wife,children=(),date=None,place=None):
    db.execute('INSERT INTO families(id,marriage_date,marriage_place) VALUES(?,?,?)',(fid,date,place))
    if husband:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,husband))
    if wife:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,wife))
    for child in children:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,child))


def _seed(db):
    names={
      1:('Root Husband','M'),2:('Root Wife','F'),3:('Line Son','M'),4:('Line Daughter','F'),5:('Line Wife','F'),6:('Endpoint Son','M'),
      10:('Root Father','M'),11:('Root Mother','F'),12:('Paternal Grandfather','M'),13:('Paternal Grandmother','F'),14:('Paternal Great Grandfather','M'),15:('Paternal Great Grandmother','F'),
      20:('Wife Father','M'),21:('Wife Mother','F'),22:('Wife Sister','F'),23:('Sister Partner','M'),24:('Sister Child','F'),25:('Too Deep','M'),
      30:('Wife Paternal Grandfather','M'),31:('Wife Paternal Grandmother','F'),
    }
    for pid,(name,sex) in names.items():_person(db,pid,name,sex)
    _family(db,90,14,15,(12,))
    _family(db,91,12,13,(10,))
    _family(db,92,10,11,(1,))
    _family(db,100,1,2,(3,4),'1900','Adelaide')
    _family(db,101,3,5,(6,),'1930','Adelaide')
    _family(db,290,30,31,(20,))
    _family(db,300,20,21,(5,22),'1905','Norwood')
    _family(db,301,23,22,(24,),'1935','Norwood')
    _family(db,302,25,24,(),'1960','Norwood')
    db.commit()


def test_release_identity_is_rc1_0_11_2():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.2 — Unified Family Charts & HTML Book QA Pass 2"' in source


def test_master_family_chart_puts_direct_paternal_couples_above_husbands_parents(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=chart_html(db,1,2,2)
    assert "Husband&#x27;s Descendants" in html
    assert html.index('Paternal Great Grandfather') < html.index('Paternal Grandfather') < html.index("Husband&#x27;s parents")
    assert 'Paternal Great Grandmother' in html
    assert 'Paternal Grandmother' in html
    db.close()


def test_spouse_chart_reuses_master_layout_and_natural_family_grouping(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    chapter=html.split('Line Son',1)[1]
    assert 'Family &amp; Descendants' in chapter
    assert 'Spouse Family &amp; Descendants' in chapter
    assert chapter.index('Family &amp; Descendants') < chapter.index('Spouse Family &amp; Descendants')
    assert "descendant-chart spouse-context-chart" in chapter
    assert 'Wife Father' in chapter and 'Wife Mother' in chapter
    assert 'Wife Sister' in chapter and 'Sister Partner' in chapter and 'Sister Child' in chapter
    assert 'Too Deep' not in chapter
    assert 'Wife Paternal Grandfather' in chapter and 'Wife Paternal Grandmother' in chapter
    db.close()


def test_scope_html_button_preserves_format_before_buttons_are_disabled(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_scope_page(db,1,{'endpoint':'6'})
    assert "e.submitter" in html
    assert "h.name=s.name" in html
    assert "h.value=s.value" in html
    assert "value='HTML'" in html
    db.close()


def test_scoped_html_document_is_family_history_not_research_person_report(tmp_path):
    db=connect(tmp_path/'family.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101])
    assert "<section class='title-page'>" in html
    assert '<h1>Family History</h1>' in html
    assert "<section class='toc pagebreak'>" in html
    assert 'Research Profile' not in html
    assert '<h2>Research</h2>' not in html
    db.close()
