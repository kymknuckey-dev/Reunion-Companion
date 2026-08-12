from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question, questions_body, blood_relationship
from reunion_companion.companion.knowledge_conversation import answer_knowledge_question, interpret_knowledge_question

class FakeClient:
    def __init__(self): self.prompts=[]
    def generate(self,prompt):
        self.prompts.append(prompt)
        return 'Grounded narrative answer.'
    def resolve_model(self): return 'gemma3:4b'

def add_person(db,pid,name,sex):
    given,*rest=name.split(' '); surname=rest[-1] if rest else ''
    db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",
               (pid,f'@I{pid}@',pid,given,surname,name,sex,name))

def seed(db):
    add_person(db,1,'Elaine Fay Cox','F'); add_person(db,2,'Mervyn Neil Knuckey','M')
    add_person(db,3,'Kym Wayne Knuckey','M'); add_person(db,4,'Jodie Karen Knuckey','F'); add_person(db,5,'Jamie Lee Knuckey','M')
    add_person(db,6,'Lois Aletha Waight','F'); add_person(db,7,'Albert William Waight','M'); add_person(db,8,'Lionel George Waight','M')
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(10,2,'Birth','1 JAN 1934','Unley Private Hospital, Unley, South Australia',NULL,NULL,'BIRT')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(11,2,'Occupation',NULL,NULL,'Public Servant. S.A. Health Commission [Retired]',NULL,'OCCU')")
    db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(12,2,'Residence','1960','Adelaide, South Australia','Brighton Road',NULL,'RESI')")
    db.executemany("INSERT INTO notes(id,person_id,note_type,gedcom_tag,gedcom_note_xref,text,is_referenced) VALUES(?,?,?,?,?,?,?)",[
      (20,1,'Sport Achievement','_SPORT',None,'Elaine played netball, then known as basketball. Her golfing activities included several years at The Vines Golf Club and a year at Flagstaff/Flaxted Golf Club before returning to The Vines in 2017.',0),
      (21,2,'Medical','_MEDI',None,'Mervyn suffered a heart attack and later had other cardiology treatment.',0),
      (22,2,'Military Service','_MILI',None,'Mervyn completed National Service in 1952 for 176 days before returning to Adelaide.',0),
      (23,2,'Misc Notes','NOTE',None,'Mervyn lived at several addresses in South Australia during his life.',0),
    ])
    # Mervyn + Elaine children
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
    for pid,role in ((2,'husband'),(1,'wife'),(3,'child'),(4,'child'),(5,'child')): db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,?,?)",(pid,role))
    # Albert -> Lois and Lionel; Lois -> Mervyn
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(2,'@F2@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,7,'husband')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,6,'child')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(2,8,'child')")
    db.execute("INSERT INTO families(id,gedcom_xref) VALUES(3,'@F3@')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(3,6,'wife')")
    db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(3,2,'child')")
    db.commit()

def test_domain_router_catches_real_world_knowledge_questions():
    assert interpret_knowledge_question('Did she play golf?')=='topic:golf'
    assert interpret_knowledge_question('Did she play netball?')=='topic:netball'
    assert interpret_knowledge_question('What health issues did he have?')=='topic:medical'
    assert interpret_knowledge_question('What illnesses or health issues did he have as he aged?')=='topic:medical'
    assert interpret_knowledge_question('Did he serve in the military during any wars or conflicts?')=='topic:military'
    assert interpret_knowledge_question('Where did he live during his lifetime?')=='topic:residence'
    assert interpret_knowledge_question('Where are the gaps in the timeline that need more search work?')=='research:gaps'

def test_golf_and_netball_use_sport_note_evidence(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    c=FakeClient(); r=answer_knowledge_question(db,1,'Did she play golf?',client=c)
    assert r['status']=='ok'; assert 'Vines Golf Club' in c.prompts[-1]
    c=FakeClient(); answer_knowledge_question(db,1,'Did she play netball?',client=c)
    assert 'netball' in c.prompts[-1].casefold() and 'basketball' in c.prompts[-1].casefold()

def test_health_query_uses_medical_evidence_not_occupation(tmp_path):
    db=connect(tmp_path/'x'); seed(db); c=FakeClient()
    answer_knowledge_question(db,2,'What illnesses or health issues did he have as he aged?',client=c)
    p=c.prompts[-1].casefold(); assert 'heart attack' in p; assert 'public servant' not in p

def test_military_query_uses_military_note_not_education_or_medical(tmp_path):
    db=connect(tmp_path/'x'); seed(db); c=FakeClient()
    answer_knowledge_question(db,2,'Did he serve in the military during any wars or conflicts?',client=c)
    p=c.prompts[-1].casefold(); assert 'national service' in p; assert 'heart attack' not in p

def test_birth_where_and_when_returns_date_and_place(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    r=answer_question(db,'Where and when was he born?',2)
    assert '1 JAN 1934' in r['answer'] and 'Unley Private Hospital' in r['answer']

def test_gendered_child_relationships_filter_children(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    sons=answer_question(db,'Who is her son?',1); daughters=answer_question(db,'Who is her daughter?',1)
    assert {p['id'] for p in sons['people']}=={3,5}
    assert {p['id'] for p in daughters['people']}=={4}

def test_pronoun_gender_mismatch_is_not_silently_accepted(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    r=answer_question(db,'What do the notes say about him?',1)
    assert r['status']=='pronoun-mismatch' and 'Did you mean her?' in r['answer']
    r=answer_question(db,'Who is his first son?',1)
    assert r['status']=='pronoun-mismatch'

def test_uncle_path_gets_human_kinship_label(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    rel=blood_relationship(db,2,8)
    assert rel and rel['label']=='maternal uncle'
    r=answer_question(db,'How is Mervyn Neil Knuckey related to Lionel George Waight?',2)
    assert 'maternal uncle' in r['answer']

def test_focus_is_sticky_and_move_link_is_offered(tmp_path):
    db=connect(tmp_path/'x'); seed(db)
    r=answer_question(db,'Who is her daughter?',1)
    assert r['context_person_id']==1 and r['question_subject_id']==4
    h=questions_body(db,1,'Who is her daughter?',origin_id=1)
    assert 'Conversation is currently about <strong>Elaine Fay Cox</strong>' in h
    assert 'Move conversation to Jodie Karen Knuckey →' in h

def test_research_gap_question_routes_to_evidence_analysis(tmp_path):
    db=connect(tmp_path/'x'); seed(db); c=FakeClient()
    r=answer_knowledge_question(db,2,'Where are the gaps in the timeline that need more search work?',client=c)
    assert r['status']=='ok'; assert 'research aid' in c.prompts[-1].casefold(); assert 'birth' in c.prompts[-1].casefold()
