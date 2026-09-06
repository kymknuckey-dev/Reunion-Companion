import sqlite3
from reunion_companion.companion.family_publication_model import person_document_groups

def db():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
    c.executescript('''
    CREATE TABLE media(id INTEGER PRIMARY KEY,gedcom_xref TEXT,file_path TEXT,title TEXT,media_type TEXT,exists_on_disk INTEGER,attachment_scope TEXT,attachment_label TEXT,is_preferred INTEGER);
    CREATE TABLE person_media(person_id INTEGER,media_id INTEGER,relation TEXT);
    CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT,place_text TEXT,value_text TEXT,note_text TEXT,gedcom_tag TEXT);
    CREATE TABLE event_media(event_id INTEGER,media_id INTEGER,relation TEXT);
    ''')
    return c

def test_burial_event_photo_is_death_burial_document_without_filename_magic():
    c=db()
    c.execute("INSERT INTO media VALUES(47,NULL,'/Media/Photos/Knuckey, Brian Victor and Patricia Ann Burial.jpg','Knuckey, Brian Victor','PHOTO',1,'event','Burial',0)")
    c.execute("INSERT INTO events VALUES(679,239,'Burial',NULL,'McLaren Vale, Uniting Church Cemetery',NULL,NULL,'BURI')")
    c.execute("INSERT INTO event_media VALUES(679,47,'GEDCOM')")
    g=person_document_groups(c,239)
    assert [m['id'] for m in g['death']]==[47]
    assert not g['other-documents'] and not g['other-photos']

def test_birth_event_photo_uses_birth_group_even_with_generic_title():
    c=db()
    c.execute("INSERT INTO media VALUES(1,NULL,'/Media/Photos/image.jpg','Scan','PHOTO',1,'event','Birth',0)")
    c.execute("INSERT INTO events VALUES(1,10,'Birth',NULL,NULL,NULL,NULL,'BIRT')")
    c.execute("INSERT INTO event_media VALUES(1,1,'GEDCOM')")
    assert [m['id'] for m in person_document_groups(c,10)['birth']]==[1]
