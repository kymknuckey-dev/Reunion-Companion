from pathlib import Path
import pytest

from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import book_scope_page
from reunion_companion.companion.publishing_v11 import book_html, _pdf_block, _image_block


def _person(db,pid,name,sex='M'):
    db.execute('INSERT INTO people(id,display_name,sex) VALUES(?,?,?)',(pid,name,sex))


def _family(db,fid,husband,wife,children=(),date=None,place=None):
    db.execute('INSERT INTO families(id,marriage_date,marriage_place) VALUES(?,?,?)',(fid,date,place))
    if husband:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Husband')",(fid,husband))
    if wife:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Wife')",(fid,wife))
    for child in children:db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,'Child')",(fid,child))


def _seed(db):
    names={
      1:('Root Father','M'),2:('Root Wife','F'),3:('Line Son','M'),4:('Root Daughter','F'),
      5:('Line Wife','F'),6:('Endpoint Son','M'),7:('Endpoint Wife','F'),
      8:('Sibling Husband','M'),9:('Sibling Child','F'),10:('Sibling Child Partner','M'),11:('Too Deep Child','M'),
      20:('Wife Father','M'),21:('Wife Mother','F'),22:('Wife Sister','F'),23:('Sister Partner','M'),24:('Sister Child','F'),
    }
    for pid,(name,sex) in names.items():_person(db,pid,name,sex)
    _family(db,100,1,2,(3,4),'1900','Adelaide')
    _family(db,101,3,5,(6,),'1930','Adelaide')
    _family(db,102,6,7,(),'1960','Adelaide')
    _family(db,200,8,4,(9,),'1925','Adelaide')
    _family(db,201,10,9,(11,),'1955','Adelaide')
    _family(db,300,20,21,(5,22),'1905','Norwood')
    _family(db,301,23,22,(24,),'1935','Norwood')
    db.commit()


def test_release_identity_is_rc1_0_11_1():
    source=Path('macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.11.1 — Family Scope & Book Presentation QA Pass 1"' in source


def test_scope_page_has_creation_spinner_and_sibling_child_context(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    html=book_scope_page(db,1,{'endpoint':'6'})
    assert 'scope-publish-progress' in html
    assert 'rc-spinner' in html
    assert 'Creating family history report' in html
    assert 'Children: Sibling Child' in html
    db.close()


def test_scoped_family_chart_keeps_sibling_children_but_stops_next_generation(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101,102])
    # Root family's chart includes its daughter's child, but not that child's child.
    first_chapter=html.split("<section class='chapter'>",2)[1]
    assert 'Sibling Child' in first_chapter
    assert 'Too Deep Child' not in first_chapter
    db.close()


def test_chart_pair_orders_main_family_before_spouse_and_uses_new_heading(tmp_path):
    db=connect(tmp_path/'scope.sqlite3');_seed(db)
    html=book_html(db,1,tmp_path/'book.html',6,end_pid=6,selected_family_ids=[100,101,102])
    assert "family-chart-pair" in html
    assert 'Spouse Family &amp; Descendants' in html
    assert 'Spouse Family Context' not in html
    chapter=html.split("Line Son",1)[1]
    assert chapter.index('Family &amp; Descendants') < chapter.index('Spouse Family &amp; Descendants')
    assert "descendant-chart spouse-context-chart" in html
    assert 'Sister Partner' in html
    assert 'Sister Child' in html
    db.close()


def test_html_pdf_preview_links_to_copied_original(tmp_path):
    fitz=pytest.importorskip('fitz')
    pdf=tmp_path/'two pages.pdf';doc=fitz.open();doc.new_page();doc.new_page();doc.save(pdf);doc.close()
    m={'id':77,'file_path':str(pdf),'title':'Two Page PDF','exists_on_disk':1}
    html=_pdf_block(m,tmp_path/'book.html')
    assert html.count("pdf-web-plate")==1
    assert 'Open original PDF' in html
    assert 'book_assets/77_two pages.pdf' in html
    assert html.count('document-source-page')==2


def test_html_image_links_to_copied_original(tmp_path):
    Image=pytest.importorskip('PIL.Image')
    image=tmp_path/'photo.png';Image.new('RGB',(40,30)).save(image)
    m={'id':88,'file_path':str(image),'title':'Photo','exists_on_disk':1}
    html=_image_block(m,output_html=tmp_path/'book.html')
    assert 'Open original image' in html
    assert 'book_assets/88_photo.png' in html
