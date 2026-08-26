from reunion_companion.companion.database import connect
from reunion_companion.companion.research_priority import relationship_priority, death_research_semantics


def add_person(db,pid,name,sex="U"):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,name.split()[0],name.split()[-1],name,sex,name),
    )
    db.commit()


def add_family(db,fid,parent,child):
    db.execute("INSERT INTO families(id) VALUES(?)",(fid,))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",(fid,parent,"HUSB"))
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",(fid,child,"CHIL"))
    db.commit()


def test_relationship_priority_reuses_companion_engine(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Mervyn Knuckey","M")
    add_person(db,2,"Child Knuckey","M")
    add_family(db,1,1,2)
    rel=relationship_priority(db,1,2)
    assert rel["distance"]==1
    assert rel["label"] in ("son","child")


def test_unrelated_person_is_not_given_invented_relationship(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Mervyn Knuckey","M")
    add_person(db,2,"Ada Mitchell","F")
    rel=relationship_priority(db,1,2)
    assert rel["distance"] is None
    assert rel["label"]=="Relationship not established"


def test_absent_death_event_is_missing(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Peter Rigg","M")
    assert death_research_semantics(db,1)["label"]=="Death missing"
