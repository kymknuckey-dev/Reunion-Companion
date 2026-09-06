import sqlite3

from reunion_companion.companion.beta3_quality import (
    missing_information_items,
    quick_wins,
    unsourced_information_items,
)


def make_db():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
      CREATE TABLE people(id INTEGER PRIMARY KEY,display_name TEXT);
      CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT,place_text TEXT,value_text TEXT);
      CREATE TABLE event_sources(event_id INTEGER,source_id INTEGER);
      CREATE TABLE event_media(event_id INTEGER,media_id INTEGER);
      CREATE TABLE families(id INTEGER PRIMARY KEY,marriage_date TEXT,marriage_place TEXT);
      CREATE TABLE family_members(family_id INTEGER,person_id INTEGER,role TEXT);
      CREATE TABLE family_sources(family_id INTEGER,source_id INTEGER);
      CREATE TABLE family_media(family_id INTEGER,media_id INTEGER);
      CREATE TABLE media(id INTEGER PRIMARY KEY,file_path TEXT,title TEXT,exists_on_disk INTEGER);
      CREATE TABLE sources(id INTEGER PRIMARY KEY,gedcom_xref TEXT,display_text TEXT);

      INSERT INTO people VALUES(1,'Recent Person'),(2,'Early Person'),(3,'Recent Spouse');
      INSERT INTO events VALUES
        (1,1,'Birth','1950','Adelaide',NULL),
        (2,1,'Death','2020','',NULL),
        (3,1,'Occupation','1980','Adelaide','Carpenter'),
        (4,2,'Birth','1750','Cornwall',NULL);
      INSERT INTO event_sources VALUES(1,1);
      INSERT INTO families VALUES(1,'1972','');
      INSERT INTO family_members VALUES(1,1,'Husband'),(1,3,'Wife');
      INSERT INTO media VALUES(1,'missing.jpg','Missing',0),(2,'old.pict','Old',1);
      INSERT INTO sources VALUES(1,'@S1@','Birth source'),(2,'@S2@','Same'),(3,'@S3@','Same');
    """)
    return db


def test_missing_information_includes_incomplete_marriage_and_death():
    items=missing_information_items(make_db())
    assert [(x['event_type'],x['missing_fields']) for x in items] == [
        ('Death',['place']),('Marriage',['place'])
    ]
    assert all(x['actionability']=='actionable' for x in items)


def test_unsourced_information_prioritises_recent_and_retains_early():
    items=unsourced_information_items(make_db())
    assert any(x['event_type']=='Occupation' and x['actionability']=='actionable' for x in items)
    assert any(x['event_type']=='Marriage' and x['actionability']=='actionable' for x in items)
    assert any(x['event_type']=='Birth' and x['year']==1750 and x['actionability']=='low' for x in items)


def test_quick_wins_exposes_new_summary_without_breaking_existing_checks():
    q=quick_wins(make_db())
    assert q['missing_information']==2
    assert q['missing_information_actionable']==2
    assert q['unsourced_information']==4
    assert q['unsourced_information_actionable']==3
    assert q['missing_media']==1
    assert q['legacy_pict']==1
    assert q['duplicate_source_titles']==1
