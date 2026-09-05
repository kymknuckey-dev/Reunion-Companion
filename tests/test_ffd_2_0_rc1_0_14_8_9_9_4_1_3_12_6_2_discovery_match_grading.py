from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import ensure_external_evidence
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import discovery_match_assessment, render_discovery_workspace


def person(db,pid,name):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid,name,name,name,"U",name))
    db.commit()


def evidence(db,pid,*,reason,confidence=75,publication="Adelaide Advertiser",event_date="17DEC2023"):
    ensure_external_evidence(db)
    cur=db.execute("""INSERT INTO companion_external_evidence(person_gedcom_xref,person_name_snapshot,source_name,evidence_type,source_record_name,event_type,event_date,publication,publication_date,details,birth_date_claim,place_claim,match_confidence,match_reason,review_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(f"@I{pid}@","Person","Ryerson","death_notice","record","Death",event_date,publication,"20DEC2023","","","",confidence,reason,"new","2026-01-01","2026-01-01"))
    db.commit()
    return cur.lastrowid


def discovery(db,pid,eid,confidence=75):
    return remember_discovery(db,person_id=pid,source_name="Ryerson",external_record_key=f"ryerson:{eid}",proposed_fact_key="",match_confidence=confidence)


def test_birth_date_agreement_is_strong_match(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,1,'Strong Person')
    eid=evidence(db,1,reason='surname exact; full name exact; birth date exact',confidence=100)
    a=discovery_match_assessment(db,1,[discovery(db,1,eid,100)])
    assert a['level']=='Strong match'
    assert 'Birth date agrees' in a['detail']
    assert 'Adelaide Advertiser' in a['detail']


def test_place_or_family_detail_provides_supported_match(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,2,'Supported Person')
    eid=evidence(db,2,reason='surname exact; full name exact; place consistent; spouse corroborated',confidence=95)
    a=discovery_match_assessment(db,2,[discovery(db,2,eid,95)])
    assert a['level']=='Supported match'
    assert 'Place agrees' in a['detail']
    assert 'Family detail agrees' in a['detail']


def test_many_name_only_candidates_are_low_specificity(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,3,'Common Name')
    rows=[]
    for i in range(6):
        eid=evidence(db,3,reason='surname exact; full name exact',confidence=75,event_date=f'0{i+1}JAN2020')
        rows.append(discovery(db,3,eid,75))
    a=discovery_match_assessment(db,3,rows)
    assert a['level']=='Low specificity'
    assert '6 current candidates' in a['detail']


def test_one_strong_candidate_is_not_erased_by_many_name_candidates(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,4,'Many But One Strong')
    rows=[]
    for i in range(8):
        reason='surname exact; full name exact; birth date exact' if i==4 else 'surname exact; full name exact'
        conf=100 if i==4 else 75
        eid=evidence(db,4,reason=reason,confidence=conf,event_date=f'0{i+1}JAN2020')
        rows.append(discovery(db,4,eid,conf))
    a=discovery_match_assessment(db,4,rows)
    assert a['level']=='Strong match'
    assert '1 strong match among 8' in a['detail']


def test_ui_keeps_two_sort_modes_and_shows_match_grade(tmp_path):
    db=connect(tmp_path/'x.db'); person(db,5,'Visual Grade')
    eid=evidence(db,5,reason='surname exact; full name exact; birth date exact',confidence=100)
    discovery(db,5,eid,100)
    html=render_discovery_workspace(db,state='new',sort_mode='recent')
    assert 'Most Recent' in html
    assert 'Relationship' in html
    assert 'Research Value' not in html
    assert 'Strong match' in html
    assert 'Birth date agrees' in html
