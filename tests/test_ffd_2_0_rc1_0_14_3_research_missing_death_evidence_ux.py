from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import add_external_evidence
from reunion_companion.companion.beta_ui import person_page, research_page

def person(db,pid,xref,name,surname):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,xref,pid,name,surname,f"{name} {surname}","M",f"{name} /{surname}/"))

def event(db,pid,kind,date=None,place=None):
    db.execute("INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(?,?,?,?)",(pid,kind,date,place))

def test_missing_death_visible(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Rodney Thomas","Howie"); event(db,1,"Birth","07 Oct 1940","Adelaide"); db.commit()
    assert "Missing death information" in person_page(db,1,"research",presentation_override=False)
    h=research_page(db)
    assert "Missing Death Information" in h
    assert "Rodney Thomas Howie" in h
    assert "/person/1?tab=research" in h

def test_external_finding_visible(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Peter Stanly","Rigg"); event(db,1,"Birth","21 May 1944","Brighton Community Hospital"); db.commit()
    add_external_evidence(db,person_gedcom_xref="@I1@",person_name_snapshot="Peter Stanly Rigg",source_name="Ryerson",
        evidence_type="death_notice",source_record_name="Peter Stanley Rigg",event_type="Death",event_date="02JAN2021",
        publication="Adelaide Advertiser",publication_date="04JAN2021",details="late of Curramulka",
        match_confidence=99,match_reason="Exact birth date and surname.")
    h=person_page(db,1,"research",presentation_override=False)
    assert "Peter Stanley Rigg" in h
    assert "Ryerson" in h
    assert "Match 99%" in h
    assert "Adelaide Advertiser" in h
    assert "Curramulka" in h

def test_resolved_death_retains_finding(tmp_path):
    db=connect(tmp_path/"x.db"); person(db,1,"@I1@","Peter Stanly","Rigg"); db.commit()
    add_external_evidence(db,person_gedcom_xref="@I1@",person_name_snapshot="Peter Stanly Rigg",source_name="Ryerson",
        evidence_type="death_notice",source_record_name="Peter Stanley Rigg",event_type="Death",event_date="02JAN2021",review_status="accepted")
    event(db,1,"Death","02 Jan 2021"); db.commit()
    h=person_page(db,1,"research",presentation_override=False)
    assert "Resolved in Reunion" in h
    assert "Peter Stanley Rigg" in h
    assert "Accepted" in h
