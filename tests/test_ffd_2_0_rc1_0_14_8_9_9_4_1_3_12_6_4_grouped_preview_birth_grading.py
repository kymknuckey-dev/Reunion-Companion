from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import ensure_external_evidence
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import discovery_match_assessment, render_discovery_review_section


def add_person(db,pid,name,birth='01JAN1940'):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f'@I{pid}@',pid,name,name,name,'U',name))
    db.execute("INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)",(pid,'Birth',birth))
    db.commit()


def add_candidate(db,pid,claim,event_date,reason='surname exact; full name exact'):
    ensure_external_evidence(db)
    cur=db.execute("""INSERT INTO companion_external_evidence(person_gedcom_xref,person_name_snapshot,source_name,evidence_type,source_record_name,event_type,event_date,publication,publication_date,details,birth_date_claim,place_claim,match_confidence,match_reason,review_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(f'@I{pid}@','Person','Ryerson','death_notice','record','Death',event_date,'Adelaide Advertiser','20DEC2023','',claim,'',75,reason,'new','2026-01-01','2026-01-01'))
    db.commit()
    return remember_discovery(db,person_id=pid,source_name='Ryerson',external_record_key=f'ryerson:{cur.lastrowid}',proposed_fact_key='',match_confidence=75)


def test_direct_birth_claim_makes_one_of_four_candidates_strong(tmp_path):
    db=connect(tmp_path/'x.db'); add_person(db,1,'John Bickle Style',birth='10 MAR 1940')
    rows=[
        add_candidate(db,1,'11MAR1940','01JAN2020'),
        add_candidate(db,1,'10MAR1940','01JAN2021'),
        add_candidate(db,1,'12MAR1940','01JAN2022'),
        add_candidate(db,1,'13MAR1940','01JAN2023'),
    ]
    a=discovery_match_assessment(db,1,rows)
    assert a['level']=='Strong match'
    assert '1 strong match among 4' in a['detail']
    assert 'Birth date agrees' in a['detail']


def test_research_preview_is_grouped_not_flat(tmp_path):
    db=connect(tmp_path/'x.db')
    add_person(db,1,'Strong Person',birth='01JAN1940')
    add_candidate(db,1,'01JAN1940','01JAN2024')
    add_person(db,2,'Possible Person',birth='01JAN1940')
    add_candidate(db,2,'02JAN1940','01JAN2025')
    html=render_discovery_review_section(db,sort_mode='recent')
    assert "id='preview-grade-strong' open" in html
    assert "id='preview-grade-possible'" in html
    assert html.index('Strong match') < html.index('Possible match')
    assert 'Grouped by match quality' in html


def test_confirmed_complete_candidates_keep_match_grading(tmp_path):
    from reunion_companion.companion.ryerson_discovery_review import set_discovery_state
    from reunion_companion.companion.ryerson_discovery_ui import render_discovery_workspace
    db=connect(tmp_path/'x.db')
    add_person(db,1,'Completed Strong Person',birth='10 MAR 1940')
    row=add_candidate(db,1,'10MAR1940','01JAN2023')
    set_discovery_state(db,row['id'],'confirmed_complete')
    confirmed=db.execute("SELECT d.*,p.display_name,p.raw_name FROM companion_external_discovery_review d LEFT JOIN people p ON p.id=d.person_id WHERE d.state='confirmed_complete'").fetchall()
    assessment=discovery_match_assessment(db,1,confirmed)
    assert assessment['level']=='Strong match'
    html=render_discovery_workspace(db,state='confirmed_complete',sort_mode='recent')
    assert 'Strong match' in html
    assert 'Completed Strong Person' in html
    assert 'Unassessed' not in html or "0 people" in html
