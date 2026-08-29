from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery, set_discovery_state
from reunion_companion.companion.ryerson_discovery_ui import render_discovery_workspace


def add_person(db,pid,name):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,name.split()[0],name.split()[-1],name,"U",name),
    )
    db.commit()


def test_workspace_is_compact_person_index_without_decision_controls(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"David Mitchell")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a",proposed_fact_key="death:1993-11-30")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="b",proposed_fact_key="death:2018-12-03")

    html=render_discovery_workspace(db,state="new",page=1)

    assert "David Mitchell" in html
    assert "2 candidates" in html
    assert "/person/1?tab=research" in html
    assert "death:1993-11-30" not in html
    assert "death:2018-12-03" not in html
    assert ">Accept</button>" not in html
    assert ">Known</button>" not in html
    assert ">Not This Person</button>" not in html
    assert ">Decide Later</button>" not in html


def test_workspace_uses_styled_review_state_choices_and_hides_ineligible(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"David Mitchell")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a")

    html=render_discovery_workspace(db,state="new",page=1)

    assert "rc-review-statebar" in html
    assert "rc-review-statechoice active" in html
    assert "No Longer Eligible" not in html
    assert "← Research Priorities" not in html


def test_ineligible_state_is_retained_but_not_a_normal_navigation_choice(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"David Mitchell")
    row=remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a")
    set_discovery_state(db,row["id"],"ineligible")

    html=render_discovery_workspace(db,state="ineligible",page=1)

    assert "David Mitchell" in html
    assert "1 candidate" in html
    assert "No Longer Eligible" not in html
    assert "/person/1?tab=research" in html


def test_workspace_keeps_sorting_controls_for_person_index(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"David Mitchell")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a")

    html=render_discovery_workspace(db,state="new",page=1)

    assert "Most Recent" in html
    assert "Relationship" in html
    assert "Relationship anchor" in html
