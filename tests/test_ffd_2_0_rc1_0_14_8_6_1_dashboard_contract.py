from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import (
    remember_discovery,
    set_discovery_state,
)
from reunion_companion.companion.ryerson_discovery_ui import (
    render_discovery_review_section,
    render_discovery_workspace,
)


def add_person(db,pid,name):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,f"@I{pid}@",pid,name.split()[0],name.split()[-1],name,"U",name),
    )
    db.commit()


def test_dashboard_and_workspace_are_summary_only(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Peter Rigg")
    remember_discovery(
        db,
        person_id=1,
        source_name="Ryerson",
        external_record_key="notice:rigg",
        proposed_fact_key="death:2021-01-02",
    )

    dashboard=render_discovery_review_section(db)
    workspace=render_discovery_workspace(db,state="new",page=1)

    assert "Review New Discoveries" in dashboard
    assert "death:2021-01-02" not in dashboard
    assert "Accept for Reunion" not in dashboard

    assert "death:2021-01-02" not in workspace
    assert ">Accept</button>" not in workspace
    assert "1 candidate" in workspace
    assert "/person/1?tab=research" in workspace


def test_waiting_workspace_stays_summary_only(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,2,"John Mitchell")
    row=remember_discovery(
        db,
        person_id=2,
        source_name="Ryerson",
        external_record_key="notice:mitchell",
        proposed_fact_key="death:1960-01-01",
    )
    set_discovery_state(db,row["id"],"waiting_for_reunion")

    dashboard=render_discovery_review_section(db)
    workspace=render_discovery_workspace(db,state="waiting_for_reunion",page=1)

    assert "Waiting for Reunion: 1" in dashboard
    assert "Accepted. Waiting for a future GEDCOM refresh" not in workspace
    assert "1 candidate" in workspace
    assert "/person/2?tab=research" in workspace
