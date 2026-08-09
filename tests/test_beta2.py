import sqlite3
from reunion_companion.companion.beta2_research import normalize_place_text,person_timeline_model,person_anomalies

def db():
    d=sqlite3.connect(":memory:");d.row_factory=sqlite3.Row
    d.executescript("""
      CREATE TABLE people(id INTEGER PRIMARY KEY,gedcom_xref TEXT,display_name TEXT,sex TEXT);
      CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT,place_text TEXT,value_text TEXT,note_text TEXT);
      CREATE TABLE event_sources(event_id INTEGER,source_id INTEGER);
      CREATE TABLE event_media(event_id INTEGER,media_id INTEGER);
      CREATE TABLE notes(id INTEGER PRIMARY KEY,person_id INTEGER,text TEXT,note_text TEXT);
      CREATE TABLE sources(id INTEGER PRIMARY KEY,gedcom_xref TEXT,title TEXT,text TEXT,display_text TEXT);
      CREATE TABLE person_sources(person_id INTEGER,source_id INTEGER);
      CREATE TABLE note_sources(note_id INTEGER,source_id INTEGER);
      CREATE TABLE family_sources(family_id INTEGER,source_id INTEGER);
      CREATE TABLE family_members(family_id INTEGER,person_id INTEGER,role TEXT);
      CREATE TABLE media(id INTEGER PRIMARY KEY,title TEXT,file_path TEXT,exists_on_disk INTEGER);
      CREATE TABLE person_media(person_id INTEGER,media_id INTEGER);
      INSERT INTO people VALUES(1,'@I1@','Example Person','M');
      INSERT INTO events VALUES(1,1,'Birth','1900','Adelaide S.A.','',NULL);
      INSERT INTO events VALUES(2,1,'Occupation','1890',NULL,'Carpenter',NULL);
      INSERT INTO event_sources VALUES(1,7);
      INSERT INTO notes VALUES(1,1,'Some doubt exists about this record.',NULL);
    """)
    return d

def test_place_normalizer():
    assert normalize_place_text("Adelaide S.A.")=="Adelaide South Australia"

def test_timeline_sorted_and_evidence():
    t=person_timeline_model(db(),1)
    assert [x["type"] for x in t["events"]]==["Occupation","Birth"]
    assert t["events"][1]["evidence_status"]=="supported"

def test_anomalies_detect_chronology_and_uncertainty():
    msgs=[x["message"] for x in person_anomalies(db(),1)]
    assert any("before recorded birth" in x for x in msgs)
    assert any("uncertainty language" in x for x in msgs)
