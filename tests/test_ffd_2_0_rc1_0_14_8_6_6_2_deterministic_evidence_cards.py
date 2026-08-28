from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import add_external_evidence, external_evidence_for_person
from reunion_companion.companion.ryerson_person_finding_bridge import materialize_person_level_ryerson_findings
from reunion_companion.companion.ryerson_discovery_review import set_discovery_state
from reunion_companion.companion.ryerson_discovery_ui import review_row_for_finding, render_external_evidence_candidate, sort_external_findings_recent_first


def add_person(db,pid,name="Ellen Clark",xref="@I1@"):
    bits=name.split()
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,xref,pid," ".join(bits[:-1]),bits[-1],name,"F",name))
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",(pid,"Birth","1 JAN 1930",None,None))
    db.commit()


def add_finding(db,xref,event_date,pubdate):
    return add_external_evidence(db,person_gedcom_xref=xref,person_name_snapshot="Ellen Clark",source_name="Ryerson",evidence_type="Death notice",source_record_name="Ellen CLARK",event_type="Death",event_date=event_date,publication="Sydney Morning Herald",publication_date=pubdate,details="candidate",match_confidence=75,match_reason="surname exact; full name exact")


def test_bridge_identity_maps_finding_directly_to_review_row(tmp_path):
    db=connect(tmp_path/"x.db"); add_person(db,1)
    eid=add_finding(db,"@I1@","28JUL1954","30JUL1954")
    materialize_person_level_ryerson_findings(db)
    finding=[f for f in external_evidence_for_person(db,"@I1@") if f["id"]==eid][0]
    row=review_row_for_finding(db,1,finding)
    assert row is not None
    assert row["external_record_key"]==f"ryerson:{eid}"


def test_every_actionable_finding_has_all_buttons(tmp_path):
    db=connect(tmp_path/"x.db"); add_person(db,1)
    add_finding(db,"@I1@","28JUL1954","30JUL1954")
    add_finding(db,"@I1@","29JUL1954","31JUL1954")
    materialize_person_level_ryerson_findings(db)
    for finding in external_evidence_for_person(db,"@I1@"):
        html=render_external_evidence_candidate(db,1,finding)
        assert ">Accept</button>" in html
        assert ">Known</button>" in html
        assert "Not This Person" in html
        assert "Decide Later" in html


def test_existing_decision_is_preserved(tmp_path):
    db=connect(tmp_path/"x.db"); add_person(db,1)
    add_finding(db,"@I1@","28JUL1954","30JUL1954")
    materialize_person_level_ryerson_findings(db)
    finding=external_evidence_for_person(db,"@I1@")[0]
    row=review_row_for_finding(db,1,finding)
    set_discovery_state(db,row["id"],"already_known")
    html=render_external_evidence_candidate(db,1,finding)
    assert "Already Known" in html
    assert ">Accept</button>" not in html


def test_recent_event_date_orders_first(tmp_path):
    db=connect(tmp_path/"x.db"); add_person(db,1)
    add_finding(db,"@I1@","01JAN1930","02JAN1930")
    add_finding(db,"@I1@","01JAN2000","02JAN2000")
    rows=sort_external_findings_recent_first(external_evidence_for_person(db,"@I1@"))
    assert rows[0]["event_date"]=="01JAN2000"
