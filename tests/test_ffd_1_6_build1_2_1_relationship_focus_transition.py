from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question, questions_body


def seed(db):
    rows=[
        (1,'Mervyn','Neil Knuckey','M'),
        (2,'Elaine','Cox','F'),
        (3,'Victor','Alexander Knuckey','M'),
        (4,'Mavis','May Example','F'),
    ]
    for pid,g,s,sex in rows:
        db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
                   (pid,f'@I{pid}@',pid,g,s,f'{g} {s}',sex,f'{g} /{s}/'))
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(31,3,'Death','10 OCT 1975','Adelaide, South Australia',NULL,NULL,'DEAT')")
    for fid in (1,2): db.execute("INSERT INTO families(id,gedcom_xref) VALUES(?,?)",(fid,f'@F{fid}@'))
    # Mervyn + Elaine
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,2,'wife')")
    # Victor + Mavis -> Mervyn
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,3,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,4,'wife')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,1,'child')")
    db.commit()


def test_relationship_resolution_continues_original_fact_query(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    r=answer_question(db,'When did his father die?',1)
    assert r['status']=='ok'
    assert 'Victor Alexander Knuckey' in r['answer']
    assert '10 OCT 1975' in r['answer']
    assert r['kind']=='fact'
    assert r['context_person_id']==1
    assert r['question_subject_id']==3


def test_singular_wife_answer_changes_focus(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    r=answer_question(db,'so what about his wife',3)
    assert r['status']=='ok'
    assert 'Mavis May Example' in r['answer']
    assert r['context_person_id']==3
    assert r['question_subject_id']==4


def test_ui_carries_transitioned_focus_to_next_form(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    h=questions_body(db,1,'When did his father die?')
    assert 'Victor Alexander Knuckey' in h
    assert "name='person' value='1'" in h
    assert 'Move conversation to Victor Alexander Knuckey →' in h
    h=questions_body(db,3,'so what about his wife')
    assert 'Conversation is currently about <strong>Victor Alexander Knuckey</strong>' in h
    assert 'Move conversation to Mavis May Example →' in h
    assert "name='person' value='3'" in h
