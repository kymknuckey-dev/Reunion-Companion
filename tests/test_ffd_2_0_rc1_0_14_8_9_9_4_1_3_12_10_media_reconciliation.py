from pathlib import Path
import sqlite3

from reunion_companion.companion.media_reconciliation import infer_media_root,reconcile_media
from reunion_companion.companion.beta_ui import media_reconciliation_page


def _db(tmp_path):
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


def test_media_reconciliation_compares_recursive_media_tree_with_gedcom_refs(tmp_path,monkeypatch):
    media_root=tmp_path/'Reunion Files'/'Media'; photos=media_root/'Photos'; docs=media_root/'Documents'; photos.mkdir(parents=True);docs.mkdir()
    referenced=photos/'Brian.jpg'; referenced.write_bytes(b'photo')
    orphan=docs/'Unattached scan.pdf'; orphan.write_bytes(b'%PDF-test')
    missing=docs/'Missing.pdf'
    db=_db(tmp_path)
    db.execute("INSERT INTO people VALUES(1,'Brian Victor Knuckey')")
    db.execute("INSERT INTO events VALUES(10,1,'Burial')")
    db.execute("INSERT INTO media VALUES(1,'Brian Burial',?,'PHOTO',1,'event','Burial',0)",(str(referenced),))
    db.execute("INSERT INTO media VALUES(2,'Missing doc',?,'PDF',0,'event','Birth',0)",(str(missing),))
    db.execute("INSERT INTO event_media VALUES(10,1,'GEDCOM')")
    monkeypatch.setattr('reunion_companion.companion.media_reconciliation.configured_media_root',lambda db:None)
    assert infer_media_root(db)==str(media_root)
    data=reconcile_media(db)
    assert data['counts']['referenced_found']==1
    assert data['counts']['referenced_missing']==1
    assert data['counts']['unreferenced']==1
    assert data['unreferenced'][0]['relative_path']=='Documents/Unattached scan.pdf'
    assert data['referenced_found'][0]['contexts'][0]['event_type']=='Burial'


def test_media_reconciliation_page_is_read_only_and_offers_native_folder_picker(tmp_path,monkeypatch):
    db=_db(tmp_path)
    monkeypatch.setattr('reunion_companion.companion.beta_ui.reconcile_media',lambda db:{'root':str(tmp_path),'root_exists':True,'counts':{'referenced':0,'referenced_found':0,'referenced_missing':0,'physical':0,'unreferenced':0,'cloud_placeholders':0},'referenced_found':[],'referenced_missing':[],'unreferenced':[],'cloud_placeholders':[]})
    html=media_reconciliation_page(db,{})
    assert 'Media Reconciliation' in html
    assert 'reunion-companion://choose-media-root' in html
    assert 'Nothing on this page changes, moves, renames or deletes your files.' in html
    assert 'Not referenced' in html
