from reunion_companion.companion.database import connect
from reunion_companion.companion.knowledge_conversation import answer_knowledge_question, interpret_knowledge_question
from reunion_companion.companion.ffd_relationship_questions import answer_question
from semantic_llm_test_support import SemanticFakeClient


def seed(db):
    db.executemany(
        "INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
        [
            (1,"@I1@",1,"James","Knuckey","James Knuckey","M","James /Knuckey/"),
            (2,"@I2@",2,"Elizabeth","Hunter","Elizabeth Hunter","F","Elizabeth /Hunter/"),
            (3,"@I3@",3,"Thomas","Knuckey","Thomas Knuckey","M","Thomas /Knuckey/"),
            (4,"@I4@",4,"Jane","Peters","Jane Peters","F","Jane /Peters/"),
        ],
    )
    db.executemany(
        "INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",
        [
            (10,1,"Birth","1 JUN 1857","Tea Tree Gully, South Australia","Y","Birth memo","BIRT"),
            (11,1,"Occupation","1890","Gilberton, South Australia","Carpenter",None,"OCCU"),
            (12,1,"Religion",None,None,"Church of England",None,"RELI"),
            (13,1,"Death","11 JUL 1910","North Adelaide, South Australia",None,None,"DEAT"),
        ],
    )
    db.executemany(
        "INSERT INTO notes(id,person_id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced) VALUES(?,?,?,?,?,?,?)",
        [
            (20,1,"Note","NOTE",None,"James moved with his family and worked locally.",0),
            (21,1,"Research","_NOTE",None,"Check the exact year of the move.",0),
        ],
    )
    db.executemany("INSERT INTO families(id,gedcom_xref,marriage_date,marriage_place) VALUES(?,?,?,?)",[(30,"@F30@","1880","Adelaide, South Australia"),(31,"@F31@",None,None)])
    db.executemany("INSERT INTO family_members(family_id,person_id,role) VALUES(?,?,?)",[(30,1,"Husband"),(30,2,"Wife"),(31,3,"Husband"),(31,4,"Wife"),(31,1,"Child")])
    db.executemany("INSERT INTO sources(id,gedcom_xref,title,text,source_type,display_text) VALUES(?,?,?,?,?,?)",[(40,"@S40@","Birth Certificate","SA birth registration","Civil","Birth certificate")])
    db.execute("INSERT INTO event_sources(event_id,source_id,relation) VALUES(10,40,'GEDCOM')")
    db.executemany("INSERT INTO media(id,gedcom_xref,file_path,title,media_type,exists_on_disk,attachment_scope,attachment_label) VALUES(?,?,?,?,?,?,?,?)",[(60,None,"/tmp/james.jpg","James portrait","image/jpeg",0,"person",None)])
    db.execute("INSERT INTO person_media(person_id,media_id,relation) VALUES(1,60,'GEDCOM')")
    db.commit()


def _patch_llm(monkeypatch):
    import reunion_companion.companion.knowledge_conversation as kc
    monkeypatch.setattr(kc, 'OllamaClient', SemanticFakeClient)


def test_broad_story_intents_are_recognised_without_stealing_fact_questions():
    assert interpret_knowledge_question("Tell me about James Knuckey") == "overview"
    assert interpret_knowledge_question("What do we know about James Knuckey?") == "overview"
    assert interpret_knowledge_question("What do the notes say about him?") == "notes"
    assert interpret_knowledge_question("Tell me about his working life") == "topic:work"
    assert interpret_knowledge_question("When did James Knuckey die?") is None


def test_tell_me_about_uses_person_knowledge_semantically(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"Tell me about James Knuckey")
    a=r['answer'].casefold()
    assert r['status']=='ok' and r['kind']=='knowledge' and r['grounding']=='Reunion Person Knowledge'
    for fact in ('james knuckey','1857','tea tree gully','carpenter','elizabeth hunter','1910'):
        assert fact in a


def test_notes_question_uses_current_conversation_person(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"What do the notes say about him?",subject_id=1)
    a=r['answer'].casefold()
    assert r['status']=='ok' and r['knowledge_intent']=='notes' and r['context_person_id']==1
    assert 'family' in a and 'local' in a and ('exact year' in a or 'checking' in a)


def test_working_life_combines_event_and_note_material(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"Tell me about James Knuckey's working life")
    a=r['answer'].casefold()
    assert r['knowledge_intent']=='topic:work'
    assert 'carpenter' in a and 'gilberton' in a and '1890' in a and 'worked locally' in a


def test_marriage_topic_combines_spouse_and_family_context(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"Tell me about James Knuckey's marriage")
    a=r['answer'].casefold()
    assert r['knowledge_intent']=='topic:marriage'
    assert 'elizabeth hunter' in a and '1880' in a and 'adelaide' in a


def test_structured_fact_questions_keep_existing_path(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"When did James Knuckey die?")
    assert r['kind']=='fact' and '11 JUL 1910' in r['answer']


def test_direct_knowledge_api_is_safe_for_missing_person(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_knowledge_question(db,999,"Tell me about this person",client=SemanticFakeClient())
    assert r['status']=='not-found'
