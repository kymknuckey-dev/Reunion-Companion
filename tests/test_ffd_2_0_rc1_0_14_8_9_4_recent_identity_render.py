import sqlite3

from reunion_companion.companion.beta_ui import _research_needed_row_html


def _db():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE people(id INTEGER PRIMARY KEY, display_name TEXT);
    CREATE TABLE events(id INTEGER PRIMARY KEY, person_id INTEGER, event_type TEXT, date_value TEXT, place TEXT);
    CREATE TABLE families(id INTEGER PRIMARY KEY, husband_id INTEGER, wife_id INTEGER);
    CREATE TABLE family_members(family_id INTEGER, person_id INTEGER);
    """)
    return db


def test_recent_row_renders_birth_and_parent_identity_context(monkeypatch):
    db=_db()
    db.executemany("INSERT INTO people(id,display_name) VALUES (?,?)",[(1,"Ada Smith"),(2,"John Smith"),(3,"Mary Brown")])
    db.execute("INSERT INTO events(person_id,event_type,date_value,place) VALUES (1,'Birth','1884','Adelaide, South Australia')")
    db.execute("INSERT INTO families(id,husband_id,wife_id) VALUES (10,2,3)")
    db.executemany("INSERT INTO family_members(family_id,person_id) VALUES (10,?)",[(1,),(2,),(3,)])

    # beta_ui imports family_partners; make this test independent of its schema implementation.
    import reunion_companion.companion.beta_ui as ui
    monkeypatch.setattr(ui,"family_partners",lambda _db,_fid:(
        _db.execute("SELECT id,display_name FROM people WHERE id=2").fetchone(),
        _db.execute("SELECT id,display_name FROM people WHERE id=3").fetchone(),
    ))

    row={"person_id":1,"display_name":"Ada Smith","death_state":"missing","death_note_text":""}
    html=_research_needed_row_html(db,row,{"label":"Missing Death"},"recent",{})
    assert "Ada Smith" in html
    assert "Born 1884" in html
    assert "Adelaide, South Australia" in html
    assert "Child of John Smith and Mary Brown" in html
    assert "Relationship not established" not in html


def test_relationship_row_keeps_relationship_label():
    db=_db()
    row={"person_id":1,"display_name":"Ada Smith","death_state":"missing","death_note_text":""}
    html=_research_needed_row_html(
        db,row,{"label":"Missing Death"},"relationship",
        {1:{"label":"3rd cousin"}},
    )
    assert "3rd cousin" in html
    assert "No additional identity details recorded" not in html
