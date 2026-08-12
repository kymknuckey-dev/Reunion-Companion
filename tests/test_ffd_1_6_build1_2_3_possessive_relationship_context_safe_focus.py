from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question, questions_body


def add_person(db,pid,given,surname,sex='M'):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,f'@I{pid}@',pid,given,surname,f'{given} {surname}',sex,f'{given} /{surname}/'))


def seed_family(db,two_sons=False):
    add_person(db,1,'Mervyn Neil','Knuckey','M')
    add_person(db,2,'Elaine','Cox','F')
    add_person(db,3,'Kym','Knuckey','M')
    add_person(db,4,'Jane','Example','F')
    add_person(db,5,'Ross','Knuckey','M')
    # Mervyn + Elaine, children Kym (and optionally Ross)
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,2,'wife')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,3,'child')")
    if two_sons:
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,5,'child')")
    # Kym + Jane
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(2,'@F2@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,3,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,4,'wife')")
    db.commit()


def test_named_possessive_relative_is_resolved_before_outer_spouse_query(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=True)
    r=answer_question(db,"Who did Elaine's son Kym marry?",subject_id=2)
    assert r['status']=='ok'
    assert 'Jane Example' in r['answer']
    assert 'Mervyn Neil Knuckey' not in r['answer']
    assert r['context_person']['id']==2
    assert r['question_subject']['id']==4


def test_unique_unnamed_possessive_relative_continues_query(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=False)
    r=answer_question(db,"Who did Elaine's son marry?",subject_id=2)
    assert r['status']=='ok'
    assert 'Jane Example' in r['answer']
    assert r['context_person']['id']==2
    assert r['question_subject']['id']==4


def test_ambiguous_unnamed_possessive_relative_requires_selection(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=True)
    r=answer_question(db,"Who did Elaine's son marry?",subject_id=2)
    assert r['status']=='ambiguous'
    assert r['kind']=='identity-choice'
    assert {p['id'] for p in r['people']}=={3,5}


def test_possessive_owner_does_not_fall_back_to_origin(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=True)
    r=answer_question(db,"Who did Elaine's son Kym marry?",subject_id=2)
    assert r['context_person']['id']==2
    assert r['question_subject']['id']==4
    h=questions_body(db,2,"Who did Elaine's son Kym marry?",origin_id=1)
    assert 'Conversation is currently about <strong>Elaine Cox</strong>' in h
    assert 'Move conversation to Jane Example →' in h
    assert '← Return to Mervyn Neil Knuckey' in h


def test_return_link_uses_existing_inline_navigation_style_and_sits_below_focus(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=False)
    h=questions_body(db,2,"Who did Elaine's son Kym marry?",origin_id=1)
    focus=h.index('Conversation is currently about')
    move=h.index('Move conversation to Jane Example →')
    ret=h.index('← Return to Mervyn Neil Knuckey')
    follow=h.index('Follow-up questions can use')
    assert focus < move < ret < follow
    assert "class='ffd-inline-link rq-return-origin'" in h
