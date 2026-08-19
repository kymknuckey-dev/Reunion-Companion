from pathlib import Path

from reunion_companion.companion.database import connect
from reunion_companion.companion.gedcom import import_gedcom
from reunion_companion.companion.family_publication_model import person_media, family_publication_media
from reunion_companion.companion.ffd_person_story import _person_portrait
from reunion_companion.companion.publishing_v11 import _person_section


def _ged(path, body):
    path.write_text('0 HEAD\n1 CHAR UTF-8\n' + body + '\n0 TRLR\n', encoding='utf-8')
    return path


def test_reunion_marriage_event_media_is_imported_as_family_marriage_media(tmp_path):
    cert=tmp_path/'Marriage Certificate.pdf'; cert.write_bytes(b'%PDF')
    g=_ged(tmp_path/'x.ged', f'''0 @I1@ INDI
1 NAME Husband /Example/
0 @I2@ INDI
1 NAME Wife /Example/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 21 JAN 1961
2 OBJE
3 FILE {cert}
3 FORM application/pdf
3 TITL Marriage Certificate
3 _TYPE PDF
3 _PRIM N''')
    db=connect(tmp_path/'x.sqlite3')
    import_gedcom(db,g)
    fam=db.execute("SELECT id FROM families WHERE gedcom_xref='@F1@'").fetchone()['id']
    rows=db.execute("SELECT m.* FROM media m JOIN family_media fm ON fm.media_id=m.id WHERE fm.family_id=?",(fam,)).fetchall()
    assert len(rows)==1
    assert rows[0]['attachment_scope']=='family-event'
    assert rows[0]['attachment_label']=='Marriage'
    _,_,docs=family_publication_media(db,fam)
    assert [Path(m['file_path']).name for m in docs]==['Marriage Certificate.pdf']
    db.close()


def test_reunion_prim_y_is_preserved_and_preferred_for_person_photo(tmp_path):
    first=tmp_path/'first.jpg'; first.write_bytes(b'jpg')
    preferred=tmp_path/'preferred.jpg'; preferred.write_bytes(b'jpg')
    g=_ged(tmp_path/'x.ged', f'''0 @I1@ INDI
1 NAME Photo /Example/
1 OBJE
2 FILE {first}
2 FORM image/jpeg
2 TITL First Photo
2 _PRIM N
1 OBJE
2 FILE {preferred}
2 FORM image/jpeg
2 TITL Preferred Photo
2 _PRIM Y''')
    db=connect(tmp_path/'x.sqlite3')
    import_gedcom(db,g)
    pid=db.execute("SELECT id FROM people WHERE gedcom_xref='@I1@'").fetchone()['id']
    items=person_media(db,pid)
    assert items[0]['title']=='Preferred Photo'
    assert items[0]['is_preferred']==1
    portrait=_person_portrait(db,pid)
    assert portrait['title']=='Preferred Photo'
    db.close()


def test_book_other_photos_use_two_vertical_slots_per_page(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    db.execute("INSERT INTO people(id,display_name) VALUES(1,'Photo Example')")
    # first image is portrait/hero; next three are Other Photographs.
    for i in range(4):
        f=tmp_path/f'p{i}.jpg'
        from PIL import Image
        Image.new('RGB',(400,700 if i%2==0 else 300)).save(f)
        mid=db.execute("INSERT INTO media(file_path,title,media_type,exists_on_disk,is_preferred) VALUES(?,?,?,?,?)",(str(f),f'Photo {i}','PHOTO',1,1 if i==0 else 0)).lastrowid
        db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,?,'GEDCOM')",(mid,))
    html=_person_section(db,1,tmp_path/'book.html')
    assert "photo-page photo-pair" in html
    assert html.count("photo-page photo-pair")==2
    assert "landscape-pair" not in html
    assert "single-photo" not in html
    db.close()
