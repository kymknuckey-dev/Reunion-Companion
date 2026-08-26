from reunion_companion.companion.database import connect
from reunion_companion.companion.beta_ui import person_page, research_page
from reunion_companion.companion.external_evidence_matcher import (
    death_research_state,
    missing_death_candidates,
)

def person(db,pid,xref,name,surname):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,name,surname,f"{name} {surname}","M",f"{name} /{surname}/"),
    )

def event(db,pid,kind,date=None,place=None,note=None):
    return db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",
        (pid,kind,date,place,note),
    ).lastrowid

def test_no_death_event_is_missing(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Missing","Person")
    db.commit()
    assert death_research_state(db,1)["state"]=="missing"

def test_note_only_death_is_incomplete(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanley","Rigg")
    event(db,1,"Birth","21 MAY 1944","Brighton Community Hospital")
    event(db,1,"Death",None,None,"Death notice 02 JAN 2021 late of Curramulka")
    db.commit()
    state=death_research_state(db,1)
    assert state["state"]=="incomplete"
    assert "Death date not recorded" in state["reasons"]
    assert "Death place not recorded" in state["reasons"]
    assert "No linked death evidence" in state["reasons"]
    rows=missing_death_candidates(db)
    assert rows[0]["death_state"]=="incomplete"
    assert "Curramulka" in rows[0]["death_note_text"]

def test_structured_death_with_linked_source_is_recorded(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Complete","Person")
    eid=event(db,1,"Death","02 JAN 2021","Curramulka")
    db.execute("INSERT INTO sources(id,gedcom_xref,title) VALUES(1,'@S1@','Death notice')")
    db.execute("INSERT INTO event_sources(event_id,source_id,relation) VALUES(?,1,'GEDCOM')",(eid,))
    db.commit()
    assert death_research_state(db,1)["state"]=="recorded"
    assert missing_death_candidates(db)==[]

def test_person_research_shows_incomplete_state_and_note(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Peter Stanley","Rigg")
    event(db,1,"Death",None,None,"Death notice 02 JAN 2021 late of Curramulka")
    db.commit()
    html=person_page(db,1,"research",presentation_override=False)
    assert "Incomplete death information" in html
    assert "Death date not recorded" in html
    assert "Death place not recorded" in html
    assert "Existing event note:" in html
    assert "Curramulka" in html
    assert "Missing death information" not in html

def test_priorities_distinguish_missing_and_incomplete(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"@I1@","Missing","Person")
    person(db,2,"@I2@","Peter Stanley","Rigg")
    event(db,2,"Death",None,None,"Death notice information in note")
    db.commit()
    html=research_page(db)
    assert "Research Needed" in html
    assert "Missing Person" in html
    assert "Death missing" in html
    assert "Peter Stanley Rigg" in html
    assert "Death details incomplete" in html
    assert "Existing Death event note available" in html
