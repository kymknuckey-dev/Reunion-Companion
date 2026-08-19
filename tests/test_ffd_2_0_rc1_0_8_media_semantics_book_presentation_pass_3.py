from pathlib import Path
from PIL import Image
from reunion_companion.companion.database import connect
from reunion_companion.companion.family_publication_model import person_document_groups
from reunion_companion.companion.publishing_v11 import _person_section

ROOT=Path(__file__).resolve().parents[1]

def test_pass3_release_identity():
    s=(ROOT/'macos_app/build_app.py').read_text()
    assert 'APP_RELEASE="FFD 2.0 RC1.0.9 — Media Semantics & Book Presentation Pass 6"' in s

def test_pass3_preferred_photo_and_two_vertical_slots_are_frozen(tmp_path):
    db=connect(tmp_path/'x.sqlite3')
    db.execute("INSERT INTO people(id,display_name) VALUES(1,'Kym Wayne Knuckey')")
    for i,name in enumerate(('at 0','at 2','at 12')):
        f=tmp_path/f'Knuckey, Kym Wayne {name}.jpeg'; Image.new('RGB',(500,900)).save(f)
        mid=db.execute('INSERT INTO media(file_path,title,media_type,exists_on_disk,is_preferred) VALUES(?,?,?,?,?)',(str(f),name,'PHOTO',1,1 if name=='at 2' else 0)).lastrowid
        db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,?,'GEDCOM')",(mid,))
    groups=person_document_groups(db,1)
    assert Path(groups['portrait'][0]['file_path']).name=='Knuckey, Kym Wayne at 2.jpeg'
    html=_person_section(db,1,tmp_path/'book.html')
    assert html.count("photo-page photo-pair")==1
    css=(ROOT/'src/reunion_companion/companion/publishing_v11.py').read_text()
    assert ".photo-page .media-card { margin:0;" in css
    assert "height:113mm;" in css
    assert "justify-self:stretch;" in css
    assert "max-height:106mm; object-fit:contain" in css
    db.close()
