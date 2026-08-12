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
    add_person(db,5,'Jamie','Knuckey','M')
    add_person(db,6,'Anne','Example','F')
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
    for pid,role in ((1,'husband'),(2,'wife'),(3,'child')):
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,?,?)",(pid,role))
    if two_sons:
        db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,5,'child')")
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(2,'@F2@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,3,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,4,'wife')")
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(3,'@F3@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(3,5,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(3,6,'wife')")
    db.commit()


def test_her_son_is_intermediate_not_elaine_spouse(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=False)
    r=answer_question(db,"Who did her son marry?",subject_id=2)
    assert r['status']=='ok'
    assert 'Jane Example' in r['answer']
    assert 'Mervyn Neil Knuckey' not in r['answer']


def test_her_son_kym_uses_named_constraint(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=True)
    r=answer_question(db,"Who did her son Kym marry?",subject_id=2)
    assert r['status']=='ok'
    assert 'Jane Example' in r['answer']
    assert 'Mervyn Neil Knuckey' not in r['answer']


def test_her_son_requires_selection_when_multiple_sons(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=True)
    r=answer_question(db,"Who did her son marry?",subject_id=2)
    assert r['status']=='ambiguous'
    assert r['kind']=='identity-choice'
    assert {p['id'] for p in r['people']}=={3,5}


def test_pronoun_and_named_possessives_have_same_result(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=True)
    named=answer_question(db,"Who did Elaine's son Kym marry?",subject_id=2)
    pronoun=answer_question(db,"Who did her son Kym marry?",subject_id=2)
    assert named['answer']==pronoun['answer']
    assert named['context_person_id']==pronoun['context_person_id']


def test_return_origin_link_points_back_with_left_arrow(tmp_path):
    db=connect(tmp_path/'x'); seed_family(db,two_sons=False)
    h=questions_body(db,2,"Who did her son Kym marry?",origin_id=1)
    assert '← Return to Mervyn Neil Knuckey' in h
    assert 'Return to Mervyn Neil Knuckey →' not in h
    focus=h.index('Conversation is currently about')
    ret=h.index('← Return to Mervyn Neil Knuckey')
    follow=h.index('Follow-up questions can use')
    assert focus < ret < follow
    assert "class='ffd-inline-link rq-return-origin'" in h
