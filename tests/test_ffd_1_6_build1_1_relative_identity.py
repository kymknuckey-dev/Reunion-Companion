from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question

def seed(db):
 ps=[
 (1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),
 (2,'@I2@',2,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/'),
 (3,'@I3@',3,'Jamie Lee','Knuckey','Jamie Lee Knuckey','M','Jamie Lee /Knuckey/'),
 (10,'@I10@',10,'James','Knuckey','James Knuckey','M','James /Knuckey/'),
 (11,'@I11@',11,'James','Knuckey','James Knuckey','M','James /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
 for r in [(1,1,'Husband'),(1,2,'Child'),(1,3,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 ev=[
 (1,1,'Birth','1 JAN 1930',None,None,None,'BIRT'),
 (2,2,'Birth','1 JAN 1960',None,None,None,'BIRT'),
 (3,3,'Birth','1 JAN 1965',None,None,None,'BIRT'),
 (4,2,'Occupation',None,None,'Intranet Control Administrator [ Santos Ltd. ]',None,'OCCU'),
 (10,10,'Birth','1 JUN 1857',None,None,None,'BIRT'),(11,10,'Death','11 JUL 1910',None,None,None,'DEAT'),
 (12,11,'Birth','2 FEB 1882',None,None,None,'BIRT'),(13,11,'Death','3 MAR 1946',None,None,None,'DEAT'),
 (14,10,'Religion',None,None,'Methodist',None,'RELI'),(15,11,'Religion',None,None,'Anglican',None,'RELI')]
 for e in ev:db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",e)
 db.commit()

def test_first_son_becomes_fact_subject(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"What did his 1st son do for work?",1)
 assert "Kym Wayne Knuckey" in r["answer"]
 assert "Intranet Control Administrator" in r["answer"]

def test_oldest_son_becomes_age_subject(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"How old is his oldest son?",1)
 assert "Kym Wayne Knuckey" in r["answer"]
 assert "Mervyn Neil Knuckey’s children" not in r["answer"]

def test_ambiguous_identity_shows_dates(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"What religion was James Knuckey?",None)
 assert r["status"]=="ambiguous"
 assert "Which one do you mean?" in r["answer"]
 assert "James Knuckey (1857–1910)" in r["answer"]
 assert "James Knuckey (1882–1946)" in r["answer"]
 assert r["kind"]=="identity-choice"

def test_ambiguous_question_does_not_leak_fact(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"What religion was James Knuckey?",None)
 assert "Methodist" not in r["answer"] and "Anglican" not in r["answer"]
