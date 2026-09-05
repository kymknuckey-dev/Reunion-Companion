from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import ensure_external_evidence
from reunion_companion.companion.ryerson_discovery_review import remember_discovery, set_discovery_state
from reunion_companion.companion.ryerson_discovery_ui import research_value_assessment, render_discovery_workspace


def person(db,pid,name):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid,name,name,name,"U",name))
    db.commit()


def unsourced_death(db,pid,date):
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)",(pid,"Death",date)); db.commit()


def evidence(db,pid,event_date,evidence_type="death_notice",event_type="Death",confidence=75):
    ensure_external_evidence(db)
    cur=db.execute("""INSERT INTO companion_external_evidence(person_gedcom_xref,person_name_snapshot,source_name,evidence_type,source_record_name,event_type,event_date,publication,publication_date,details,birth_date_claim,place_claim,match_confidence,match_reason,review_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(f"@I{pid}@","Person","Ryerson",evidence_type,"record",event_type,event_date,"Paper","","","","",confidence,"name","new","2026-01-01","2026-01-01"))
    db.commit(); return cur.lastrowid


def discovery(db,pid,eid,fact,confidence=75):
    return remember_discovery(db,person_id=pid,source_name="Ryerson",external_record_key=f"ryerson:{eid}",proposed_fact_key=fact,match_confidence=confidence)


def test_same_normalised_death_date_is_high_opportunity(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,1,'Benjamin Dolphin'); unsourced_death(db,1,'11 MAR 2003')
    eid=evidence(db,1,'11MAR2003'); row=discovery(db,1,eid,'death:11MAR2003')
    a=research_value_assessment(db,1,[row])
    assert a['level']=='High opportunity'
    assert a['reason']=='May source existing Death'
    assert 'dates agree' in a['detail']


def test_conflicting_death_is_not_promoted(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,2,'Eileen Knuckey'); unsourced_death(db,2,'18 DEC 1971')
    eid=evidence(db,2,'13MAR1979'); row=discovery(db,2,eid,'death:13MAR1979')
    a=research_value_assessment(db,2,[row])
    assert a['level']=='Needs careful review'
    assert 'conflicts' in a['reason']


def test_processed_candidate_cannot_raise_current_research_value(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,3,'Accepted Person'); unsourced_death(db,3,'20 JUL 2012')
    eid=evidence(db,3,'20JUL2012'); row=discovery(db,3,eid,'death:20JUL2012')
    set_discovery_state(db,row['id'],'already_known')
    current=db.execute("SELECT * FROM companion_external_discovery_review WHERE person_id=? AND state='new'",(3,)).fetchall()
    a=research_value_assessment(db,3,current)
    assert a['level']=='Lower immediate value'


def test_discovery_review_uses_visual_match_grading_instead_of_third_value_sort(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,4,'Review Person'); unsourced_death(db,4,'01 JAN 2000')
    eid=evidence(db,4,'01JAN2000'); discovery(db,4,eid,'death:01JAN2000')
    html=render_discovery_workspace(db,state='new',sort_mode='value')
    assert 'Research Value' not in html
    assert 'Most Recent' in html
    assert 'Relationship' in html
    assert 'Possible match' in html


def test_missing_death_with_one_recent_candidate_is_high(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,5,'Specific Recent Person')
    eid=evidence(db,5,'17DEC2023'); row=discovery(db,5,eid,'death:17DEC2023')
    a=research_value_assessment(db,5,[row])
    assert a['level']=='High opportunity'
    assert a['reason']=='May fill missing Death'


def test_missing_death_with_many_candidates_is_not_high(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,6,'Common Name')
    rows=[]
    for i in range(6):
        eid=evidence(db,6,f'0{i+1}JAN2020')
        rows.append(discovery(db,6,eid,f'death:0{i+1}JAN2020'))
    a=research_value_assessment(db,6,rows)
    assert a['level']=='Needs careful review'
    assert 'Many possible' in a['reason']


def test_old_missing_death_is_not_high_even_when_specific(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,7,'Old Lead')
    eid=evidence(db,7,'27APR1924'); row=discovery(db,7,eid,'death:27APR1924')
    a=research_value_assessment(db,7,[row])
    assert a['level']=='Potential opportunity'
    assert 'Older' in a['reason']
