import sqlite3
from types import SimpleNamespace
from reunion_companion.companion.ffd_person_story import _unactioned_external_evidence_count, person_identity_header

def db_fixture():
    db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
    db.executescript('''
      CREATE TABLE imports(id INTEGER PRIMARY KEY,source_path TEXT);
      INSERT INTO imports VALUES(1,'/tmp/test.ged');
      CREATE TABLE people(id INTEGER PRIMARY KEY,display_name TEXT,sex TEXT,gedcom_xref TEXT);
      CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT,place_text TEXT,value_text TEXT,note_text TEXT,gedcom_tag TEXT);
      CREATE TABLE family_members(family_id INTEGER,person_id INTEGER,role TEXT);
      CREATE TABLE media(id INTEGER PRIMARY KEY,is_preferred INTEGER,exists_on_disk INTEGER,file_path TEXT);
      CREATE TABLE person_media(person_id INTEGER,media_id INTEGER);
      CREATE TABLE companion_person_bookmarks(workspace_id INTEGER NOT NULL, person_gedcom_xref TEXT NOT NULL, created_at TEXT, PRIMARY KEY(workspace_id,person_gedcom_xref));
      CREATE TABLE companion_external_discovery_review(id INTEGER PRIMARY KEY,person_id INTEGER,source_name TEXT,external_record_key TEXT,proposed_fact_key TEXT,match_confidence INTEGER,state TEXT,decision_note TEXT,first_seen_at TEXT,reviewed_at TEXT,confirmed_at TEXT,updated_at TEXT);
    ''')
    db.execute("INSERT INTO people VALUES(1,'Cornish, Patricia Ann','F','@I1@')")
    db.execute("INSERT INTO companion_external_discovery_review VALUES(1,1,'Ryerson','r1','death',60,'new','','','','','')")
    db.execute("INSERT INTO companion_external_discovery_review VALUES(2,1,'Ryerson','r2','death',90,'deferred','','','','','')")
    return db

def test_counts_only_new_unactioned_candidates():
    assert _unactioned_external_evidence_count(db_fixture(),1)==1

def test_research_header_surfaces_candidate_and_person_filtered_link_without_death_event():
    db=db_fixture(); w={'person':dict(db.execute('SELECT * FROM people WHERE id=1').fetchone())}
    html=person_identity_header(db,w,presentation=False)
    assert 'External evidence' in html and '1 candidate to review' in html
    assert '/research/discoveries?state=new&person=1' in html

def test_presentation_header_does_not_surface_research_candidate():
    db=db_fixture(); w={'person':dict(db.execute('SELECT * FROM people WHERE id=1').fetchone())}
    html=person_identity_header(db,w,presentation=True)
    assert 'External evidence' not in html and '/research/discoveries' not in html
