from pathlib import Path
import sqlite3

from reunion_companion.companion.media_reconciliation import reconcile_media
from reunion_companion.companion.beta_ui import media_reconciliation_page


def _db():
    db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
    db.executescript('''
    CREATE TABLE media(id INTEGER PRIMARY KEY,title TEXT,file_path TEXT,media_type TEXT,exists_on_disk INTEGER,attachment_scope TEXT,attachment_label TEXT,is_preferred INTEGER);
    CREATE TABLE people(id INTEGER PRIMARY KEY,display_name TEXT);
    CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT);
    CREATE TABLE person_media(person_id INTEGER,media_id INTEGER,relation TEXT);
    CREATE TABLE event_media(event_id INTEGER,media_id INTEGER,relation TEXT);
    CREATE TABLE family_media(family_id INTEGER,media_id INTEGER,relation TEXT);
    CREATE TABLE family_members(family_id INTEGER,person_id INTEGER);
    ''')
    return db


def test_lyell_duncan_case_only_path_difference_is_referenced_and_found(tmp_path,monkeypatch):
    root=tmp_path/'Reunion Files'/'Media'; docs=root/'Documents'; docs.mkdir(parents=True)
    physical=docs/'Duncan, Lyell Leonard Doc2065260.jpg'; physical.write_bytes(b'photo')
    gedcom_path=docs/'Duncan, Lyell Leonard doc2065260.JPG'
    db=_db()
    db.execute("INSERT INTO people VALUES(335,'Lyell Leonard Knuckey')")
    db.execute("INSERT INTO media VALUES(135,'Duncan, Lyell Leonard doc2065260',?,'PHOTO',1,'person',NULL,0)",(str(gedcom_path),))
    db.execute("INSERT INTO person_media VALUES(335,135,'GEDCOM')")
    monkeypatch.setattr('reunion_companion.companion.media_reconciliation.configured_media_root',lambda db:str(root))
    data=reconcile_media(db)
    assert data['counts']['referenced_found']==1
    assert data['counts']['referenced_missing']==0
    assert data['counts']['unreferenced']==0
    assert data['referenced_found'][0]['name']=='Duncan, Lyell Leonard Doc2065260.jpg'


def test_media_status_labels_separate_quality_from_icloud_availability(tmp_path,monkeypatch):
    db=_db()
    monkeypatch.setattr('reunion_companion.companion.beta_ui.reconcile_media',lambda db:{'root':str(tmp_path),'root_exists':True,'counts':{'referenced':1,'referenced_found':1,'referenced_missing':0,'physical':1,'unreferenced':0,'cloud_placeholders':0},'referenced_found':[],'referenced_missing':[],'unreferenced':[],'cloud_placeholders':[]})
    html=media_reconciliation_page(db,{})
    assert 'Not referenced · review' in html
    assert 'Referenced but missing · review' in html
    assert 'Referenced &amp; found · healthy' in html
    assert 'iCloud availability' in html
