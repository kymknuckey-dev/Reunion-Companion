from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import render_discovery_workspace
from reunion_companion.companion.research_priority import relationship_priority


def add_person(db,pid,name,sex="U"):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,name.split()[0],name.split()[-1],name,sex,name),
    )
    db.commit()


def test_focus_banner_does_not_split_person_candidate_group(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Ada Mitchell","F")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a",proposed_fact_key="death:1957-06-28")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="b",proposed_fact_key="death:1950-08-26")

    html=render_discovery_workspace(db,state="new",page=1,focus_id=1,sort_mode="relationship")

    assert "Relationship anchor: Ada Mitchell" in html
    assert html.count("<h2><a href='/person/1?tab=research'>Ada Mitchell</a>")==1
    assert "2 Ryerson candidates" in html


def test_relationship_label_describes_candidate_relative_to_focus(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Mervyn Knuckey","M")
    add_person(db,2,"Peter Knuckey","M")
    db.execute("INSERT INTO families(id) VALUES(1)")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'HUSB')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,2,'CHIL')")
    db.commit()

    rel=relationship_priority(db,1,2)
    assert rel["distance"]==1
    assert rel["label"]=="son"
