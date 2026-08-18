from reunion_companion.companion.database import connect
from reunion_companion.companion.identity_discovery import resolve_identity_name
from reunion_companion.companion.ffd_relationship_questions import answer_question


def seed(db):
    db.executescript("""
    INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES
      (1,'@I1@',1,'Mervyn','Knuckey','Mervyn Knuckey','M','Mervyn /Knuckey/'),
      (2,'@I2@',2,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),
      (3,'@I3@',3,'Dean Mervyn','Knuckey','Dean Mervyn Knuckey','M','Dean Mervyn /Knuckey/');
    INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES
      (10,2,'Birth','24 SEP 1933','Unley Private Hospital, Unley, South Australia',NULL,NULL,'BIRT');
    """)
    db.commit()


def test_merv_is_conservative_given_variant_of_mervyn(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    names=[p['display_name'] for p in resolve_identity_name(db,'Merv Knuckey')]
    assert 'Mervyn Knuckey' in names
    assert 'Mervyn Neil Knuckey' in names


def test_global_question_two_token_literal_offers_candidates(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    r=answer_question(db,'Where was Mervyn Knuckey born?',global_identity_discovery=True)
    assert r['kind']=='identity-choice'
    names={c['person']['display_name'] for c in r['choices']}
    assert {'Mervyn Knuckey','Mervyn Neil Knuckey'} <= names


def test_global_question_short_variant_offers_candidates(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    r=answer_question(db,'Where was Merv Knuckey born?',global_identity_discovery=True)
    assert r['kind']=='identity-choice'
    assert any(c['person']['display_name']=='Mervyn Neil Knuckey' for c in r['choices'])


def test_full_literal_name_still_answers_on_first_turn(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    r=answer_question(db,'Where was Mervyn Neil Knuckey born?',global_identity_discovery=True)
    assert r['status']=='ok'
    assert 'Unley Private Hospital' in r['answer']


def test_selected_partial_name_candidate_answers_same_turn(tmp_path):
    db=connect(tmp_path/'x.sqlite3');seed(db)
    r=answer_question(db,'Where was Mervyn Knuckey born?',selected_identity_id=2,global_identity_discovery=True)
    assert r['status']=='ok'
    assert 'Unley Private Hospital' in r['answer']
