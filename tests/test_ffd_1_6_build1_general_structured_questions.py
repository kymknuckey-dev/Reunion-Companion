from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,search_structured_facts
def seed(db):
 ps=[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Victor Alexander','Knuckey','Victor Alexander Knuckey','M','Victor Alexander /Knuckey/'),(3,'@I3@',3,'Lois Aletha','Waight','Lois Aletha Waight','F','Lois Aletha /Waight/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
 for r in [(1,2,'Husband'),(1,3,'Wife'),(1,1,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 ev=[(1,1,'Residence','1958','Glenelg, South Australia',None,None,'RESI'),(2,1,'Education','1950','Adelaide, South Australia','Brighton High School',None,'EDUC'),(3,1,'Military Service','1952',None,'National Service',None,'MILI'),(4,2,'Occupation','1930',None,'Carpenter',None,'OCCU')]
 for e in ev:db.execute("INSERT INTO events(id,person_id,event_type,date_text,place_text,value_text,note_text,gedcom_tag) VALUES(?,?,?,?,?,?,?,?)",e)
 db.commit()
def test_residence(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert "Glenelg, South Australia" in answer_question(db,"Where did Mervyn live?",1)["answer"]
def test_education(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert "Brighton High School" in answer_question(db,"What education is recorded for Mervyn?",1)["answer"]
def test_military(tmp_path):
 db=connect(tmp_path/"x");seed(db);assert "National Service" in answer_question(db,"What military service is recorded for Mervyn?",1)["answer"]
def test_relative_subject(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"What did his father do for work?",1);assert "Victor Alexander Knuckey" in r["answer"] and "Carpenter" in r["answer"]
def test_general_search(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=search_structured_facts(db,1,"Where did Mervyn live?");assert r["domain"]=="residence" and r["results"][0]["type"]=="Residence"
def test_rich_question_not_invented(tmp_path):
 db=connect(tmp_path/"x");seed(db);r=answer_question(db,"What was Mervyn like as a child?",1);assert r["status"] in ("unsupported","not-found")
