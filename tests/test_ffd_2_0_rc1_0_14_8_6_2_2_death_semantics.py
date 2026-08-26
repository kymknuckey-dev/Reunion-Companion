from reunion_companion.companion.database import connect
from reunion_companion.companion.research_priority import death_research_semantics


def person(db,pid,name="Test Person"):
    bits=name.split()
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,bits[0],bits[-1],name,"U",name),
    )


def death(db,pid,date=None,place=None,note=None):
    return db.execute(
        "INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",
        (pid,"Death",date,place,note),
    ).lastrowid


def test_no_death_event_is_death_missing(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1)
    db.commit()
    assert death_research_semantics(db,1)=={"state":"missing","label":"Death missing"}


def test_note_only_death_is_details_incomplete_not_missing(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"Peter Stanley Rigg")
    death(db,1,note="Death notice 02 JAN 2021 late of Curramulka")
    db.commit()
    result=death_research_semantics(db,1)
    assert result["state"]=="details_incomplete"
    assert result["label"]=="Death details incomplete"


def test_structured_unsourced_death_is_needs_evidence(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"Peter Stanley Rigg")
    death(db,1,date="02 JAN 2021",place="Curramulka")
    db.commit()
    result=death_research_semantics(db,1)
    assert result["state"]=="needs_evidence"
    assert result["label"]=="Death needs evidence"
