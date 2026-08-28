from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import add_external_evidence, external_evidence_for_person
from reunion_companion.companion.ryerson_person_finding_bridge import materialize_person_level_ryerson_findings
from reunion_companion.companion.ryerson_discovery_ui import render_external_evidence_candidate

def person(db):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Ellen','Clark','Ellen Clark','F','Ellen Clark')")
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",(1,"Birth","1 JAN 1930",None,None))
    db.commit()

def test_candidate_card_matches_review_presentation_contract(tmp_path):
    db=connect(tmp_path/"x.db")
    person(db)
    add_external_evidence(
        db,
        person_gedcom_xref="@I1@",
        person_name_snapshot="Ellen Clark",
        source_name="Ryerson",
        evidence_type="death_notice",
        source_record_name="Ellen CLARK",
        event_type="Death",
        event_date="28JUL1954",
        publication="Sydney Morning Herald",
        publication_date="30JUL1954",
        details="at Katoomba",
        place_claim="Katoomba, New South Wales",
        match_confidence=75,
        match_reason="surname exact; full name exact",
    )
    materialize_person_level_ryerson_findings(db)
    finding=external_evidence_for_person(db,"@I1@")[0]
    html=render_external_evidence_candidate(db,1,finding)
    assert "Ryerson · Match 75%" in html
    assert "Death 28JUL1954 · Sydney Morning Herald · published 30JUL1954" in html
    assert "at Katoomba" in html
    assert "Katoomba, New South Wales" in html
    assert "Event type:" in html
    assert "Chronology OK" in html
    assert ">Accept</button>" in html
    assert ">Known</button>" in html
    assert ">Not This Person</button>" in html
    assert ">Decide Later</button>" in html
