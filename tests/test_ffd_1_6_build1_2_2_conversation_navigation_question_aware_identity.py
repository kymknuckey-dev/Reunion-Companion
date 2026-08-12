from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question, questions_body


def add_person(db,pid,given,surname,sex='M'):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,f'@I{pid}@',pid,given,surname,f'{given} {surname}',sex,f'{given} /{surname}/'))


def seed_navigation(db):
    add_person(db,1,'Mervyn Neil','Knuckey')
    add_person(db,2,'Victor Alexander','Knuckey')
    add_person(db,3,'Mavis May','Example','F')
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(20,2,'Death','10 OCT 1975','Adelaide',NULL,NULL,'DEAT')")
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,2,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,3,'wife')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'child')")
    db.commit()


def seed_ambiguous(db):
    add_person(db,10,'Thomas','Knuckey')
    add_person(db,11,'Thomas','Knuckey')
    add_person(db,12,'Thomas','Knuckey')
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(101,11,'Religion',NULL,NULL,'Church of England',NULL,'RELI')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(102,12,'Occupation',NULL,NULL,'Miner',NULL,'OCCU')")
    db.commit()


def test_origin_is_preserved_while_relative_is_offered_as_explicit_move(tmp_path):
    db=connect(tmp_path/'x'); seed_navigation(db)
    h=questions_body(db,1,'When did his father die?',origin_id=1)
    assert 'Conversation started with <strong>Mervyn Neil Knuckey</strong>' in h
    assert 'Conversation is currently about <strong>Mervyn Neil Knuckey</strong>' in h
    assert 'Move conversation to Victor Alexander Knuckey →' in h
    assert 'Return to Mervyn Neil Knuckey' not in h
    assert "name='origin' value='1'" in h
    assert "name='person' value='1'" in h


def test_return_origin_link_restores_original_person(tmp_path):
    db=connect(tmp_path/'x'); seed_navigation(db)
    h=questions_body(db,1,'',origin_id=1)
    assert 'Conversation is currently about <strong>Mervyn Neil Knuckey</strong>' in h
    assert 'Return to Mervyn Neil Knuckey' not in h


def test_followup_wording_is_below_context_and_old_calculated_copy_removed(tmp_path):
    db=connect(tmp_path/'x'); seed_navigation(db)
    h=questions_body(db,1,'',origin_id=1)
    current=h.index('Conversation is currently about')
    follow=h.index('Follow-up questions can use')
    assert follow > current
    assert "class='rq-followup'" in h
    assert 'Answers are calculated directly' not in h
    assert 'Answers are generated directly' not in h


def test_religion_question_ranks_recorded_candidate_without_hiding_others(tmp_path):
    db=connect(tmp_path/'x'); seed_ambiguous(db)
    r=answer_question(db,'What religion is Thomas Knuckey?')
    assert r['status']=='ambiguous' and r['kind']=='identity-choice'
    by_id={c['person']['id']:c for c in r['choices']}
    assert by_id[11]['question_relevant'] is True
    assert by_id[11]['relevance_label']=='Religion recorded'
    assert by_id[10]['question_relevant'] is False
    assert by_id[12]['question_relevant'] is False
    h=questions_body(db,None,'What religion is Thomas Knuckey?')
    assert 'Matches with religion information' in h
    assert 'Other matches — requested information not currently recorded (2)' in h
    assert h.count("<div class='rq-identity-name'>Thomas Knuckey</div>")==3


def test_occupation_question_uses_same_fact_aware_ranking(tmp_path):
    db=connect(tmp_path/'x'); seed_ambiguous(db)
    r=answer_question(db,'What occupation did Thomas Knuckey have?')
    by_id={c['person']['id']:c for c in r['choices']}
    assert by_id[12]['question_relevant'] is True
    assert by_id[12]['relevance_label']=='Occupation recorded'
    assert by_id[10]['question_relevant'] is False
    assert by_id[11]['question_relevant'] is False
