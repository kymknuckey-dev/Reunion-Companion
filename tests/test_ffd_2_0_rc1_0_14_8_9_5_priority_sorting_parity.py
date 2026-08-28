import sqlite3
from reunion_companion.companion.beta_ui import _priority_recent_event_keys, _priority_sort_choice_html

def test_recent_event_keys_use_most_recent_event():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("CREATE TABLE events(id INTEGER PRIMARY KEY,person_id INTEGER,event_type TEXT,date_text TEXT);")
    db.executemany(
        "INSERT INTO events(person_id,event_type,date_text) VALUES (?,?,?)",
        [(1,"Birth","1823"),(1,"Marriage","12 JUN 1850"),(2,"Birth","ABT 1940"),(2,"Residence","2005")],
    )
    keys=_priority_recent_event_keys(db,[1,2])
    assert keys[1] == (1850,6,12)
    assert keys[2] == (2005,0,0)
    assert keys[2] > keys[1]

def test_priority_sort_control_offers_recent_and_relationship():
    html=_priority_sort_choice_html("recent",{"id":42,"display_name":"Anchor"},"data-quality")
    assert "Most Recent" in html
    assert "Relationship" in html
    assert "/research?sort=relationship&focus=42" in html
    assert "data-quality" in html
