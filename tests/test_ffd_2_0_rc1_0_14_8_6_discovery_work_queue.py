from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
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


def test_dashboard_does_not_render_thousands_of_discoveries(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid in range(1,31):
        add_person(db,pid,f"Person{pid} Smith")
        for n in range(3):
            remember_discovery(
                db,person_id=pid,source_name="Ryerson",
                external_record_key=f"{pid}-{n}",
                proposed_fact_key=f"death:2000-01-{n+1:02d}",
            )
    html=render_discovery_review_section(db,preview_people=5)
    assert "New: 90" in html
    assert "Review New Discoveries" in html
    assert "Showing 5 of 30 people" in html


def test_workspace_groups_multiple_candidates_by_person(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Ada Mitchell")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a",proposed_fact_key="death:1957-06-28")
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="b",proposed_fact_key="death:1950-08-26")
    html=render_discovery_workspace(db,state="new",page=1)
    assert html.count("<h2><a href='/person/1?tab=research'>Ada Mitchell</a>")==1
    assert "2 Ryerson candidates" in html
    assert "death:1957-06-28" in html
    assert "death:1950-08-26" in html


def test_workspace_paginates_by_people_not_discoveries(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid in range(1,26):
        add_person(db,pid,f"Person{pid} Smith")
        remember_discovery(db,person_id=pid,source_name="Ryerson",external_record_key=str(pid))
    html=render_discovery_workspace(db,state="new",page=1,page_size=20)
    assert "Showing 20 of 25 people" in html
    assert "Page 1 of 2" in html
    assert ">Next<" in html


def test_workspace_includes_reunion_context_and_return_target(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Ada Mitchell")
    # Events schema varies between tests/builds, so use only columns known to be present.
    cols={r[1] for r in db.execute("PRAGMA table_info(events)").fetchall()}
    values={"person_id":1,"event_type":"Birth"}
    if "date_text" in cols:
        values["date_text"]="1 JAN 1900"
    elif "event_date" in cols:
        values["event_date"]="1 JAN 1900"
    if "place" in cols:
        values["place"]="Adelaide"
    keys=list(values)
    db.execute(
        f"INSERT INTO events({','.join(keys)}) VALUES({','.join('?' for _ in keys)})",
        tuple(values[k] for k in keys),
    )
    db.commit()
    remember_discovery(db,person_id=1,source_name="Ryerson",external_record_key="a",proposed_fact_key="death:1957-06-28")
    html=render_discovery_workspace(db,state="new",page=1)
    assert "Reunion record" in html
    assert "Birth:" in html
    assert "Ryerson candidates" in html
    assert "name='return'" in html
