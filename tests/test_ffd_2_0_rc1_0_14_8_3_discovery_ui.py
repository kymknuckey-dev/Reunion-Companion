from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery, set_discovery_state
from reunion_companion.companion.ryerson_discovery_ui import discovery_review_groups, render_discovery_review_section


def add_person(db,pid,name):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,name.split()[0],name.split()[-1],name,"U",name),
    )
    db.commit()


def test_empty_ui_explains_no_assembled_discoveries(tmp_path):
    db=connect(tmp_path/"x.db")
    html=render_discovery_review_section(db)
    assert "External Evidence Review" in html
    assert "No person-level discoveries have been assembled yet" in html


def test_new_discovery_renders_person_and_review_actions(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Peter Rigg")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="notice:rigg",proposed_fact_key="death:2021-01-02")
    html=render_discovery_review_section(db)
    assert "Peter Rigg" in html
    assert "death:2021-01-02" in html
    assert "Accept for Reunion" in html
    assert "Already Known" in html
    assert "Not This Person" in html
    assert "Decide Later" in html


def test_waiting_discovery_has_no_repeat_review_buttons(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,2,"John Mitchell")
    row=remember_discovery(db,person_id=2,source_name="Ryerson",external_record_key="notice:mitchell",proposed_fact_key="death:1960-01-01")
    set_discovery_state(db,row["id"],"waiting_for_reunion")
    html=render_discovery_review_section(db)
    assert "Waiting for Reunion" in html
    assert "Accepted. Waiting for a future GEDCOM refresh" in html


def test_groups_keep_states_separate(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,3,"Mary Dunstan")
    a=remember_discovery(db,person_id=3,source_name="Ryerson",external_record_key="a")
    b=remember_discovery(db,person_id=3,source_name="Ryerson",external_record_key="b")
    set_discovery_state(db,b["id"],"rejected")
    groups=discovery_review_groups(db)
    assert len(groups["new"])==1
    assert len(groups["rejected"])==1
