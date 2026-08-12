from reunion_companion.companion.database import connect
from reunion_companion.companion.knowledge_conversation import answer_knowledge_question
from reunion_companion.companion.local_llm import LocalLLMConfig, LocalLLMError, OllamaClient, _assert_loopback


class FakeClient:
    def __init__(self):
        self.prompts=[]
    def generate(self, prompt):
        self.prompts.append(prompt)
        if 'Relevant factual digest:' in prompt:
            return 'Condensed factual digest.'
        return 'Mervyn served for 176 days in 1952 before returning to Adelaide. This is newly written narrative prose.'
    def resolve_model(self):
        return 'gemma3:4b'


def seed(db):
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn','Knuckey','Mervyn Neil Knuckey','M','Mervyn /Knuckey/')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(10,1,'Occupation',NULL,NULL,'Public Servant. S.A. Health Commission [Retired]',NULL,'OCCU')")
    db.executemany(
        "INSERT INTO notes(id,person_id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced) VALUES(?,?,?,?,?,?,?)",
        [
            (20,1,'Misc Notes','NOTE',None,"After leaving school Mervyn worked at A.M. Bickford & Sons. Later he worked at Rawson's Electrical.",0),
            (21,1,'Medical','NOTE',None,"Mervyn was admitted to hospital with a cardiology problem and later returned home.",0),
            (22,1,'Military Service','NOTE',None,"Mervyn enlisted in 1952. He completed 176 days before returning to Adelaide. His posting and discharge are recorded.",0),
        ],
    )
    db.commit()


def test_build3_uses_local_llm_and_keeps_medical_out_of_military_prompt(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); client=FakeClient()
    r=answer_knowledge_question(db,1,'Tell me about his military service',client=client)
    assert r['status']=='ok'
    assert r['synthesis_mode']=='local-llm-grounded'
    assert r['llm_provider']=='Ollama'
    assert r['llm_model']=='gemma3:4b'
    assert 'newly written narrative prose' in r['answer']
    final=client.prompts[-1]
    assert '[Military Service]' in final
    assert '176 days' in final
    assert 'cardiology problem' not in final
    assert '[Medical]' not in final
    assert 'Based on: Military Service' in r['answer']


def test_notes_overview_supplies_all_authored_note_objects_to_llm(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); client=FakeClient()
    r=answer_knowledge_question(db,1,'What do the notes say about him?',client=client)
    final=client.prompts[-1]
    assert '[Misc Notes]' in final
    assert '[Medical]' in final
    assert '[Military Service]' in final
    assert 'Do not dump each note in sequence' in final
    assert 'Misc Notes' in r['answer'] and 'Medical' in r['answer'] and 'Military Service' in r['answer']


def test_work_topic_uses_structured_occupation_and_general_work_passages(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db); client=FakeClient()
    answer_knowledge_question(db,1,'Tell me about his working life',client=client)
    final=client.prompts[-1]
    assert 'Public Servant. S.A. Health Commission [Retired]' in final
    assert "Rawson's Electrical" in final
    assert 'cardiology problem' not in final
    assert 'Mervyn enlisted in 1952' not in final


def test_long_note_is_processed_in_chunks_before_final_synthesis(tmp_path):
    db=connect(tmp_path/'x.sqlite3'); seed(db)
    long=' '.join([f'Mervyn enlisted in 1952 and military detail number {i}.' for i in range(700)])
    db.execute("UPDATE notes SET text=? WHERE id=22",(long,)); db.commit()
    client=FakeClient()
    r=answer_knowledge_question(db,1,'Tell me about his military service',client=client)
    assert len(client.prompts) > 2
    assert any('Relevant factual digest:' in p for p in client.prompts[:-1])
    assert 'Condensed factual digest.' in client.prompts[-1]
    assert r['status']=='ok'


def test_local_build_rejects_non_loopback_endpoint():
    try:
        _assert_loopback('https://example.com:11434')
    except LocalLLMError:
        pass
    else:
        raise AssertionError('non-local endpoint must be rejected')


def test_ollama_defaults_to_loopback():
    cfg=LocalLLMConfig()
    assert cfg.base_url.startswith('http://127.0.0.1:')
