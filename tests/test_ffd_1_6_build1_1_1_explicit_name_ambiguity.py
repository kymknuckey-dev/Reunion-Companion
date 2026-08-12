from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question
def seed(db):
 db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/')")
 for n in range(55):
  pid=100+n;year=1800+n
  db.execute("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",(pid,f'@I{pid}@',pid,'James','Knuckey','James Knuckey','M','James /Knuckey/'))
  db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",(1000+n,pid,'Birth',f'1 JAN {year}',None,None,None,'BIRT'))
  db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",(2000+n,pid,'Religion',None,None,'Church Of England' if n==0 else 'Methodist',None,'RELI'))
 db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
 db.execute("INSERT INTO family_members VALUES(1,1,'Husband')");db.execute("INSERT INTO family_members VALUES(1,100,'Child')")
 db.commit()
def test_55_literal_jameses_require_choice_with_context(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"What religion is James Knuckey?",1)
 assert r["status"]=="ambiguous" and r["kind"]=="identity-choice" and len(r["people"])==55
 assert "Which one do you mean?" in r["answer"] and "James Knuckey (born 1800)" in r["answer"]
 assert "Church Of England" not in r["answer"] and "Methodist" not in r["answer"]
def test_55_literal_jameses_require_choice_without_context(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"What religion is James Knuckey?")
 assert r["status"]=="ambiguous" and len(r["choices"])==55
