from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question
from reunion_companion.companion.knowledge_conversation import answer_knowledge_question
from test_ffd_1_7_build2_knowledge_grounded_conversation import seed
from semantic_llm_test_support import SemanticFakeClient


def _patch_llm(monkeypatch):
    import reunion_companion.companion.knowledge_conversation as kc
    monkeypatch.setattr(kc, 'OllamaClient', SemanticFakeClient)


def test_notes_are_synthesised_not_renderer_dump(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"What do the notes say about James Knuckey?")
    a=r['answer'].casefold()
    assert r['kind']=='knowledge'
    assert 'family' in a and ('research' in a or 'exact year' in a)
    assert 'rather than repeating them verbatim' not in a


def test_work_answer_filters_note_material_to_work(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"Tell me about James Knuckey's working life")
    a=r['answer'].casefold()
    assert 'carpenter' in a and 'worked locally' in a
    assert 'check the exact year' not in a


def test_family_marriage_date_answers_structured_when_question(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"When did James Knuckey marry?")
    assert r['status']=='ok' and r['kind']=='fact'
    assert '1880' in r['answer'] and 'Adelaide, South Australia' in r['answer']


def test_marriage_narrative_uses_family_event_and_spouse(tmp_path, monkeypatch):
    _patch_llm(monkeypatch); db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_question(db,"What do we know about James Knuckey's marriage?")
    a=r['answer'].casefold()
    assert 'elizabeth hunter' in a and '1880' in a and 'adelaide' in a


def test_tell_me_more_reuses_prior_knowledge_topic(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    r=answer_knowledge_question(db,1,"Tell me more about that",prior_intent='topic:work',client=SemanticFakeClient())
    a=r['answer'].casefold()
    assert r['status']=='ok' and r['knowledge_intent']=='topic:work'
    assert 'carpenter' in a and 'worked locally' in a
