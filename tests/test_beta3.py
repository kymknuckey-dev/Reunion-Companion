import sqlite3
from reunion_companion.companion.beta3_data_manager import ensure_companion_tables
from reunion_companion.companion.beta3_quality import quick_wins
from reunion_companion.companion.beta3_publishing import publication_history

def make_db():
    d=sqlite3.connect(":memory:");d.row_factory=sqlite3.Row
    d.executescript("""
      CREATE TABLE people(id INTEGER PRIMARY KEY,display_name TEXT);
      CREATE TABLE families(id INTEGER PRIMARY KEY);
      CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,place_text TEXT);
      CREATE TABLE notes(id INTEGER PRIMARY KEY);
      CREATE TABLE sources(id INTEGER PRIMARY KEY,gedcom_xref TEXT,display_text TEXT);
      CREATE TABLE media(id INTEGER PRIMARY KEY,file_path TEXT,title TEXT,exists_on_disk INTEGER);
      CREATE TABLE citations(id INTEGER PRIMARY KEY);
      CREATE TABLE event_sources(event_id INTEGER,source_id INTEGER);
      CREATE TABLE event_media(event_id INTEGER,media_id INTEGER);
      CREATE TABLE imports(id INTEGER PRIMARY KEY,source_path TEXT,source_type TEXT,imported_at TEXT);
      INSERT INTO people VALUES(1,'Example');
      INSERT INTO events VALUES(1,1,'Birth',NULL);
      INSERT INTO events VALUES(2,1,'Occupation','Adelaide S.A.');
      INSERT INTO media VALUES(1,'missing.jpg','Missing',0);
      INSERT INTO media VALUES(2,'legacy.pict','Legacy',1);
      INSERT INTO sources VALUES(1,'@S1@','Same');
      INSERT INTO sources VALUES(2,'@S2@','Same');
    """)
    ensure_companion_tables(d);return d

def test_companion_history_tables():
    d=make_db();names={x[0] for x in d.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"companion_import_history","companion_publication_history"} <= names

def test_quick_wins():
    q=quick_wins(make_db())
    assert q["unsourced_events"]==2 and q["missing_birth_place"]==1
    assert q["missing_media"]==1 and q["legacy_pict"]==1
    assert q["duplicate_source_titles"]==1

def test_publication_history_is_explicit_only():
    assert publication_history(make_db())==[]
