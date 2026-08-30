from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import add_external_evidence
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import discovery_review_rows,_group_people,sort_grouped_people_recent,render_discovery_review_section,render_discovery_workspace
from reunion_companion.companion.beta_ui import research_page


def add_person(db,pid,name):
    bits=name.split()
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid," ".join(bits[:-1]),bits[-1],name,"U",name))
    db.commit()


def discovery(db,pid,year,confidence=75):
    remember_discovery(db,person_id=pid,source_name="Ryerson",external_record_key=f"r{pid}",proposed_fact_key=f"death:01JAN{year}",match_confidence=confidence)


def test_recent_priority_uses_highest_current_unresolved_external_candidate(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Peter Charles Mitchell"); add_person(db,2,"Newer Name Match")
    discovery(db,1,2010,75); discovery(db,2,2025,75)
    add_external_evidence(db,person_gedcom_xref="@I1@",person_name_snapshot="Peter Charles Mitchell",source_name="Ryerson",evidence_type="death_notice",event_date="2010-01-01",match_confidence=100,review_status="new")
    ordered=sort_grouped_people_recent(_group_people(discovery_review_rows(db,state="new")),db)
    assert [pid for pid,_ in ordered]==[1,2]


def test_resolved_high_confidence_no_longer_controls_priority(tmp_path):
    db=connect(tmp_path/"x.db")
    add_person(db,1,"Older Resolved Match"); add_person(db,2,"Newer Unresolved Match")
    discovery(db,1,2010,75); discovery(db,2,2025,75)
    add_external_evidence(db,person_gedcom_xref="@I1@",person_name_snapshot="Older Resolved Match",source_name="Ryerson",evidence_type="death_notice",event_date="2010-01-01",match_confidence=100,review_status="accepted")
    ordered=sort_grouped_people_recent(_group_people(discovery_review_rows(db,state="new")),db)
    assert [pid for pid,_ in ordered]==[2,1]


def test_embedded_external_review_page_two_has_previous(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid in range(1,14): add_person(db,pid,f"Person {pid}"); discovery(db,pid,2000+pid)
    html=render_discovery_review_section(db,page=2)
    assert "evidence_page=1" in html and html.count(">Previous</a>")==1 and "Page 2 of 2" in html


def test_full_external_review_page_two_has_previous(tmp_path):
    db=connect(tmp_path/"x.db")
    for pid in range(1,22): add_person(db,pid,f"Person {pid}"); discovery(db,pid,2000+pid)
    html=render_discovery_workspace(db,page=2,page_size=20)
    assert "page=1" in html and html.count(">Previous</a>")==1 and "Page 2 of 2" in html


def test_research_needed_and_data_quality_page_two_have_previous(tmp_path,monkeypatch):
    db=connect(tmp_path/"x.db")
    for pid in range(1,14):
        add_person(db,pid,f"Person {pid}")
        db.execute("INSERT INTO events(person_id,event_type,date_text,place_text) VALUES(?,?,?,?)",(pid,"Birth",f"01JAN{1900+pid}","Adelaide"))
    db.commit()
    import reunion_companion.companion.external_evidence_matcher as matcher
    death_rows=[{"person_id":pid,"display_name":f"Person {pid}","death_state":"missing","death_note_text":""} for pid in range(1,14)]
    monkeypatch.setattr(matcher,"missing_death_candidates",lambda db:death_rows)
    html=research_page(db,{"research_page":"2","quality_page":"2"})
    assert "research_page=1" in html and "quality_page=1" in html
    assert html.count(">Previous</a>")==2
