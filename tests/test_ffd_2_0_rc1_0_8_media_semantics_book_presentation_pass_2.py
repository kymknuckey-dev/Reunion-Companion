from pathlib import Path
from PIL import Image
from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.family_publication_model import person_document_groups, family_publication_media
from reunion_companion.companion.ffd_person_story import _person_portrait
from reunion_companion.companion.publishing_v11 import _person_section

def _ged(path, body):
    path.write_text('0 HEAD\n1 CHAR UTF-8\n' + body + '\n0 TRLR\n', encoding='utf-8')
    return path

def test_exact_reunion_marriage_event_media_survives_import(tmp_path):
    merv=tmp_path/'Mervyn Marriage Certificate.pdf'; merv.write_bytes(b'%PDF')
    kym=tmp_path/'Kym Marriage Certificate.pdf'; kym.write_bytes(b'%PDF')
    body=(
      '0 @I1@ INDI\n1 NAME Mervyn Neil /Knuckey/\n0 @I2@ INDI\n1 NAME Elaine Fay /Cox/\n'
      '0 @I270@ INDI\n1 NAME Kym Wayne /Knuckey/\n0 @I275@ INDI\n1 NAME Susan Lee /Jones/\n'
      '0 @F1@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n1 MARR\n2 DATE 21 JAN 1961\n2 OBJE\n'
      f'3 FILE {merv}\n3 FORM application/pdf\n3 TITL Marriage Certificate\n3 _TYPE PDF\n3 _PRIM N\n'
      '0 @F184@ FAM\n1 HUSB @I270@\n1 WIFE @I275@\n1 MARR\n2 DATE 2 JUL 1988\n2 OBJE\n'
      f'3 FILE {kym}\n3 FORM application/pdf\n3 TITL Marriage Certificate\n3 _TYPE PDF\n3 _PRIM N')
    db=connect(tmp_path/'x.sqlite3'); import_gedcom(db,_ged(tmp_path/'x.ged',body))
    for xref,filename in [('@F1@',merv.name),('@F184@',kym.name)]:
        fid=db.execute('SELECT id FROM families WHERE gedcom_xref=?',(xref,)).fetchone()['id']
        rows=db.execute('SELECT m.* FROM media m JOIN family_media fm ON fm.media_id=m.id WHERE fm.family_id=?',(fid,)).fetchall()
        assert any(Path(r['file_path']).name==filename and r['attachment_scope']=='family-event' and r['attachment_label']=='Marriage' for r in rows)
        _,_,docs=family_publication_media(db,fid)
        assert any(Path(r['file_path']).name==filename for r in docs)
    db.close()

def test_preferred_person_photo_is_semantic_not_first(tmp_path):
    first=tmp_path/'Knuckey, Kym Wayne at 0.jpeg'; preferred=tmp_path/'Knuckey, Kym Wayne at 2.jpeg'
    Image.new('RGB',(400,600)).save(first); Image.new('RGB',(400,600)).save(preferred)
    body=(f'0 @I270@ INDI\n1 NAME Kym Wayne /Knuckey/\n1 OBJE\n2 FILE {first}\n2 FORM image/jpeg\n2 TITL First\n2 _TYPE PHOTO\n2 _PRIM N\n'
          f'1 OBJE\n2 FILE {preferred}\n2 FORM image/jpeg\n2 TITL Preferred\n2 _TYPE PHOTO\n2 _PRIM Y')
    db=connect(tmp_path/'x.sqlite3'); import_gedcom(db,_ged(tmp_path/'x.ged',body))
    pid=db.execute("SELECT id FROM people WHERE gedcom_xref='@I270@'").fetchone()['id']
    assert Path(_person_portrait(db,pid)['file_path']).name==preferred.name
    groups=person_document_groups(db,pid)
    assert Path(groups['portrait'][0]['file_path']).name==preferred.name
    assert [Path(x['file_path']).name for x in groups['other-photos']]==[first.name]
    db.close()

def test_two_portrait_gallery_photos_share_one_book_page_without_original_links(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); db.execute("INSERT INTO people(id,display_name) VALUES(1,'Photo Example')")
    for i in range(3):
        f=tmp_path/f'p{i}.jpg'; Image.new('RGB',(500,900)).save(f)
        mid=db.execute('INSERT INTO media(file_path,title,media_type,exists_on_disk,is_preferred) VALUES(?,?,?,?,?)',(str(f),f'Photo {i}','PHOTO',1,1 if i==0 else 0)).lastrowid
        db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,?,'GEDCOM')",(mid,))
    html=_person_section(db,1,tmp_path/'book.html')
    assert html.count('photo-page photo-pair')==1
    assert 'single-tail' not in html
    assert 'Open original image' not in html
    db.close()
