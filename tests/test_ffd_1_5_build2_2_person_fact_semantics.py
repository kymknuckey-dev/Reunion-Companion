import datetime
from reunion_companion.companion.database import connect
from reunion_companion.companion.ffd_relationship_questions import answer_question,interpret_question,_ordinal_index
def seed(db):
 ps=[(1,'@I1@',1,'Mervyn Neil','Knuckey','Mervyn Neil Knuckey','M','Mervyn Neil /Knuckey/'),(2,'@I2@',2,'Kym Wayne','Knuckey','Kym Wayne Knuckey','M','Kym Wayne /Knuckey/'),(3,'@I3@',3,'Jodie Karen','Knuckey','Jodie Karen Knuckey','F','Jodie Karen /Knuckey/'),(4,'@I4@',4,'Jamie Lee','Knuckey','Jamie Lee Knuckey','M','Jamie Lee /Knuckey/')]
 db.executemany("INSERT INTO people(id,gedcom_xref,reunion_person_id,given_names,surname,display_name,sex,raw_name) VALUES(?,?,?,?,?,?,?,?)",ps)
 db.execute("INSERT INTO families(id,gedcom_xref) VALUES(1,'@F1@')")
 for r in [(1,1,'Husband'),(1,2,'Child'),(1,3,'Child'),(1,4,'Child')]:db.execute("INSERT INTO family_members VALUES(?,?,?)",r)
 db.commit()
def test_numeric_ordinal_parser():
 assert _ordinal_index("who is Mervyn's 2nd child?")==1
 assert _ordinal_index("who is Mervyn's 3rd child?")==2
 assert _ordinal_index("who is Mervyn's 4th child?")==3
def test_numeric_second_child(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 assert answer_question(db,"who is Mervyn's 2nd child?",1)["answer"]=="Mervyn Neil Knuckey’s 2nd child is Jodie Karen Knuckey."
def test_fact_intents():
 assert interpret_question("How old is Kym Knuckey?")=="age"
 assert interpret_question("What occupation did Kym Knuckey do?")=="occupation"
 assert interpret_question("How did Barry Jones die?")=="death_cause"
 assert interpret_question("When did Barry Jones die?")=="death"
 assert interpret_question("Where did Barry Jones die?")=="death_place"
def test_age_without_birth_is_honest(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"How old is Kym Knuckey?",1)
 assert r["status"]=="not-found" and "cannot calculate" in r["answer"]
def test_occupation_without_data_is_honest(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"What occupation did Kym Knuckey do?",1)
 assert r["status"]=="not-found" and "No occupations" in r["answer"]
def test_how_died_without_cause_is_not_a_date_answer(tmp_path):
 db=connect(tmp_path/"x");seed(db)
 r=answer_question(db,"How did Mervyn Knuckey die?",1)
 assert r["status"]=="not-found" and "cause of death" in r["answer"]
