from reunion_companion.companion.database import connect
from reunion_companion.companion.external_evidence import ensure_external_evidence
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import render_discovery_workspace


def add_person(db,pid,name):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f"@I{pid}@",pid,name,name,name,"U",name))
    db.commit()


def add_evidence(db,pid,*,reason,event_date,confidence=75):
    ensure_external_evidence(db)
    cur=db.execute("""INSERT INTO companion_external_evidence(person_gedcom_xref,person_name_snapshot,source_name,evidence_type,source_record_name,event_type,event_date,publication,publication_date,details,birth_date_claim,place_claim,match_confidence,match_reason,review_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(f"@I{pid}@",f"Person {pid}","Ryerson","death_notice",f"record-{pid}","Death",event_date,"Adelaide Advertiser","20DEC2023","","","",confidence,reason,"new","2026-01-01","2026-01-01"))
    db.commit()
    remember_discovery(db,person_id=pid,source_name="Ryerson",external_record_key=f"ryerson:{cur.lastrowid}",proposed_fact_key="",match_confidence=confidence)


def test_workspace_groups_by_grade_and_sorts_recent_inside_group(tmp_path):
    db=connect(tmp_path/'x.db')
    add_person(db,1,'Older Strong'); add_evidence(db,1,reason='birth date exact',event_date='01JAN2020',confidence=100)
    add_person(db,2,'Newer Strong'); add_evidence(db,2,reason='birth date exact',event_date='01JAN2024',confidence=100)
    add_person(db,3,'Possible'); add_evidence(db,3,reason='surname exact; full name exact',event_date='01JAN2025',confidence=75)
    html=render_discovery_workspace(db,state='new',sort_mode='recent',page_size=20)
    assert "<details class='card rc-review-grade-group' id='grade-strong' open>" in html
    assert 'Strong match' in html and 'Possible match' in html
    assert html.index('Newer Strong') < html.index('Older Strong')
    assert html.index('Strong match') < html.index('Possible match')


def test_group_pager_is_inside_requested_group(tmp_path):
    db=connect(tmp_path/'x.db')
    for pid in range(1,4):
        add_person(db,pid,f'Strong {pid}')
        add_evidence(db,pid,reason='birth date exact',event_date=f'0{pid}JAN2024',confidence=100)
    html=render_discovery_workspace(db,state='new',sort_mode='recent',page=2,page_size=2,group='strong')
    start=html.index("id='grade-strong'")
    end=html.index('</details>',start)
    group_html=html[start:end]
    assert 'Page 2 of 2 · 3 people in Strong match' in group_html
    assert '>Previous<' in group_html
    assert '#grade-strong' in group_html
    assert 'Strong 3' in group_html
    assert 'Strong 1' not in group_html
