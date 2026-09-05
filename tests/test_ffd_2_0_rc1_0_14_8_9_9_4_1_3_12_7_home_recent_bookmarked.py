import sqlite3

from reunion_companion.companion.person_recents import record_recent_person, recently_explored_people


def _db():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE people(id INTEGER PRIMARY KEY,display_name TEXT,gedcom_xref TEXT);
    CREATE TABLE companion_family_files(id INTEGER PRIMARY KEY,display_name TEXT,is_active INTEGER DEFAULT 0);
    INSERT INTO companion_family_files(id,display_name,is_active) VALUES(1,'Test',1);
    INSERT INTO people VALUES(10,'Alpha Person','@I10@');
    INSERT INTO people VALUES(11,'Beta Person','@I11@');
    """)
    return db


def test_recent_people_are_distinct_and_newest_first():
    db=_db()
    record_recent_person(db,10)
    record_recent_person(db,11)
    record_recent_person(db,10)
    rows=recently_explored_people(db,6)
    assert [r["gedcom_xref"] for r in rows]==["@I10@","@I11@"]


def test_recent_people_use_stable_xref_after_people_id_replacement():
    db=_db()
    record_recent_person(db,10)
    db.execute("DELETE FROM people WHERE id=10")
    db.execute("INSERT INTO people VALUES(99,'Alpha Person','@I10@')")
    db.commit()
    rows=recently_explored_people(db,6)
    assert len(rows)==1
    assert rows[0]["id"]==99
