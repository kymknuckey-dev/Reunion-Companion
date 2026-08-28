from reunion_companion.companion.database import connect
from reunion_companion.companion.ryerson_discovery_assembly import _definite_date, impossible_death_before_birth
from reunion_companion.companion.ryerson_discovery_review import remember_discovery
from reunion_companion.companion.ryerson_discovery_ui import review_row_for_finding, render_finding_decision_controls, finding_impossible_for_person


def add_person(db,pid,name='Ellen Clark'):
    bits=name.split()
    db.execute('INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)',(pid,f'@I{pid}@',pid,' '.join(bits[:-1]),bits[-1],name,'U',name))
    db.commit()


def add_birth(db,pid,date_text):
    db.execute('INSERT INTO events(person_id,event_type,date_text) VALUES(?,?,?)',(pid,'Birth',date_text))
    db.commit()


def test_compact_ryerson_date_parses():
    assert str(_definite_date('01JUN1860'))=='1860-06-01'


def test_funeral_before_birth_is_impossible():
    assert impossible_death_before_birth({'person_id':1,'birth_date':'01 JAN 1869','funeral_date':'01JUN1860'})


def test_impossible_finding_is_detected_for_person(tmp_path):
    db=connect(tmp_path/'x.db'); add_person(db,1); add_birth(db,1,'01 JAN 1869')
    assert finding_impossible_for_person(db,1,{'event_type':'Funeral','event_date':'01JUN1860'})


def test_duplicate_same_date_uses_publication_to_match(tmp_path):
    db=connect(tmp_path/'x.db'); add_person(db,1)
    a=remember_discovery(db,person_id=1,source_name='Ryerson',external_record_key='ryerson:clark|ellen|28JUL1954|30JUL1954|Sydney Morning Herald|death',proposed_fact_key='death:28JUL1954')
    b=remember_discovery(db,person_id=1,source_name='Ryerson',external_record_key='ryerson:clark|ellen|28JUL1954|31JUL1954|Sydney Morning Herald|death',proposed_fact_key='death:28JUL1954')
    finding={'source_name':'Ryerson','event_type':'Death','event_date':'28JUL1954','publication':'Sydney Morning Herald','publication_date':'31JUL1954'}
    row=review_row_for_finding(db,1,finding)
    assert row['id']==b['id']
    html=render_finding_decision_controls(db,1,finding)
    assert '>Accept</button>' in html and '>Known</button>' in html and 'Not This Person' in html and 'Decide Later' in html
