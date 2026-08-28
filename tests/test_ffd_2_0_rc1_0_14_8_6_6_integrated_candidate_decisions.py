from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_assembly import (
    assemble_candidate,
    candidate_is_reviewable,
    impossible_death_before_birth,
)
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import render_finding_decision_controls


def add_person(db,pid,name="Test Person"):
    bits=name.split()
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid," ".join(bits[:-1]),bits[-1],name,"U",name),
    )
    db.commit()


def test_definite_death_before_birth_is_filtered():
    row={"person_id":1,"birth_date":"21 MAY 1944","death_date":"02 JAN 1940"}
    assert impossible_death_before_birth(row)
    assert not candidate_is_reviewable(row)
    assert assemble_candidate(row) is None


def test_death_after_birth_remains_reviewable():
    row={"person_id":1,"birth_date":"21 MAY 1944","death_date":"02 JAN 2021"}
    assert not impossible_death_before_birth(row)
    assert candidate_is_reviewable(row)


def test_approximate_birth_does_not_auto_reject():
    row={"person_id":1,"birth_date":"ABT 1944","death_date":"02 JAN 1940"}
    assert not impossible_death_before_birth(row)
    assert candidate_is_reviewable(row)


def test_year_only_birth_does_not_auto_reject():
    row={"person_id":1,"birth_date":"1944","death_date":"02 JAN 1940"}
    assert not impossible_death_before_birth(row)
    assert candidate_is_reviewable(row)


def test_finding_gets_decision_controls_beside_details(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Graham Shearer")
    remember_discovery(
        db,person_id=1,source_name="Ryerson",
        external_record_key="g1",proposed_fact_key="death:02 JAN 2021",
    )
    finding={"event_date":"02 JAN 2021","source_name":"Ryerson"}
    html=render_finding_decision_controls(db,1,finding)
    assert ">Accept</button>" in html
    assert ">Known</button>" in html
    assert "Not This Person" in html
    assert "Decide Later" in html
    assert "/person/1?tab=research" in html
