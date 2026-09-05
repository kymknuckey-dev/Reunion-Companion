from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import discovery_review_rows,_group_people,sort_grouped_people_recent,render_discovery_review_section


def add_person(db,pid,name):
    bits=name.split()
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid," ".join(bits[:-1]),bits[-1],name,"U",name))
    db.commit()


def discovery(db,pid,key):
    remember_discovery(db,person_id=pid,source_name="Ryerson",external_record_key=f"x{pid}-{key}",proposed_fact_key=key)


def test_recent_sort_uses_actual_candidate_event_date(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Older Person"); add_person(db,2,"Recent Person"); add_person(db,3,"Undated Person")
    discovery(db,1,"death:01JAN1950"); discovery(db,2,"death:01JAN2025"); discovery(db,3,"")
    ordered=sort_grouped_people_recent(_group_people(discovery_review_rows(db,state="new")))
    assert [pid for pid,_ in ordered]==[2,1,3]


def test_dashboard_defaults_to_recent_and_shows_twelve(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid in range(1,14):
        add_person(db,pid,f"Person {pid}"); discovery(db,pid,f"death:01JAN{2000+pid}")
    html=render_discovery_review_section(db)
    assert "Grouped by match quality" in html
    assert "Most Recent" in html
    assert "Relationship" in html
    assert "Page 1 of 2 · 13 people in Unassessed" in html


def test_relationship_mode_exposes_anchor_picker(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Mervyn Neil Knuckey"); add_person(db,2,"Other Person"); discovery(db,2,"death:01JAN2025")
    html=render_discovery_review_section(db,sort_mode="relationship",focus_id=1)
    assert "Relationship anchor" in html
    assert "Mervyn Neil Knuckey" in html
    assert "Calculating relationships" in html
