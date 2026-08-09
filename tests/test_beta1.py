import sqlite3
from reunion_companion.companion.beta_ui_service import search_people,person_confidence
from reunion_companion.companion.beta_ui import layout

def db():
    d=sqlite3.connect(":memory:");d.row_factory=sqlite3.Row
    d.executescript("""
      CREATE TABLE people(id INTEGER PRIMARY KEY,gedcom_xref TEXT,display_name TEXT,sex TEXT);
      CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT,place_text TEXT,value_text TEXT);
      CREATE TABLE event_sources(event_id INTEGER,source_id INTEGER);
      CREATE TABLE event_media(event_id INTEGER,media_id INTEGER);
      CREATE TABLE sources(id INTEGER PRIMARY KEY,gedcom_xref TEXT,title TEXT,text TEXT,display_text TEXT);
      CREATE TABLE person_sources(person_id INTEGER,source_id INTEGER);
      CREATE TABLE notes(id INTEGER PRIMARY KEY,person_id INTEGER,note_type_name TEXT,gedcom_tag TEXT,text TEXT);
      CREATE TABLE note_sources(note_id INTEGER,source_id INTEGER);
      CREATE TABLE media(id INTEGER PRIMARY KEY,title TEXT,file_path TEXT);
      CREATE TABLE person_media(person_id INTEGER,media_id INTEGER);
      CREATE TABLE family_sources(family_id INTEGER,source_id INTEGER);
      CREATE TABLE family_members(family_id INTEGER,person_id INTEGER,role TEXT);
      INSERT INTO people VALUES(1,'@I1@','Mervyn Neil Knuckey','M');
      INSERT INTO people VALUES(2,'@I2@','Elaine Fay Cox','F');
      INSERT INTO events VALUES(1,1,'Birth','24 SEP 1933','Unley','');
      INSERT INTO events VALUES(2,1,'Occupation',NULL,NULL,'Public Servant');
      INSERT INTO event_sources VALUES(1,7);
      INSERT INTO sources VALUES(7,'@S7@','Birth Certificate','Birth Certificate.','Birth Certificate.');
    """)
    return d

def test_beta_search_people():
    r=search_people(db(),"Mervyn")
    assert len(r)==1 and r[0]["display_name"]=="Mervyn Neil Knuckey"

def test_beta_confidence_is_evidence_coverage():
    r=person_confidence(db(),1)
    assert r["summary"]["event_count"]==2
    assert r["summary"]["supported_events"]==1
    assert r["summary"]["support_percent"]==50
    assert {x["status"] for x in r["events"]}=={"supported","unsourced"}

def test_beta_layout_branding():
    x=layout("Test","<p>Hello</p>")
    assert "Reunion Companion" in x and "Beta " in x
    assert "Research" in x and "Publishing" in x
