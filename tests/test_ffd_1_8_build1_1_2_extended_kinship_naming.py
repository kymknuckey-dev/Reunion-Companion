from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question, blood_relationship
from test_ffd_1_8_build1_1_query_consistency_hardening import seed, add_person


def seed_mitchell(db):
    seed(db)
    add_person(db,9,'Mitchell Luke Knuckey','M')
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(4,'@F4@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(4,3,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(4,9,'child')")
    db.commit()


def test_existing_mervyn_lionel_maternal_uncle_is_retained(tmp_path):
    db=connect(tmp_path/'x'); seed_mitchell(db)
    rel=blood_relationship(db,2,8)
    assert rel and rel['label']=='maternal uncle'
    r=answer_question(db,'How is Mervyn Neil Knuckey related to Lionel George Waight?',2)
    assert 'maternal uncle' in r['answer'].casefold()


def test_mitchell_lionel_is_great_great_uncle(tmp_path):
    db=connect(tmp_path/'x'); seed_mitchell(db)
    rel=blood_relationship(db,9,8)
    assert rel and rel['label']=='great-great-uncle'
    r=answer_question(db,'How is Mitchell Luke Knuckey related to Lionel George Waight?',9)
    assert 'great-great-uncle' in r['answer'].casefold()
    assert r.get('context_person_id')==9
