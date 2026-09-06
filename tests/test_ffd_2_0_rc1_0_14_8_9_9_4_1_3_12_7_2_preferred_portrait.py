
import sqlite3
from reunion_companion.companion.ffd_person_story import _person_portrait
from reunion_companion.companion.family_publication_model import person_document_groups

def make_db():
    d=sqlite3.connect(":memory:"); d.row_factory=sqlite3.Row
    d.executescript("""
    CREATE TABLE media(id INTEGER PRIMARY KEY,gedcom_xref TEXT,file_path TEXT NOT NULL,title TEXT,media_type TEXT,exists_on_disk INTEGER NOT NULL DEFAULT 0,attachment_scope TEXT,attachment_label TEXT,is_preferred INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE person_media(person_id INTEGER,media_id INTEGER,relation TEXT);
    CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT);
    CREATE TABLE event_media(event_id INTEGER,media_id INTEGER,relation TEXT);
    """)
    return d

def add(d,mid,path,pref):
    d.execute("INSERT INTO media(id,file_path,title,media_type,exists_on_disk,attachment_scope,is_preferred) VALUES(?,?,?,?,?,?,?)",(mid,str(path),path.name,"PHOTO",1,"person",pref))
    d.execute("INSERT INTO person_media VALUES(262,?,'GEDCOM')",(mid,))

def test_john_thomas_nonpreferred_building_photos_are_not_portrait(tmp_path):
    d=make_db()
    a=tmp_path/"Build 1.jpg"; b=tmp_path/"Build 2.jpg"; a.touch(); b.touch()
    add(d,60,a,0); add(d,61,b,0)
    assert _person_portrait(d,262) is None
    g=person_document_groups(d,262)
    assert g["portrait"]==[]
    assert {m["id"] for m in g["other-photos"]}=={60,61}

def test_preferred_direct_person_photo_still_wins(tmp_path):
    d=make_db()
    a=tmp_path/"portrait.jpg"; a.touch()
    add(d,70,a,1)
    assert _person_portrait(d,262)["id"]==70
    assert person_document_groups(d,262)["portrait"][0]["id"]==70
