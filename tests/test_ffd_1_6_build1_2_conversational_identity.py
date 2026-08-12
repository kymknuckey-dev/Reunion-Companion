from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,questions_body

def seed(db):
 rows=[
  (1,'James','Knuckey','M'),(2,'James','Knuckey','M'),(3,'Thomas','Knuckey','M'),(4,'Elizabeth','Hunter','F')]
 for pid,g,s,sex in rows:
  db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f'@I{pid}@',pid,g,s,f'{g} {s}',sex,f'{g} /{s}/'))
 for eid,pid,kind,date,place,val in [
  (11,1,'Birth','1 JUN 1857','Adelaide, South Australia',None),(12,1,'Religion',None,None,'Church Of England'),
  (21,2,'Birth','1 JAN 1737','Cornwall, England',None),(31,3,'Death','2 FEB 1880','Adelaide, South Australia',None)]:
  db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",(eid,pid,kind,date,place,val,None,kind[:4].upper()))
 db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
 db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,3,'husband')")
 db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,4,'wife')")
 db.execute("INSERT INTO family_members(family_id,person_id,role) VALUES(1,1,'child')")
 db.commit()

def test_selection_becomes_followup_context(tmp_path):
 db=connect(tmp_path/'x');seed(db)
 h=questions_body(db,None,'What religion is James Knuckey?',1)
 assert 'Church Of England' in h
 assert "name='person' value='1'" in h
 assert 'Conversation is currently about <strong>James Knuckey</strong>' in h

def test_pronoun_followup_uses_carried_context(tmp_path):
 db=connect(tmp_path/'x');seed(db)
 r=answer_question(db,'Where was he born?',1)
 assert r['status']=='ok' and 'Adelaide, South Australia' in r['answer']
 assert r['context_person_id']==1

def test_parent_followup_keeps_focus_and_offers_relative(tmp_path):
 db=connect(tmp_path/'x');seed(db)
 r=answer_question(db,'When did his father die?',1)
 assert r['status']=='ok' and 'Thomas Knuckey' in r['answer'] and '2 FEB 1880' in r['answer']
 assert r['context_person_id']==1
 assert r['question_subject_id']==3

def test_next_spouse_question_uses_shifted_focus(tmp_path):
 db=connect(tmp_path/'x');seed(db)
 r=answer_question(db,'What about his wife?',3)
 assert 'Elizabeth Hunter' in r['answer']

def test_ambiguity_does_not_silently_change_context(tmp_path):
 db=connect(tmp_path/'x');seed(db)
 r=answer_question(db,'What religion is James Knuckey?',3)
 assert r['status']=='ambiguous'
 assert r['context_person_id']==3
