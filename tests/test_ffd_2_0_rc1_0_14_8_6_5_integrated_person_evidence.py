from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery, set_discovery_state
from reunion_companion.companion.ryerson_discovery_ui import render_person_discovery_decisions, render_discovery_review_section


def person(db,pid,name):
    bits=name.split()
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid," ".join(bits[:-1]),bits[-1],name,"U",name),
    )
    db.commit()


def test_person_workspace_renders_actions_for_new_candidate(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"Graham Shearer")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="g1",proposed_fact_key="death:2020-01-01")
    html=render_person_discovery_decisions(db,1)
    assert ">Accept</button>" in html
    assert ">Known</button>" in html
    assert "Not This Person" in html
    assert "Decide Later" in html
    assert "/person/1?tab=research" in html


def test_person_workspace_preserves_existing_decisions(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"Graham Shearer")
    a=remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a")
    b=remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="b")
    c=remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="c")
    set_discovery_state(db,a["id"],"rejected")
    set_discovery_state(db,b["id"],"waiting_for_reunion")
    set_discovery_state(db,c["id"],"already_known")
    html=render_person_discovery_decisions(db,1)
    assert "Not This Person" in html
    assert "Waiting for Reunion" in html
    assert "Already Known" in html
    assert "Accept for Reunion" not in html


def test_dashboard_person_link_goes_direct_to_research_workspace(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db,1,"Peter Rigg")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="p1",proposed_fact_key="death:2021-01-02")
    html=render_discovery_review_section(db,preview_people=5,focus_id=1)
    assert "href='/person/1?tab=research'" in html
