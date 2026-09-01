from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.family_book_scope import (
    build_scope, paternal_person_path, paternal_family_path,
)
from reunion_companion.companion.spouse_context_chart import spouse_context_chart_html
from reunion_companion.companion.publishing_v11 import book_html, book_family_ids
from reunion_companion.companion.beta_ui import book_scope_page


def _person(db,pid,name,sex='M'):
    db.execute('INSERT INTO people(id,display_name,sex) VALUES(?,?,?)',(pid,name,sex))


def _family(db,fid,husband,wife,children=(),date=None,place=None):
    db.execute('INSERT INTO families(id,marriage_date,marriage_place) VALUES(?,?,?)',(fid,date,place))
    if husband:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,husband))
    if wife:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,wife))
    for child in children:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,child))


def _seed(db):
    # Primary paternal line: Root -> Line Son -> Endpoint.
    names={
        1:('Root Father','M'),2:('Root Wife','F'),3:('Line Son','M'),4:('Root Daughter','F'),
        5:('Line Wife','F'),6:('Endpoint Son','M'),7:('Endpoint Wife','F'),
        8:('Sibling Husband','M'),9:('Sibling Child','F'),
        20:('Wife Father','M'),21:('Wife Mother','F'),22:('Wife Sister','F'),23:('Sister Partner','M'),
        24:('Sister Child','F'),25:('Too Deep Child','M'),26:('Sister Child Partner','M'),
    }
    for pid,(name,sex) in names.items():_person(db,pid,name,sex)
    _family(db,100,1,2,(3,4),'1900','Adelaide')
    _family(db,101,3,5,(6,),'1930','Adelaide')
    _family(db,102,6,7,(),'1960','Adelaide')
    # Root Daughter's family is a manual candidate but not on the default line.
    _family(db,200,8,4,(9,),'1925','Adelaide')
    # Incoming spouse (Line Wife) family of origin and sibling context.
    _family(db,300,20,21,(5,22),'1905','Norwood')
    _family(db,301,23,22,(24,),'1935','Norwood')
    # This is deliberately one generation too deep for spouse-context traversal.
    _family(db,302,26,24,(25,),'1965','Norwood')
    db.commit()


def test_release_identity_is_rc1_0_11():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11 — Family-based Book Scope & Lineage Selection"' in source


def test_paternal_path_uses_recorded_father_relationships(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    assert paternal_person_path(db,1,6)==[1,3,6]
    fams,main=paternal_family_path(db,1,6)
    assert fams==[100,101,102]
    assert main=={100:1,101:3,102:6}
    db.close()


def test_default_scope_selects_line_families_but_keeps_sibling_family_chart_only(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    scope=build_scope(db,1,6,6)
    assert scope['selected_family_ids']==[100,101,102]
    states={e.family_id:e.state for e in scope['entries']}
    assert states[100]=='book_section'
    assert states[101]=='book_section'
    assert states[102]=='book_section'
    assert states[200]=='chart_only'
    db.close()


def test_manual_family_promotion_adds_only_that_family(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    scope=build_scope(db,1,6,6,{100,101,102,200})
    assert scope['selected_family_ids']==[100,101,200,102]
    # RC1.0.14.8.9.9.4.1.3.8 now keeps selected sibling-family chapters
    # together before descending into the next generation. Root Daughter's
    # promoted family therefore stays beside Line Son's family before Endpoint.
    # No collateral family is selected merely because it is available.
    assert 300 not in scope['selected_family_ids']
    db.close()


def test_scoped_book_has_only_selected_family_chapters(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    selected=[100,101,102]
    assert book_family_ids(db,1,6,6,selected)==selected
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=selected)
    assert html.count("<section class='chapter'>")==3
    assert 'Root Father and Root Wife' in html
    assert 'Line Son and Line Wife' in html
    assert 'Endpoint Son and Endpoint Wife' in html
    # The sibling's spouse family does not become a chapter/contents entry.
    assert 'Chapter 4' not in html
    db.close()


def test_spouse_context_includes_sibling_partner_and_children_then_stops(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    html=spouse_context_chart_html(db,101,3)
    assert 'Line Wife' in html
    assert 'Wife Father' in html and 'Wife Mother' in html
    assert 'Wife Sister' in html
    assert 'Sister Partner' in html
    assert 'Sister Child' in html
    assert 'Too Deep Child' not in html
    assert 'Chart context only' in html
    db.close()


def test_family_selector_exposes_book_section_and_chart_only_states(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    html=book_scope_page(db,1,{'endpoint':'6'})
    assert 'Family-history Book Scope' in html
    assert 'Paternal path' in html
    assert 'Chart only' in html
    assert "name='family_100'" in html
    assert "name='family_200'" in html
    assert 'Create Print-ready PDF' in html
    assert 'Spouse context rule' in html
    db.close()
