from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question
from semantic_llm_test_support import SemanticFakeClient


def seed(db):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Neil Knuckey','M','Mervyn /Knuckey/')")
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(2,'@I2@',2,'Elaine','Cox','Elaine Fay Cox','F','Elaine /Cox/')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(10,1,'Occupation',NULL,NULL,'Public Servant. S.A. Health Commission [Retired]',NULL,'OCCU')")
    db.executemany("INSERT INTO notes(id,person_id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced) VALUES(?,?,?,?,?,?,?)",[
        (20,1,'Misc Notes','NOTE',None,"After leaving School Mervyn's first job was with A.M.Bickford & Sons in Currie St. Adelaide as a warehouse assistant. He later worked with Rawson's Electrical. This note also says service at the counter was busy.",0),
        (21,1,'Medical','NOTE',None,"Mervyn was admitted to hospital with a cardiology problem. He later returned home after treatment.",0),
        (22,1,'Military Service','NOTE',None,"Mervyn enlisted in 1952. He completed 176 days before returning to Adelaide. His record notes his posting and discharge details.",0),
    ])
    db.execute("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(30,'@F30@','1954','Adelaide, South Australia')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(30,1,'Husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(30,2,'Wife')")
    db.commit()


def _patch_llm(monkeypatch):
    import reunion_companion.companion.knowledge_conversation as kc
    monkeypatch.setattr(kc, 'OllamaClient', SemanticFakeClient)


def test_notes_preserve_note_subjects_semantically(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,'What do the notes say about Mervyn Knuckey?')
    a=r['answer'].casefold()
    assert 'working life' in a and 'medical' in a and 'military' in a
    assert '1952' in a and '176 days' in a
    assert 'Based on:' in r['answer']


def test_military_topic_uses_typed_military_evidence_and_excludes_medical(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"Tell me about Mervyn Knuckey's military service")
    a=r['answer'].casefold()
    assert '1952' in a and '176 days' in a and 'posting and discharge' in a
    assert 'cardiology' not in a and 'hospital' not in a
    assert 'Based on: Military Service' in r['answer']


def test_working_life_preserves_work_facts_without_medical_dump(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"Tell me about Mervyn Knuckey's working life")
    a=r['answer'].casefold()
    for fact in ('public servant','s.a. health commission','bickford','rawson'):
        assert fact in a
    assert 'cardiology' not in a and 'hospital' not in a


def test_note_evidence_is_not_character_truncated_before_synthesis(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,'What do the notes say about him?', subject_id=1)
    a=r['answer'].casefold()
    assert 'posting and discharge details' in a
    assert '…' not in r['answer']


def test_family_marriage_integration_is_retained(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"What do we know about Mervyn Knuckey's marriage?")
    a=r['answer'].casefold()
    assert 'elaine fay cox' in a and '1954' in a and 'adelaide' in a
