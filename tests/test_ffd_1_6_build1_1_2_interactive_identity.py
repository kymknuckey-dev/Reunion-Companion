from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,questions_body

def seed(db):
 db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/')")
 for n,year,religion in [(10,1857,'Church Of England'),(11,1828,'Methodist'),(12,1806,'Anglican')]:
  db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(n,f'@I{n}@',n,'James','Knuckey','James Knuckey','M','James /Knuckey/'))
  db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",(100+n,n,'Birth',f'1 JAN {year}',None,None,None,'BIRT'))
  db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",(200+n,n,'Religion',None,None,religion,None,'RELI'))
 db.commit()

def test_picker_cards_preserve_original_question(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 h=questions_body(db,1,"What religion is James Knuckey?")
 assert "rq-identity-card" in h and "matching Reunion people" in h
 assert "q=What%20religion%20is%20James%20Knuckey%3F" in h
 assert "selected=10" in h and "selected=11" in h and "selected=12" in h

def test_selection_replays_question_for_exact_person(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 h=questions_body(db,1,"What religion is James Knuckey?",11)
 assert "Methodist" in h
 assert "rq-identity-card" not in h

def test_normal_question_remains_ambiguous_until_selection(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"What religion is James Knuckey?",1)
 assert r["status"]=="ambiguous" and len(r["choices"])==3
 assert "Church Of England" not in r["answer"] and "Methodist" not in r["answer"]

def test_picker_is_chronological(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 h=questions_body(db,1,"What religion is James Knuckey?")
 assert h.index("1806") < h.index("1828") < h.index("1857")
