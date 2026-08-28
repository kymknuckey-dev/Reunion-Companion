from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_person_finding_bridge import (
    _finding_to_candidate,
    materialize_person_level_ryerson_findings,
)
from reunion_companion.companion.ryerson_discovery_review import (
    discoveries_for_person,
    set_discovery_state,
)


def add_person(db,pid,name,xref):
    db.execute(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (pid,xref,pid,name.split()[0],name.split()[-1],name,"U",name),
    )
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text,note_text) VALUES(?,?,?,?,?)",(pid,"Birth","1 JAN 1950",None,None))
    db.commit()


def test_existing_ryerson_finding_adapts_to_person_candidate():
    finding={"source_name":"Ryerson","id":"abc","death_date":"1910-07-11","review_status":"candidate"}
    c=_finding_to_candidate(7,finding)
    assert c["person_id"]==7
    assert c["notice_id"]=="abc"
    assert c["death_date"]=="1910-07-11"


def test_non_ryerson_and_rejected_findings_are_not_materialised():
    assert _finding_to_candidate(1,{"source_name":"Other","id":"x"}) is None
    assert _finding_to_candidate(1,{"source_name":"Ryerson","id":"x","review_status":"rejected"}) is None


def test_bridge_uses_existing_person_level_evidence_api(monkeypatch,tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Richard Knuckey","@I1@")
    add_person(db,2,"Mary Smith","@I2@")

    import reunion_companion.companion.external_evidence as evidence

    def fake(db,xref):
        if xref=="@I1@":
            return [{"source_name":"Ryerson","id":"richard-1","death_date":"2020-01-02","review_status":"candidate"}]
        return []

    monkeypatch.setattr(evidence,"external_evidence_for_person",fake)

    result=materialize_person_level_ryerson_findings(db)
    assert result["people_checked"]==2
    assert result["ryerson_findings"]==1
    rows=discoveries_for_person(db,1)
    assert len(rows)==1
    assert rows[0]["proposed_fact_key"]=="death:2020-01-02"


def test_bridge_is_idempotent_and_preserves_decision(monkeypatch,tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Richard Knuckey","@I1@")

    import reunion_companion.companion.external_evidence as evidence
    monkeypatch.setattr(
        evidence,
        "external_evidence_for_person",
        lambda db,xref:[{"source_name":"Ryerson","id":"same","review_status":"candidate"}],
    )

    materialize_person_level_ryerson_findings(db)
    row=discoveries_for_person(db,1)[0]
    set_discovery_state(db,row["id"],"already_known",note="Checked")

    materialize_person_level_ryerson_findings(db)
    rows=discoveries_for_person(db,1)
    assert len(rows)==1
    assert rows[0]["state"]=="already_known"
    assert rows[0]["decision_note"]=="Checked"
